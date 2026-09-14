"""The text-to-SQL family: BIRD mini-dev's ``financial`` questions over one pinned SQLite database.

Each task states one question in natural language, carries BIRD's own
evidence as hints, and ships the database into the working directory
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

Three families share the pinned questions and database. Two differ only in
slack, mirroring ``curriculum`` vs ``curriculum-strict``: ``text2sql`` budgets
three shell calls, so a pass may spend calls inspecting the schema and
iterating on the query; ``text2sql-strict`` budgets exactly the knowing floor
of one, so a pass that must discover the schema convention cannot fit and only
a pass that already knows it — from the store, or from the model — stays within
budget. Both draw the ``graded`` group, the adaptation set. The third family,
``text2sql-holdout``, carries the ``holdout`` group at the slack budget: the
held-out generalization set, its templates disjoint from the graded set's, its
schema conventions shared, so it measures whether an admitted record transfers
rather than being re-learned.

The database layer is injectable: everything that is specific to one BIRD
database — its ``db_id``, the pinned basename, the name the agent sees, the
source SHA pin, the path inside BIRD's dev bundle, the selected questions with
their groups, and any schema-specific size reduction — is one
:class:`DbConfig`, and :func:`_register` turns a config into the three
families. Only ``financial`` is registered today; a second BIRD database is a
second :class:`DbConfig` plus one :func:`_register` call, no code fork.

Dataset ``birdsql/bird_mini_dev``, ``data/mini_dev_sqlite`` (500 rows, of
which 32 are the ``financial`` database), CC-BY-SA-4.0, pinned at revision
``f65faf4ae3b638c1fa6df1d3370c8d92c8366301``; the database is BIRD's dev
``financial.sqlite`` (SHA-256 :data:`FINANCIAL.orig_sha`), transcribed on
2026-09-13. All 32 ``financial`` questions are pinned, including the four that
read ``trans`` (116, 129, 145, 159). The pinned database is therefore the full
``financial.sqlite`` with every table kept whole — ``trans`` (1,056,320 rows)
included, since on-disk size is not a constraint here and every gold must
execute against the shipped copy. :func:`fetch` re-executes each gold against
both the full source database and the pinned copy and pins the question only
when their rows match, so a reduction that changed any answer would fail loudly
rather than silently grade against a different world.
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
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import requests

from suite.families import DATA, family
from suite.families.genesis import RESULT_STR
from suite.tasks import Check, Task

DATASET = "birdsql/bird_mini_dev"
SQLITE_ROWS = "data/mini_dev_sqlite-00000-of-00001.json"
LICENSE = "CC-BY-SA-4.0"
HF_REVISION = "f65faf4ae3b638c1fa6df1d3370c8d92c8366301"
QUESTIONS_URL = f"https://huggingface.co/datasets/{DATASET}/resolve/{HF_REVISION}/{SQLITE_ROWS}"
"""The BIRD mini-dev questions file; every database's questions live here and are selected by ``db_id``."""
FETCHED = "2026-09-13"

DEV_ZIP_URL = "https://bird-bench.oss-cn-beijing.aliyuncs.com/dev.zip"
"""Where the databases live: BIRD's dev bundle, whose ``financial.sqlite`` this family pins. :func:`fetch`
verifies the extracted database against the config's ``orig_sha``; set ``$HGI_BIRD_DEV_ZIP`` to a local copy to skip the download."""

SHELL_BUDGET = 3
KNOWING_SHELL = 1
"""The knowing floor: a pass that knows the schema and conventions writes the query and verifies it in one shell call.
``text2sql`` budgets :data:`SHELL_BUDGET` (slack for discovery); ``text2sql-strict`` budgets exactly this floor."""

CHECK_TIMEOUT = 30
"""Seconds a query gets against the database before the check counts it failed."""


# --- the injectable database layer -------------------------------------------------------------------

