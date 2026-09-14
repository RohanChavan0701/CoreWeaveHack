"""The text-to-SQL family: all 32 BIRD ``financial`` questions over one pinned SQLite database, graded by
re-executing the returned SELECT against the shipped database and comparing its rows to the gold's — never a
string comparison. These tests read the pinned records and database offline (no network), so they run only when
the family has been fetched; they assert the group split, the leakage guard, the injectable DB layer, and that
grading is by row-equality including the "valid but semantically wrong" case a missing CAST produces.
"""

from __future__ import annotations

import sqlite3

import pytest

from suite.families import FAMILIES
from suite.families import text2sql as t2

GRADED = {117, 118, 92, 93, 98, 99, 89, 136, 112, 119, 100, 120, 138, 145, 149, 159, 173, 194}
HOLDOUT = {137, 192, 168, 128, 189, 125, 94, 95, 115, 186, 116, 169, 129, 152}
TRANS_READERS = {116, 129, 145, 159}
"""The four ``financial`` questions whose gold reads the ``trans`` table; two land in each group."""

pytestmark = pytest.mark.skipif(
    not (t2.DATA / t2.FINANCIAL.basename).exists(),
    reason="text2sql not fetched: run `hgi suite fetch text2sql`",
)


def _records():
    return FAMILIES[t2.FINANCIAL.fam_base].records()


def _by_id(name: str):
    return {int(tk.id.split("/q")[1]): tk for tk in FAMILIES[name].tasks()}


# --- the pinned pool and the group split -------------------------------------------------------------

def test_all_32_questions_pinned_split_18_graded_14_holdout():
    recs = _records()
    assert len(recs) == 32
    graded = {r["id"] for r in recs if r["group"] == "graded"}
    holdout = {r["id"] for r in recs if r["group"] == "holdout"}
    assert graded == GRADED
    assert holdout == HOLDOUT
    assert graded.isdisjoint(holdout)  # no question straddles the split
    assert (graded | holdout) == {qid for qid, _ in t2.FINANCIAL.selected}  # the union is exactly the selected pool
    assert len(graded) == 18 and len(holdout) == 14


def test_selected_config_covers_exactly_the_32_with_valid_groups():
    sel = t2.FINANCIAL.selected
    ids = [qid for qid, _ in sel]
    assert len(ids) == len(set(ids)) == 32  # no id selected twice
    assert {g for _, g in sel} == {"graded", "holdout"}


def test_every_record_carries_the_grading_and_prompt_fields():
    for r in _records():
        assert set(r) == {"id", "group", "difficulty", "question", "evidence", "gold"}
        assert r["gold"].strip().lower().startswith("select")


# --- the three families ------------------------------------------------------------------------------

def test_three_families_load_the_expected_groups_at_the_expected_budgets():
    graded_tasks = FAMILIES["text2sql"].tasks()
    strict_tasks = FAMILIES["text2sql-strict"].tasks()
    holdout_tasks = FAMILIES["text2sql-holdout"].tasks()
    assert {int(t.id.split("/q")[1]) for t in graded_tasks} == GRADED
    assert {int(t.id.split("/q")[1]) for t in strict_tasks} == GRADED  # strict is the graded group, one call tighter
    assert {int(t.id.split("/q")[1]) for t in holdout_tasks} == HOLDOUT
    assert all(t.shell_budget == t2.SHELL_BUDGET for t in graded_tasks + holdout_tasks)
    assert all(t.shell_budget == t2.KNOWING_SHELL for t in strict_tasks)
    # ids are prefixed by family so the three never collide in one suite
    assert graded_tasks[0].id.startswith("text2sql/q")
    assert strict_tasks[0].id.startswith("text2sql-strict/q")
    assert holdout_tasks[0].id.startswith("text2sql-holdout/q")


def test_gold_never_leaks_into_the_prompt_or_the_shown_row():
    recs = {r["id"]: r for r in _records()}
    for t in FAMILIES["text2sql"].tasks() + FAMILIES["text2sql-holdout"].tasks():
        gold = recs[int(t.id.split("/q")[1])]["gold"]
        assert gold not in t.prompt
        assert gold not in str(t.row())


# --- the pinned database: trans is now whole ---------------------------------------------------------

