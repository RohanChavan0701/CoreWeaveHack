"""The api family: the same TableBench questions, reached through a paged mock API instead of a file.

A task's table is not on disk. ``/table`` describes it — the columns, how
many rows there are, and the path of the first page — and the rows arrive
:data:`PAGE_SIZE` at a time, each page naming the next or ``null`` at the
end. The budget is exactly the pages plus two, so the agent has room for the
description and one recovered failure and none for a page it fetched twice.
What the family grades is therefore the walk, not the arithmetic: the same
:func:`suite.families.tables.matches` normalizer decides the answer.

The family is derived, not fetched: it reads the pinned records of the
``tables`` family, so the dataset is transcribed once. ``tables`` takes the
records at **even** positions of that file and ``api`` the records at **odd**
positions, so a suite holding both never asks the same question twice. When
the ``tables`` file is absent the family holds no tasks.
"""

from __future__ import annotations

from typing import Any

from suite.families import family
from suite.families.tables import RESULT_SCALAR, check_for, records
from suite.tasks import Task

PAGE_SIZE = 8
"""Rows a page of ``/table/rows`` carries."""
BUDGET_SLACK = 2
"""Calls the budget allows beyond the pages: the description, and one transient failure recovered from."""

INSTRUCTION = ("The API at /table describes a table; its rows are paged. Fetch what you need and return the answer as result: "
               "a number as a JSON number (rounded to 2 decimals when it is not an integer), otherwise a short string.")


def page_path(k: int) -> str:
    return f"/table/rows?page={k}"


def pages(rows: list[list[Any]]) -> int:
    """How many pages the rows fill; an empty table still answers one, empty, page."""
    return max(1, -(-len(rows) // PAGE_SIZE))


def routes(record: dict[str, Any]) -> dict[str, Any]:
    """The mock API: the description at ``/table``, then one route per page, the last naming no next."""
    rows = record["data"]
    n = pages(rows)
    out: dict[str, Any] = {"/table": {"columns": list(record["columns"]), "rows": len(rows), "first": page_path(1)}}
    for k in range(1, n + 1):
        out[page_path(k)] = {"rows": rows[(k - 1) * PAGE_SIZE:k * PAGE_SIZE], "next": page_path(k + 1) if k < n else None}
    return out


@family("api", source="derived from the `tables` family's pinned file (TableBench, Apache-2.0); the odd records, served as a paged API")
def tasks() -> list[Task]:
    return [Task(f"api/{r['id'][:8]}", f"{r['question'].strip()} {INSTRUCTION}", ("http-tool", "error-wrapping", "tool-budget"),
                 RESULT_SCALAR, check_for(r["answer"]), http_budget=pages(r["data"]) + BUDGET_SLACK, routes=routes(r))
            for r in records(1)]
