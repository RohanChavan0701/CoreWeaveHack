"""The transcribed families, read offline from their pinned files: each loads the tasks its records hold,
an mbpp task's hidden test is the dataset's own asserts, and a table question is graded by one normalizer
whichever way the table is reached — a CSV in the working directory, or a paged API."""

from __future__ import annotations

import csv
import io

import pytest

from suite.families import FAMILIES
from suite.families.api import PAGE_SIZE, pages
from suite.families.tables import _number, matches, records
from suite.families import text2sql as _t2s
from suite.tasks import SuiteSpec, build

MBPP_ROWS = 257
TABLE_ROWS = 200
"""The pinned TableBench records; `tables` takes the even half and `api` the odd half."""
T2S_GRADED = 10
T2S_HOLDOUT = 6
"""The pinned text2sql records: the graded group `text2sql` and its strict twin carry, the holdout group `text2sql-holdout` carries."""

SQUARE_PERIMETER = "mbpp/17"
"""One pinned task with a solution short enough to write by hand: ``square_perimeter(side) == 4 * side``."""


def _by_id(name: str):
    return {t.id: t for t in FAMILIES[name].tasks()}


def test_each_family_loads_its_pinned_records_with_unique_ids():
    counts = {name: len(FAMILIES[name].tasks()) for name in ("mbpp", "tables", "api")}
    assert counts == {"mbpp": MBPP_ROWS, "tables": TABLE_ROWS // 2, "api": TABLE_ROWS // 2}
    for name, n in counts.items():
        assert len(_by_id(name)) == n, f"{name}: task ids are not unique"
    world = build(SuiteSpec(families=["mbpp", "tables", "api"]))
    assert len(world.by_id) == sum(counts.values()) and world.families() == counts


def test_the_two_table_families_split_the_pinned_file_between_them():
    even, odd = records(0), records(1)
    assert len(even) == len(odd) == TABLE_ROWS // 2
    assert not {r["id"] for r in even} & {r["id"] for r in odd}
    assert [t.id.split("/", 1)[1] for t in FAMILIES["tables"].tasks()] == [r["id"][:8] for r in even]
    assert [t.id.split("/", 1)[1] for t in FAMILIES["api"].tasks()] == [r["id"][:8] for r in odd]


def test_an_mbpp_task_leaves_its_tests_to_read_and_grades_by_running_them(tmp_path):
    spec = _by_id("mbpp")[SQUARE_PERIMETER]
    assert spec.shapes == ("file-tool", "shell-tool", "test-failure-triage", "tool-budget") and spec.shell_budget == 3
    assert "solution.py" in spec.prompt and "tests.py" in spec.prompt
    tests = spec.files["tests.py"]
    assert "from solution import *" in tests and "square_perimeter(10)==40" in tests

    good = tmp_path / "good"
    spec.setup(good)
    (good / "solution.py").write_text("def square_perimeter(side):\n    return 4 * side\n")
    assert spec.check("solution.py", good)

    wrong = tmp_path / "wrong"
    spec.setup(wrong)
    (wrong / "solution.py").write_text("def square_perimeter(side):\n    return 3 * side\n")
    assert not spec.check("solution.py", wrong)

    missing = tmp_path / "missing"
    spec.setup(missing)
    assert not spec.check("solution.py", missing)


def test_an_mbpp_record_drops_the_reference_solution_and_keeps_its_asserts_in_order():
    record = next(r for r in FAMILIES["mbpp"].records() if f"mbpp/{r['id']}" == SQUARE_PERIMETER)
    assert "code" not in record
    assert _by_id("mbpp")[SQUARE_PERIMETER].files["tests.py"].splitlines() == [*record["test_imports"], "from solution import *", *record["test_list"]]


@pytest.mark.parametrize("name", ["tables", "api"])
def test_every_table_question_accepts_its_gold_answer_and_refuses_a_wrong_one(tmp_path, name):
    gold_of = {r["id"][:8]: r["answer"] for r in FAMILIES["tables"].records()}
    for spec in FAMILIES[name].tasks():
        gold = gold_of[spec.id.split("/", 1)[1]]
        number = _number(gold)
        wrong = number * 3.0 + 7.0 if number is not None else "zzz not the answer at all"
        assert spec.check(gold, tmp_path), f"{spec.id}: the gold answer {gold!r} must pass"
        assert not spec.check(wrong, tmp_path), f"{spec.id}: {wrong!r} must not pass for gold {gold!r}"


def test_a_tables_task_writes_the_table_as_csv_under_a_shell_budget():
    record = records(0)[0]
    spec = _by_id("tables")[f"tables/{record['id'][:8]}"]
    assert spec.shapes == ("file-tool", "shell-tool", "tool-budget") and spec.shell_budget == 3 and not spec.routes
    assert spec.schema["properties"]["result"]["type"] == ["number", "string"]
    read = list(csv.reader(io.StringIO(spec.files["table.csv"])))
    assert read[0] == record["columns"] and read[1:] == record["data"]


def test_an_api_task_pages_its_whole_table_and_budgets_exactly_the_pages_it_serves():
    gold_of = {r["id"][:8]: r for r in FAMILIES["tables"].records()}
    for spec in FAMILIES["api"].tasks():
        record = gold_of[spec.id.split("/", 1)[1]]
        assert spec.shapes == ("http-tool", "error-wrapping", "tool-budget") and not spec.files
        head = spec.routes["/table"]
        assert head["columns"] == record["columns"] and head["rows"] == len(record["data"]) and head["first"] == "/table/rows?page=1"
        walked, path, fetched = [], head["first"], 1
        while path is not None:
            body = spec.routes[path]
            assert len(body["rows"]) <= PAGE_SIZE
            walked += body["rows"]
            path, fetched = body["next"], fetched + 1
        assert walked == record["data"], f"{spec.id}: the pages must serve the whole table"
        assert fetched == pages(record["data"]) + 1 and spec.http_budget == pages(record["data"]) + 2
        assert len(spec.routes) == fetched, f"{spec.id}: the API serves the description and its pages, nothing else"


@pytest.mark.parametrize("result, gold, ok", [
    (37.64, "37.64%", True),                 # a percent sign is noise, not a unit
    ("37.6%", "37.64%", True),               # and a result that reads as a number is graded as one
    (1234.5, "1,234.50", True),              # thousands separators
    ("$1,234", "1234", True),                # and currency
    (10.6, "10.60", True),                   # a gold answer rounded to two decimals
    (10.59, "10.6", True),                   # and a result rounded the other way
    (1000000.0, "1005000", True),            # relative slack, for the totals absolute slack cannot reach
    (11.0, "10.6", False),                   # past both slacks
    (0.0, "0", True),
    (1.0, "0", False),                       # a zero gold has no relative slack to give
    ("Yes", " yes ", True),                  # a string, casefolded and its whitespace collapsed
    ("no", "Yes", False),
    (5, "high", False),                      # a number never answers a word
    ("high", "5", False),                    # nor a word a number
    ("2009,2010", "2009,2010", True),        # a comma-separated list is a string, never a number
    (20092010, "2009,2010", False),
])
def test_the_normalizer_reads_a_number_through_its_noise_and_a_string_through_its_case(result, gold, ok):
    assert matches(result, gold) is ok


def test_the_three_text2sql_families_split_the_pinned_questions_by_group():
    counts = {name: len(FAMILIES[name].tasks()) for name in ("text2sql", "text2sql-strict", "text2sql-holdout")}
    assert counts == {"text2sql": T2S_GRADED, "text2sql-strict": T2S_GRADED, "text2sql-holdout": T2S_HOLDOUT}
    graded = {t.id.rsplit("/q", 1)[1] for t in FAMILIES["text2sql"].tasks()}
    strict = {t.id.rsplit("/q", 1)[1] for t in FAMILIES["text2sql-strict"].tasks()}
    holdout = {t.id.rsplit("/q", 1)[1] for t in FAMILIES["text2sql-holdout"].tasks()}
    assert graded == strict, "the strict twin carries the same questions as the graded family"
    assert not (graded & holdout), "the held-out questions are disjoint from the graded ones"
    world = build(SuiteSpec(families=["text2sql", "text2sql-strict", "text2sql-holdout"]))
    assert len(world.by_id) == sum(counts.values()), "id-prefixing keeps the slack and strict twins from colliding"


def test_a_text2sql_task_ships_the_database_and_grades_by_re_executing_the_gold_query(tmp_path):
    gold_of = {r["id"]: r["gold"] for r in FAMILIES["text2sql"].records()}
    spec = {t.id: t for t in FAMILIES["text2sql"].tasks()}["text2sql/q117"]
    assert spec.shapes == ("shell-tool", "file-tool", "tool-budget") and spec.shell_budget == 3 and spec.knowing == {"shell": 1}
    assert _t2s.DB_FILENAME in spec.blobs and not spec.files, "the database ships as a binary blob, not a text file"
    spec.setup(tmp_path)
    assert (tmp_path / _t2s.DB_FILENAME).exists()

    gold = gold_of[117]
    assert spec.check(gold, tmp_path), "the gold query must grade as a pass"
    assert not spec.check("SELECT 1 WHERE 1=0", tmp_path), "a query that returns the wrong rows must fail"
    assert not spec.check("SELECT * FROM no_such_table", tmp_path), "a query that will not run must fail"
    assert not spec.check("not sql at all", tmp_path) and not spec.check("", tmp_path)
    # a ratio without CAST integer-divides in SQLite: it executes cleanly and returns the wrong number, and must fail —
    # the "valid but semantically wrong" case the credit correction grades as a failure, never a string comparison
    no_cast = "SELECT (SUM(CASE WHEN status = 'A' THEN amount ELSE 0 END) * 100) / SUM(amount) FROM loan"
    assert _t2s.run_sql(tmp_path / _t2s.DB_FILENAME, no_cast), "the no-CAST query executes"
    assert not spec.check(no_cast, tmp_path), "but returns the wrong rows, so it fails the hidden check"


def test_every_text2sql_gold_passes_its_own_check_and_the_gold_never_leaks(tmp_path):
    for name in ("text2sql", "text2sql-strict", "text2sql-holdout"):
        gold_of = {f"{name}/q{r['id']}": r["gold"] for r in FAMILIES["text2sql"].records()}
        for spec in FAMILIES[name].tasks():
            spec.setup(tmp_path)
            gold = gold_of[spec.id]
            assert spec.check(gold, tmp_path), f"{spec.id}: the gold query must pass"
            assert gold not in spec.prompt, f"{spec.id}: the gold SQL must not appear in the prompt"
            assert "gold" not in spec.row() and gold not in str(spec.row()), f"{spec.id}: the gold SQL must not appear in Task.row"


def test_the_strict_twin_budgets_the_knowing_floor_the_slack_family_leaves_room():
    strict = FAMILIES["text2sql-strict"].tasks()[0]
    slack = FAMILIES["text2sql"].tasks()[0]
    assert strict.shell_budget == strict.knowing["shell"] == _t2s.KNOWING_SHELL
    assert slack.shell_budget == _t2s.SHELL_BUDGET > slack.knowing["shell"]


@pytest.mark.parametrize("agent, gold, ok", [
    ([(18,)], [(18.0155,)], False),               # a ratio integer-divided to 18 is not the gold 18.02
    ([(18.02,)], [(18.0155,)], True),             # rounded to two decimals, the percentages match
    ([(69,)], [(69,)], True),
    ([(47.0,)], [(47,)], True),                   # a float that equals the gold int
    ([("Brno", 75), ("Praha", 324)], [("Praha", 324), ("Brno", 75)], True),   # order-insensitive
    ([("D",), ("D",)], [("D",)], False),          # duplicates are kept: a multiset, not a set
    ([(" Sokolov ",)], [("Sokolov",)], True),     # a string trimmed
])
def test_rows_match_compares_as_a_float_rounded_multiset(agent, gold, ok):
    assert _t2s.rows_match(agent, gold) is ok


def test_a_union_of_types_validates_against_any_of_them():
    from suite.scorers import _matches

    spec = {"type": ["number", "string"]}
    assert _matches(1, spec) and _matches(1.5, spec) and _matches("ok", spec)
    assert not _matches(None, spec) and not _matches({"a": 1}, spec) and not _matches(True, spec)