@dataclass(frozen=True)
class DbConfig:
    """One BIRD database and its pinned questions — everything the three families need that is DB-specific.

    A second BIRD database is a second instance of this plus one :func:`_register` call: parameterize the
    ``db_id`` (which selects its questions from the shared BIRD file), the pinned ``basename`` and the
    ``filename`` the agent sees, the source ``orig_sha`` pin, the ``inner_path`` inside the dev bundle,
    the ``selected`` questions with their groups, and — only if its largest table must be shrunk to a
    committable size — a ``reduce`` step. ``financial`` keeps every table whole (``reduce`` is ``None``)."""

    id: str
    """BIRD ``db_id``; selects this database's questions from the shared BIRD mini-dev file."""
    fam_base: str
    """Base family name; the strict and holdout families append ``-strict`` / ``-holdout``."""
    basename: str
    """The pinned database as committed under ``suite/data/``."""
    filename: str
    """The database as the agent sees it in the working directory (the leakage-safe name from the prompt)."""
    orig_sha: str
    """SHA-256 of the source database (the leakage rule's pinned digest); :func:`fetch` refuses a source that moved."""
    inner_path: str
    """Path to the ``.sqlite`` inside ``dev_databases.zip`` within the dev bundle."""
    selected: tuple[tuple[int, str], ...]
    """``(question_id, group)`` pins. ``graded`` is the adaptation set; ``holdout`` is disjoint in template,
    selected so no near-duplicate question straddles the two — the schema conventions are shared, the questions are not."""
    questions_url: str = QUESTIONS_URL
    dev_zip_url: str = DEV_ZIP_URL
    reduce: Callable[[sqlite3.Connection], None] | None = None
    """A schema-specific reduction of the source database to a committable size, or ``None`` to keep every table whole.
    Whatever it does, :func:`fetch` re-executes every gold against both the source and the reduced copy and refuses to
    pin a question whose rows the reduction changed, so a reduction can never silently grade against a different world."""


# The `financial` database: all 32 BIRD `financial` questions over the full financial.sqlite (every table whole,
# `trans` included). The graded group is the adaptation set (18 questions); the holdout group is the held-out
# generalization set (14 questions), its gold-SQL templates disjoint from the graded set's — no near-duplicate
# straddles the split. The four trans-reading questions (116, 129, 145, 159) are split two per group.
FINANCIAL = DbConfig(
    id="financial",
    fam_base="text2sql",
    basename="text2sql.sqlite",
    filename="financial.sqlite",
    orig_sha="d15d89cdb068a202b6f2b99342af44dffc1d52545b39ceaf62efdc0ba570101e",
    inner_path="dev_databases/financial/financial.sqlite",
    reduce=None,  # every table kept whole, `trans` included; on-disk size is not a constraint here
    selected=(
        # graded — the adaptation set (18)
        (117, "graded"), (118, "graded"), (92, "graded"), (93, "graded"), (98, "graded"),
        (99, "graded"), (89, "graded"), (136, "graded"), (112, "graded"), (119, "graded"),
        (100, "graded"), (120, "graded"), (138, "graded"), (145, "graded"), (149, "graded"),
        (159, "graded"), (173, "graded"), (194, "graded"),
        # holdout — the held-out generalization set (14), templates disjoint from graded
        (137, "holdout"), (192, "holdout"), (168, "holdout"), (128, "holdout"), (189, "holdout"),
        (125, "holdout"), (94, "holdout"), (95, "holdout"), (115, "holdout"), (186, "holdout"),
        (116, "holdout"), (169, "holdout"), (129, "holdout"), (152, "holdout"),
    ),
)


