"""The text-to-SQL family: BIRD mini-dev's ``financial`` questions over one pinned SQLite database.

Each task states one question in natural language, carries BIRD's own
evidence as hints, and ships ``financial.sqlite`` into the working directory
(a :class:`suite.tasks.Task` binary blob). The agent inspects the schema and
values with the shell tool and returns, as ``result``, the single SQLite
``SELECT`` that answers the question. The hidden check EXECUTES that query
against the shipped database and compares the rows it returns to the rows the
dataset's own gold query returns — a set/row comparison (:func:`rows_match`),
never a string comparison against a reference query, the way ``mbpp`` reruns
``tests.py`` rather than diffing source. The gold SQL is the grading key: it
lives in the pinned record but is never placed in the prompt or in
:meth:`suite.tasks.Task.row`, so it cannot leak to the agent, and grading is
by re-execution alone.

The recurring convention of this world is the database's own schema quirks,
which is why a decision learned on one question transfers to unseen questions
over the same schema (the stream/transfer experiments). BIRD's evidence names
the domain mappings (``status = 'A'`` means a finished loan; ``'POPLATEK PO
OBRATU'`` means issuance after transaction) so a question stays answerable,
but the *transferable* conventions are the SQLite-dialect facts the evidence
never states and a general model gets wrong on first contact: dates are TEXT
``'YYYY-MM-DD'`` reached with ``STRFTIME``/``LIKE`` (there is no ``YEAR()``);
a ratio needs ``CAST(... AS REAL)`` or SQLite integer-divides to a wrong
number that still executes; the loan status and the Czech frequency/purpose
codes are literal coded values, gender is ``'F'``/``'M'``; and ``order`` is a
reserved word needing quoting. A query that omits the CAST executes cleanly
and returns the wrong rows — the exact "valid but semantically wrong" case the
credit correction in :func:`hgi.consolidate.row_passed` grades as a failure.

Two families share the pinned questions and database and differ only in slack,
mirroring ``curriculum`` vs ``curriculum-strict``: ``text2sql`` budgets three
shell calls, so a pass may spend calls inspecting the schema and iterating on
the query; ``text2sql-strict`` budgets exactly the knowing floor of one, so a
pass that must discover the schema convention cannot fit and only a pass that
already knows it — from the store, or from the model — stays within budget.
A third family, ``text2sql-holdout``, carries a disjoint group of questions
over the same database at the slack budget: the held-out generalization set,
its templates disjoint from the graded set's, its schema conventions shared,
so it measures whether an admitted record transfers rather than being re-learned.

Dataset ``birdsql/bird_mini_dev``, ``data/mini_dev_sqlite`` (500 rows, of
which 32 are the ``financial`` database), CC-BY-SA-4.0, pinned at revision
``f65faf4ae3b638c1fa6df1d3370c8d92c8366301``; the database is BIRD's dev
``financial.sqlite`` (SHA-256 :data:`ORIG_SHA`), transcribed on 2026-09-13.
The pinned ``text2sql.sqlite`` is that database reduced to a committable size:
every table is kept whole except ``trans`` (1,056,320 rows, 70 MB), which is
sampled to the accounts numbered at most :data:`TRANS_ACCOUNT_CAP` for schema
fidelity. No selected question reads ``trans`` (:func:`fetch` guards this by
never selecting a trans-touching id), so every gold query returns exactly the
rows it returns against the full database — the transcriber verifies each gold
runs on the reduced database before pinning it.
"""

from __future__ import annotations

import base64
import hashlib
import io
import os
import sqlite3
import tempfile
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any

import requests

from suite.families import DATA, family
from suite.families.genesis import RESULT_STR
from suite.tasks import Check, Task

DATASET = "birdsql/bird_mini_dev"
SQLITE_ROWS = "data/mini_dev_sqlite-00000-of-00001.json"
LICENSE = "CC-BY-SA-4.0"
HF_REVISION = "f65faf4ae3b638c1fa6df1d3370c8d92c8366301"
QUESTIONS_URL = f"https://huggingface.co/datasets/{DATASET}/resolve/{HF_REVISION}/{SQLITE_ROWS}"
FETCHED = "2026-09-13"

DEV_ZIP_URL = "https://bird-bench.oss-cn-beijing.aliyuncs.com/dev.zip"
"""Where the databases live: BIRD's dev bundle, whose ``financial.sqlite`` this family reduces and pins. ``fetch``
verifies the extracted database against :data:`ORIG_SHA`; set ``$HGI_BIRD_DEV_ZIP`` to a local copy to skip the download."""
ORIG_SHA = "d15d89cdb068a202b6f2b99342af44dffc1d52545b39ceaf62efdc0ba570101e"
"""SHA-256 of the downloaded ``financial.sqlite`` (the leakage rule's pinned digest); ``fetch`` refuses a source that moved."""

