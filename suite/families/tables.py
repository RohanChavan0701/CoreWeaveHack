"""The tables family: TableBench questions over a CSV in the working directory.

Each task asks one question of one table. The table is written to
``table.csv`` and the agent computes the answer with the shell tool under a
budget of three calls, so the question has to be turned into one or two
commands rather than explored row by row. The hidden check is
:func:`matches`, a normalizer over the dataset's gold answer: numbers
compare with tolerance so a rounding or a percent sign is not a failure,
strings compare casefolded with their whitespace collapsed.

Dataset ``Multilingual-Multimodal-NLP/TableBench``, the raw
``TableBench.jsonl`` (886 rows), Apache-2.0, pinned at revision
``a23c244f9ccae1ea238d614fe7620984707e411a`` (2025-04-18), transcribed on
2026-09-12.

The transcriber keeps only what a shell one-liner can be graded on: question
types :data:`QTYPES`, an answer that is a scalar (a number, optionally signed
or with a percent or currency sign, or a short string of at most
:data:`MAX_STRING` characters holding no comma), and a table whose JSON is at
most :data:`MAX_TABLE_BYTES`. File order is kept, so the pinned file is a
prefix of the dataset.

The pinned file serves two families. ``tables`` takes the records at **even**
positions and :mod:`suite.families.api` the records at **odd** positions, so
a suite holding both never asks the same question twice.
"""

from __future__ import annotations

import csv
import io
import json
import re
from typing import Any

import requests

from suite.families import family
from suite.tasks import Check, Task

DATASET = "Multilingual-Multimodal-NLP/TableBench"
FILE_URL = f"https://huggingface.co/datasets/{DATASET}/resolve/main/TableBench.jsonl"
LICENSE = "Apache-2.0"
REVISION = "a23c244f9ccae1ea238d614fe7620984707e411a"
FETCHED = "2026-09-12"

QTYPES = ("NumericalReasoning", "FactChecking")
"""The question types the family carries: the ones whose answer is one value."""
MAX_STRING = 40
"""Characters a string answer may hold to count as a scalar."""
MAX_TABLE_BYTES = 3000
"""Bytes a table's JSON may hold, so the whole table fits a prompt's working directory."""

SHELL_BUDGET = 3

ABS_TOLERANCE = 0.011
"""Absolute slack on a numeric answer — enough for a gold answer rounded to two decimals."""
REL_TOLERANCE = 0.01
"""Relative slack on a numeric answer, for the totals whose scale makes absolute slack meaningless."""

INSTRUCTION = ("table.csv in the working directory holds the table. Use the shell tool to compute the answer. "
               "Return it as result: a number as a JSON number (rounded to 2 decimals when it is not an integer), "
               "otherwise a short string.")

_NUMBER = re.compile(r"^[+-]?(?:\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?|\.\d+)$")
"""One number, its thousands separators grouped by three — so ``1,234.5`` reads as a number and the
list ``1969, 1971, 1975`` does not."""
_NOISE = str.maketrans("", "", "$€£¥%" + " \t\u00a0")
"""Currency, the percent sign and whitespace — an ordinary space among them, so ``1 234`` groups too:
never part of the value, always droppable."""


def _number(value: Any) -> float | None:
    """The value as a float when it reads as one number, else ``None``; currency, a percent sign and thousands separators are noise."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if not isinstance(value, str):
        return None
    s = value.translate(_NOISE)
    return float(s.replace(",", "")) if _NUMBER.match(s) else None


def _text(value: Any) -> str:
    return " ".join(str(value).split()).casefold()


def matches(result: Any, gold: str) -> bool:
    """Whether ``result`` answers what ``gold`` answers: numbers within tolerance, strings up to case and whitespace.

    A result that reads as a number is graded as a number, so the string
    ``"37.6%"`` and the JSON number ``37.64`` both answer a gold ``37.64%``.
    A number against a non-numeric gold, or the reverse, never matches.
    """
    g, r = _number(gold), _number(result)
    if g is None or r is None:
        return g is None and r is None and _text(result) == _text(gold)
    return abs(r - g) <= ABS_TOLERANCE or (g != 0 and abs(r - g) / abs(g) <= REL_TOLERANCE)


def check_for(gold: str) -> Check:
    """The hidden test for one question: :func:`matches` against that question's gold answer."""
    return lambda result, workdir: matches(result, gold)


RESULT_SCALAR = {"type": "object", "required": ["result"], "properties": {"result": {"type": ["number", "string"]}}}
"""One value, of either shape the instruction allows."""


def table_csv(record: dict[str, Any]) -> str:
    """The record's table as CSV: the header row, then the rows, newline-terminated for a POSIX working directory."""
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(record["columns"])
    writer.writerows(record["data"])
    return buf.getvalue()


def _scalar(answer: str) -> bool:
    a = answer.strip()
    if not a:
        return False
    return _number(a) is not None or (len(a) <= MAX_STRING and "," not in a)


def fetch(n: int) -> list[dict[str, Any]]:
    """Transcribe the first ``n`` rows the filters keep, in file order, into pinned records."""
    body = requests.get(FILE_URL, timeout=120)
    body.raise_for_status()
    out: list[dict[str, Any]] = []
    for line in body.text.splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row["qtype"] not in QTYPES or not _scalar(row["answer"]) or len(json.dumps(row["table"])) > MAX_TABLE_BYTES:
            continue
        out.append({"id": row["id"], "qtype": row["qtype"], "qsubtype": row["qsubtype"], "columns": row["table"]["columns"],
                    "data": row["table"]["data"], "question": row["question"], "answer": row["answer"]})
        if len(out) == n:
            break
    return out


def records(step: int) -> list[dict[str, Any]]:
    """The pinned records at ``step``'s side of the file: 0 for ``tables``, 1 for ``api``."""
    from suite.families import FAMILIES

    return FAMILIES["tables"].records()[step::2]


@family("tables", source=f"{DATASET} [TableBench.jsonl] ({LICENSE}, rev {REVISION[:8]}); the even records, the odd ones being `api`'s",
        fetch=fetch)
def tasks() -> list[Task]:
    return [Task(f"tables/{r['id'][:8]}", f"{r['question'].strip()} {INSTRUCTION}", ("file-tool", "shell-tool", "tool-budget"),
                 RESULT_SCALAR, check_for(r["answer"]), shell_budget=SHELL_BUDGET, files={"table.csv": table_csv(r)})
            for r in records(0)]