def test_shipped_database_keeps_trans_whole(tmp_path):
    task = _by_id("text2sql")[159]  # q159 reads trans
    task.setup(tmp_path)
    con = sqlite3.connect(tmp_path / t2.FINANCIAL.filename)
    try:
        tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert "trans" in tables
        # whole, not the old twenty-account sample: trans references far more than twenty accounts
        accounts = con.execute("SELECT COUNT(DISTINCT account_id) FROM trans").fetchone()[0]
        assert accounts > 20
        assert con.execute("SELECT COUNT(*) FROM trans").fetchone()[0] > 100_000
    finally:
        con.close()


# --- grading is by re-execution and row-equality -----------------------------------------------------

def test_check_passes_the_gold_and_fails_a_wrong_query(tmp_path):
    recs = {r["id"]: r for r in _records()}
    task = _by_id("text2sql")[117]
    task.setup(tmp_path)
    gold = recs[117]["gold"]
    assert task.check(gold, tmp_path) is True  # the gold, re-executed, matches itself
    assert task.check("SELECT 1", tmp_path) is False  # a running query with the wrong rows fails
    assert task.check("", tmp_path) is False  # an empty result fails
    assert task.check("this is not sql", tmp_path) is False  # a query that will not run fails, never raises
    assert task.check(42, tmp_path) is False  # a non-string result fails


def test_missing_cast_runs_but_grades_as_a_failure(tmp_path):
    """The signature text2sql failure: a percentage without CAST integer-divides to a wrong number that still executes."""
    task = _by_id("text2sql")[117]
    task.setup(tmp_path)
    no_cast = "SELECT (SUM(CASE WHEN status = 'A' THEN amount ELSE 0 END) * 100) / SUM(amount) FROM loan"
    # it runs (no raise) but the row differs from the gold's, so the check must return False
    assert t2.run_sql(tmp_path / t2.FINANCIAL.filename, no_cast)  # executes
    assert task.check(no_cast, tmp_path) is False


def test_check_is_order_insensitive_but_row_sensitive(tmp_path):
    recs = {r["id"]: r for r in _records()}
    task = _by_id("text2sql")[119]  # a 21-row projection
    task.setup(tmp_path)
    gold = recs[119]["gold"]
    assert task.check(f"SELECT * FROM ({gold}) ORDER BY 1 DESC", tmp_path) is True  # reordered rows still match
    assert task.check(f"{gold} LIMIT 5", tmp_path) is False  # a strict subset does not


def test_trans_reading_gold_grades_against_the_shipped_db(tmp_path):
    recs = {r["id"]: r for r in _records()}
    for qid in TRANS_READERS:
        group = "text2sql" if qid in GRADED else "text2sql-holdout"
        task = _by_id(group)[qid]
        task.setup(tmp_path)
        assert task.check(recs[qid]["gold"], tmp_path) is True, f"q{qid} gold does not grade against the shipped trans"


# --- rows_match semantics ----------------------------------------------------------------------------

def test_rows_match_is_a_multiset_up_to_two_decimals():
    assert t2.rows_match([(1,), (2,)], [(2,), (1,)])  # order-insensitive
    assert t2.rows_match([(1.0001,)], [(1.0,)])  # floats compared to two decimals
    assert not t2.rows_match([(1,), (1,)], [(1,)])  # duplicates are kept
    assert not t2.rows_match([(1,)], [(2,)])


# --- the injectable database layer -------------------------------------------------------------------

def test_financial_config_is_the_only_registered_db_and_names_are_stable():
    cfg = t2.FINANCIAL
    assert cfg.id == "financial"
    assert cfg.fam_base == "text2sql"
    assert cfg.filename == "financial.sqlite"
    assert cfg.basename == "text2sql.sqlite"
    assert cfg.reduce is None  # every table kept whole
    # the three families a single DbConfig registers, all present under the base name
    for fam in ("text2sql", "text2sql-strict", "text2sql-holdout"):
        assert fam in FAMILIES
    # only the base family declares the transcriber; the twins derive from its pinned records
    assert FAMILIES["text2sql"].fetch is not None
    assert FAMILIES["text2sql-strict"].fetch is None
    assert FAMILIES["text2sql-holdout"].fetch is None