DB_ID = "financial"
DB_BASENAME = "text2sql.sqlite"
"""The reduced database as pinned under ``suite/data/``."""
DB_FILENAME = "financial.sqlite"
"""The database as the agent sees it in the working directory."""
TRANS_ACCOUNT_CAP = 20
"""``trans`` is sampled to accounts numbered at most this, for schema fidelity; no selected question reads ``trans``."""

SHELL_BUDGET = 3
KNOWING_SHELL = 1
"""The knowing floor: a pass that knows the schema and conventions writes the query and verifies it in one shell call.
``text2sql`` budgets :data:`SHELL_BUDGET` (slack for discovery); ``text2sql-strict`` budgets exactly this floor."""

CHECK_TIMEOUT = 30
"""Seconds a query gets against the database before the check counts it failed."""

# (question_id, group). The graded group is the adaptation set; the holdout group is disjoint in template and
# selected so no near-duplicate question straddles the two — the schema conventions are shared, the questions are not.
# Every id here reads only the tables kept whole, never `trans`, so its gold returns identical rows on the reduced DB.
SELECTED: tuple[tuple[int, str], ...] = (
    (117, "graded"), (118, "graded"), (92, "graded"), (93, "graded"), (98, "graded"),
    (99, "graded"), (89, "graded"), (136, "graded"), (112, "graded"), (119, "graded"),
    (137, "holdout"), (192, "holdout"), (168, "holdout"), (128, "holdout"), (189, "holdout"), (125, "holdout"),
)

INSTRUCTION = (
    f"{DB_FILENAME} in the working directory is a SQLite database. Inspect its schema and values with the shell tool "
    f"(for example `sqlite3 {DB_FILENAME} \".schema\"`, or a SELECT DISTINCT on a column), then return result: the "
    "single SQLite SELECT statement that answers the question. The hidden check runs your statement against the "
    "database and compares the rows it returns to a reference query's rows, so return the query text itself, not a "
    "computed value."
)


# --- SQL execution and row comparison, shared by the check and the fetch sanity pass -----------------

def last_statement(sql: str) -> str:
    """The last non-empty ``;``-separated statement — an agent that prefixes a scratch query still grades on its answer."""
    parts = [p for p in sql.strip().rstrip(";").split(";") if p.strip()]
    return parts[-1] if parts else sql


def run_sql(db_path: Path, sql: str) -> list[tuple[Any, ...]]:
    """Run ``sql`` read-only against the database and return its rows; raises on a bad query, which the check reads as a failure."""
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=CHECK_TIMEOUT)
    try:
        con.execute("PRAGMA query_only = ON")
        return con.execute(last_statement(sql)).fetchall()
    finally:
        con.close()


def _norm_row(row: tuple[Any, ...]) -> tuple[Any, ...]:
    """A row with floats rounded to two decimals and strings trimmed, so a percentage's formatting is not a mismatch."""
    return tuple(round(v, 2) if isinstance(v, float) else (v.strip() if isinstance(v, str) else v) for v in row)


def rows_match(agent: list[tuple[Any, ...]], gold: list[tuple[Any, ...]]) -> bool:
    """Whether two result sets hold the same rows, as multisets up to float rounding — order-insensitive, duplicates kept."""
    return Counter(_norm_row(r) for r in agent) == Counter(_norm_row(r) for r in gold)


def check_for(gold: str) -> Check:
    """The hidden test for one question: execute the agent's SQL and the gold SQL against the shipped database, compare rows."""

    def check(result: Any, workdir: Path) -> bool:
        if not isinstance(result, str) or not result.strip():
            return False
        db = workdir / DB_FILENAME
        try:
            agent_rows = run_sql(db, result)
        except Exception:  # a query that will not run — a syntax error, an unknown column — is a failed task, never a raise
            return False
        try:
            gold_rows = run_sql(db, gold)
        except Exception:  # a gold that cannot run against the shipped DB grades nothing; fetch guards against pinning one
            return False
        return rows_match(agent_rows, gold_rows)

    return check


# --- the transcriber ---------------------------------------------------------------------------------

def _download(url: str, suffix: str) -> Path:
    tmp = Path(tempfile.mkstemp(suffix=suffix)[1])
    with requests.get(url, stream=True, timeout=600) as resp:
        resp.raise_for_status()
        with tmp.open("wb") as f:
            for chunk in resp.iter_content(chunk_size=1 << 20):
                f.write(chunk)
    return tmp


