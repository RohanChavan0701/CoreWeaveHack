"""The mbpp family: MBPP's sanitized split as write-and-run tasks graded by the dataset's own asserts.

Each task states a small programming problem and leaves ``tests.py`` in the
working directory — the dataset's ``test_imports``, ``from solution import
*``, and its asserts. The agent writes ``solution.py`` and runs the tests
through the shell tool under a budget of three calls, so a failing assert
must be read and diagnosed rather than brute-forced. The hidden check reruns
``python3 tests.py`` in the working directory: the grade is the dataset's own
test, never a string comparison against a reference solution, and the
reference ``code`` is dropped at transcription so the pinned file cannot leak
an answer.

Dataset ``google-research-datasets/mbpp``, config ``sanitized``, split
``test`` (257 rows), CC-BY-4.0, pinned at revision
``4bb6404fdc6cacfda99d4ac4205087b89d32030c`` (2024-01-04), transcribed
through the datasets-server rows API on 2026-09-12.

:data:`EXCLUDED` holds the task ids the family does not carry: a row is
excluded when the dataset's own reference solution, written to
``solution.py``, does not make ``python3 tests.py`` exit zero — a test that
the reference cannot pass grades the harness, not the agent. The set is
empty: all 257 rows of the split clear their own asserts here.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import requests

from suite.families import family
from suite.families.genesis import RESULT_STR
from suite.tasks import Task

DATASET = "google-research-datasets/mbpp"
CONFIG = "sanitized"
SPLIT = "test"
LICENSE = "CC-BY-4.0"
REVISION = "4bb6404fdc6cacfda99d4ac4205087b89d32030c"
FETCHED = "2026-09-12"
ROWS_API = "https://datasets-server.huggingface.co/rows"
PAGE = 100
"""The rows API's maximum page; the transcriber pages until it has what it was asked for."""

TIMEOUT = 20
"""Seconds the hidden check gives ``python3 tests.py`` before it counts the task failed."""

SHELL_BUDGET = 3

EXCLUDED: frozenset[int] = frozenset()
"""MBPP task ids whose own reference solution does not pass their own asserts here."""

INSTRUCTION = ("Write the solution to solution.py in the working directory: the hidden check runs `python3 tests.py` there, "
               "and tests.py is in the working directory for you to read.")


def fetch(n: int) -> list[dict[str, Any]]:
    """Transcribe at most ``n`` rows into pinned records, dropping the reference solution and :data:`EXCLUDED`."""
    out: list[dict[str, Any]] = []
    offset = 0
    while len(out) < n:
        page = requests.get(ROWS_API, params={"dataset": DATASET, "config": CONFIG, "split": SPLIT, "offset": offset, "length": PAGE}, timeout=60)
        page.raise_for_status()
        rows = page.json()["rows"]
        if not rows:
            break
        for row in rows:
            r = row["row"]
            if r["task_id"] in EXCLUDED:
                continue
            out.append({"id": r["task_id"], "prompt": r["prompt"], "test_imports": list(r["test_imports"]), "test_list": list(r["test_list"])})
            if len(out) == n:
                break
        offset += len(rows)
    return out


def tests_file(record: dict[str, Any]) -> str:
    """The working directory's ``tests.py``: the record's imports, the solution's names, then its asserts."""
    return "\n".join([*record["test_imports"], "from solution import *", *record["test_list"]]) + "\n"


def check(result: Any, workdir: Path) -> bool:
    """The dataset's own test: ``python3 tests.py`` exits zero and the solution is where the prompt asked for it."""
    try:
        proc = subprocess.run(["python3", "tests.py"], cwd=workdir, capture_output=True, text=True, timeout=TIMEOUT)
    except Exception:  # a run that cannot happen — a timeout, a missing interpreter — is a failed task, never a raise
        return False
    return proc.returncode == 0 and (workdir / "solution.py").exists()


@family("mbpp", source=f"{DATASET} [{CONFIG}/{SPLIT}] ({LICENSE}, rev {REVISION[:8]}); the dataset's asserts run as the hidden test",
        fetch=fetch)
def tasks() -> list[Task]:
    from suite.families import FAMILIES

    return [Task(f"mbpp/{r['id']}", f"{r['prompt'].strip()} {INSTRUCTION}",
                 ("file-tool", "shell-tool", "test-failure-triage", "tool-budget"), RESULT_STR, check,
                 shell_budget=SHELL_BUDGET, files={"tests.py": tests_file(r)})
            for r in FAMILIES["mbpp"].records()]