def _instruction(filename: str) -> str:
    return (
        f"{filename} in the working directory is a SQLite database. Inspect its schema and values with the shell tool "
        f"(for example `sqlite3 {filename} \".schema\"`, or a SELECT DISTINCT on a column), then return result: the "
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


def check_for(gold: str, filename: str) -> Check:
    """The hidden test for one question: execute the agent's SQL and the gold SQL against the shipped database, compare rows."""

    def check(result: Any, workdir: Path) -> bool:
        if not isinstance(result, str) or not result.strip():
            return False
        db = workdir / filename
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


def _source_db(db: DbConfig) -> Path:
    """The full source database from BIRD's dev bundle, verified against ``db.orig_sha``; ``$HGI_BIRD_DEV_ZIP`` caches the download."""
    cache = os.environ.get("HGI_BIRD_DEV_ZIP")
    zpath = Path(cache) if cache else _download(db.dev_zip_url, ".zip")
    with zipfile.ZipFile(zpath) as z:
        inner = z.read("dev_20240627/dev_databases.zip")
    with zipfile.ZipFile(io.BytesIO(inner)) as z2:
        db_bytes = z2.read(db.inner_path)
    sha = hashlib.sha256(db_bytes).hexdigest()
    if sha != db.orig_sha:
        raise SystemExit(f"{db.inner_path} sha256 {sha} != pinned {db.orig_sha}; the source moved — re-verify before re-pinning")
    out = Path(tempfile.mkstemp(suffix=".sqlite")[1])
    out.write_bytes(db_bytes)
    return out


def _build_reduced(db: DbConfig, src: Path) -> Path:
    """A committable copy of the source: ``db.reduce`` applied (a no-op when ``None``), then vacuumed. Content, not bytes."""
    dst = Path(tempfile.mkstemp(suffix=".sqlite")[1])
    dst.write_bytes(src.read_bytes())
    con = sqlite3.connect(dst)
    try:
        if db.reduce is not None:
            db.reduce(con)
            con.commit()
        con.execute("VACUUM")
    finally:
        con.close()
    return dst


def _make_fetch(db: DbConfig) -> Callable[[int], list[dict[str, Any]]]:
    """Bind :func:`fetch` to one :class:`DbConfig`, so ``hgi suite fetch <family>`` transcribes that database."""

    def fetch(n: int) -> list[dict[str, Any]]:
        return _fetch(db, n)

    return fetch


def _fetch(db: DbConfig, n: int) -> list[dict[str, Any]]:
    """Transcribe the selected questions into pinned records and write the pinned database beside them.

    Side effect: writes ``suite/data/<db.basename>``, the database ``tasks`` ships. Each gold is run against BOTH the
    full source database and the pinned copy, and a question is pinned only when the two return matching rows — so a
    ``reduce`` that changed any answer fails here rather than silently grading against a different world.
    """
    page = requests.get(db.questions_url, timeout=120)
    page.raise_for_status()
    by_id = {r["question_id"]: r for r in page.json() if r["db_id"] == db.id}

    source = _source_db(db)
    reduced = _build_reduced(db, source)
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / db.basename).write_bytes(reduced.read_bytes())

    out: list[dict[str, Any]] = []
    for qid, group in db.selected:
        if len(out) >= n:
            break
        r = by_id[qid]
        gold = " ".join(r["SQL"].split())
        # The pinned world must answer every gold exactly as the full source does, or the question cannot be pinned.
        full_rows = run_sql(source, gold)
        pinned_rows = run_sql(DATA / db.basename, gold)
        if not rows_match(full_rows, pinned_rows):
            raise SystemExit(f"gold for q{qid} returns different rows on the pinned {db.basename} than on the source "
                             f"{db.id}.sqlite; the reduction changed its answer — do not pin it")
        out.append({"id": qid, "group": group, "difficulty": r["difficulty"],
                    "question": r["question"].strip(), "evidence": r["evidence"].strip(), "gold": gold})
    return out


# --- the tasks ---------------------------------------------------------------------------------------

def _budget(n: int) -> str:
    return f"You have a budget of {n} shell call{'s' if n != 1 else ''}."


def _db_blob(db: DbConfig) -> str | None:
    """The pinned database as base64, or ``None`` when it has not been fetched yet."""
    path = DATA / db.basename
    return base64.b64encode(path.read_bytes()).decode() if path.exists() else None


def _tasks(db: DbConfig, fam: str, group: str, shell_budget: int) -> list[Task]:
    """The tasks of one family: its ``group`` of the pinned questions, id-prefixed by ``fam`` so the slack, strict and
    held-out families never collide when a suite composes more than one of them (as ``curriculum`` and its strict twin do)."""
    from suite.families import FAMILIES

    records = [r for r in FAMILIES[db.fam_base].records() if r.get("group") == group]
    blob = _db_blob(db)
    if not records or blob is None:
        return []
    return [Task(f"{fam}/q{r['id']}", f"{r['question']} Hints: {r['evidence']} {_instruction(db.filename)} {_budget(shell_budget)}",
                 ("shell-tool", "file-tool", "tool-budget"), RESULT_STR, check_for(r["gold"], db.filename),
                 shell_budget=shell_budget, blobs={db.filename: blob}, knowing={"shell": KNOWING_SHELL})
            for r in records]


def _source(db: DbConfig) -> str:
    return (f"{DATASET} [{SQLITE_ROWS}] {db.id} subset ({LICENSE}, rev {HF_REVISION[:8]}) over a pinned "
            f"{db.basename} (orig sha {db.orig_sha[:8]}); the gold SQL is re-executed as the hidden test, never shown")


def _register(db: DbConfig) -> None:
    """Register the three families of one database: the slack graded pool, its strict twin, and the held-out group."""
    src = _source(db)
    base = db.fam_base
    family(base, source=f"{src}; the graded group, three shell calls of slack", fetch=_make_fetch(db))(
        lambda: _tasks(db, base, "graded", SHELL_BUDGET))
    family(f"{base}-strict", source=f"{src}; the graded group, budgeted at exactly the knowing floor of one shell call")(
        lambda: _tasks(db, f"{base}-strict", "graded", KNOWING_SHELL))
    family(f"{base}-holdout", source=f"{src}; the disjoint held-out group over the same schema, three shell calls of slack")(
        lambda: _tasks(db, f"{base}-holdout", "holdout", SHELL_BUDGET))


_register(FINANCIAL)