def _source_db() -> Path:
    """The full ``financial.sqlite`` from BIRD's dev bundle, verified against :data:`ORIG_SHA`; ``$HGI_BIRD_DEV_ZIP`` caches the download."""
    cache = os.environ.get("HGI_BIRD_DEV_ZIP")
    zpath = Path(cache) if cache else _download(DEV_ZIP_URL, ".zip")
    with zipfile.ZipFile(zpath) as z:
        inner = z.read("dev_20240627/dev_databases.zip")
    with zipfile.ZipFile(io.BytesIO(inner)) as z2:
        db_bytes = z2.read("dev_databases/financial/financial.sqlite")
    sha = hashlib.sha256(db_bytes).hexdigest()
    if sha != ORIG_SHA:
        raise SystemExit(f"financial.sqlite sha256 {sha} != pinned {ORIG_SHA}; the source moved — re-verify before re-pinning")
    out = Path(tempfile.mkstemp(suffix=".sqlite")[1])
    out.write_bytes(db_bytes)
    return out


def _build_reduced(src: Path) -> Path:
    """The source database with ``trans`` sampled to :data:`TRANS_ACCOUNT_CAP` accounts and vacuumed to a committable size."""
    dst = Path(tempfile.mkstemp(suffix=".sqlite")[1])
    dst.write_bytes(src.read_bytes())
    con = sqlite3.connect(dst)
    try:
        con.execute(f"DELETE FROM trans WHERE account_id > {TRANS_ACCOUNT_CAP}")
        con.commit()
        con.execute("VACUUM")
    finally:
        con.close()
    return dst


def fetch(n: int) -> list[dict[str, Any]]:
    """Transcribe the selected ``financial`` questions into pinned records and write the reduced database beside them.

    Side effect: writes ``suite/data/text2sql.sqlite``, the pinned database ``tasks`` ships. Each gold query is run
    against that reduced database before it is pinned, so a question whose rows the reduction changed would fail here
    rather than silently grade against a different world.
    """
    page = requests.get(QUESTIONS_URL, timeout=120)
    page.raise_for_status()
    by_id = {r["question_id"]: r for r in page.json() if r["db_id"] == DB_ID}

    reduced = _build_reduced(_source_db())
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / DB_BASENAME).write_bytes(reduced.read_bytes())

    out: list[dict[str, Any]] = []
    con = sqlite3.connect(f"file:{DATA / DB_BASENAME}?mode=ro", uri=True)
    try:
        for qid, group in SELECTED:
            if len(out) >= n:
                break
            r = by_id[qid]
            gold = " ".join(r["SQL"].split())
            con.execute("PRAGMA query_only = ON")
            con.execute(last_statement(gold)).fetchall()  # sanity: the gold runs on the reduced DB, else the id must not be selected
            out.append({"id": qid, "group": group, "difficulty": r["difficulty"],
                        "question": r["question"].strip(), "evidence": r["evidence"].strip(), "gold": gold})
    finally:
        con.close()
    return out


# --- the tasks ---------------------------------------------------------------------------------------

def _budget(n: int) -> str:
    return f"You have a budget of {n} shell call{'s' if n != 1 else ''}."


def _db_blob() -> str | None:
    """The pinned database as base64, or ``None`` when it has not been fetched yet."""
    path = DATA / DB_BASENAME
    return base64.b64encode(path.read_bytes()).decode() if path.exists() else None


def _tasks(fam: str, group: str, shell_budget: int) -> list[Task]:
    """The tasks of one family: its ``group`` of the pinned questions, id-prefixed by ``fam`` so the slack, strict and
    held-out families never collide when a suite composes more than one of them (as ``curriculum`` and its strict twin do)."""
    from suite.families import FAMILIES

    records = [r for r in FAMILIES["text2sql"].records() if r.get("group") == group]
    blob = _db_blob()
    if not records or blob is None:
        return []
    return [Task(f"{fam}/q{r['id']}", f"{r['question']} Hints: {r['evidence']} {INSTRUCTION} {_budget(shell_budget)}",
                 ("shell-tool", "file-tool", "tool-budget"), RESULT_STR, check_for(r["gold"]),
                 shell_budget=shell_budget, blobs={DB_FILENAME: blob}, knowing={"shell": KNOWING_SHELL})
            for r in records]


_SOURCE = (f"{DATASET} [{SQLITE_ROWS}] {DB_ID} subset ({LICENSE}, rev {HF_REVISION[:8]}) over a pinned reduced "
           f"financial.sqlite (orig sha {ORIG_SHA[:8]}); the gold SQL is re-executed as the hidden test, never shown")


@family("text2sql", source=f"{_SOURCE}; the graded group, three shell calls of slack", fetch=fetch)
def tasks() -> list[Task]:
    return _tasks("text2sql", "graded", SHELL_BUDGET)


@family("text2sql-strict", source=f"{_SOURCE}; the graded group, budgeted at exactly the knowing floor of one shell call")
def strict_tasks() -> list[Task]:
    return _tasks("text2sql-strict", "graded", KNOWING_SHELL)


@family("text2sql-holdout", source=f"{_SOURCE}; the disjoint held-out group over the same schema, three shell calls of slack")
def holdout_tasks() -> list[Task]:
    return _tasks("text2sql-holdout", "holdout", SHELL_BUDGET)
