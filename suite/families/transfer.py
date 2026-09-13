"""The transfer family: the conventions of the ``conventions`` family, re-dressed.

The ``conventions`` family grades whether a convention of this world is
learned; this family grades whether the *lesson* is learned rather than the
task. Each task here turns on a convention that ``conventions`` already
carries — files with no trailing newline that ``wc -l`` undercounts, an API
that pages, an API that has moved under ``/v2`` — worn in different clothes:
different file names, a different API surface, different endpoints. A record
whose hook keys on the convention (``shell-tool`` files whose count is short,
an ``http-tool`` route that pages or answers 410) transfers and scores here;
a record that memorised ``a.txt`` or ``/items`` or ``/users/7`` does not. So
a record admitted while scoring ``conventions`` (or ``api``) is scored again
on a suite that holds this family beside it.

The conventions themselves are not re-authored: the no-trailing-newline
files are built by :func:`suite.families.conventions._no_newline` and counted
naively by :func:`suite.families.conventions._naive_count`, the same
mechanisms ``conventions`` uses, so the two families share one convention and
differ only in their clothes. The scripted policies are naive — they do what
a first contact does — so the stub's curve on this family is flat and honest.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from suite.families import family
from suite.families.conventions import _naive_count, _no_newline
from suite.families.genesis import RESULT_INT, RESULT_STR
from suite.tasks import Task

if TYPE_CHECKING:
    from suite.agent import Script


# The no-trailing-newline convention, under names `conventions` never uses.
REPORT_LINES = _no_newline({"part-1.tsv": 2, "part-2.tsv": 6, "part-3.tsv": 3, "part-4.tsv": 4})   # 15 lines; wc -l says 11
CHUNK_LINES = _no_newline({"chunk_00.dat": 5, "chunk_01.dat": 9})                                   # 14 lines; wc -l says 12


def _naive_paged_records(s: "Script"):
    """Sum only the first page — the naive read of a paged API."""
    return sum(s.get("/records")["items"])


def _naive_paged_accounts(s: "Script"):
    return sum(1 for a in s.get("/accounts")["items"] if a["active"])


def _naive_moved_account(s: "Script"):
    return s.get("/account/42")["name"]  # raises on the 410


def _naive_moved_health(s: "Script"):
    return "ok" if s.get("/health")["ok"] else "down"  # raises on the 410


@family("transfer", source="hand-written; the `conventions` conventions re-dressed — same lessons, different clothes")
def tasks() -> list[Task]:
    return [
        # The no-trailing-newline convention, on files `conventions` never names.
        Task("transfer/report_lines",
             "Four files part-1.tsv..part-4.tsv are in the working directory; none ends with a newline. Return the total number of lines across them as result, using the shell tool. You have a budget of 2 shell calls.",
             ("shell-tool", "tool-budget"), RESULT_INT, lambda r, w: r == 15, shell_budget=2, files=REPORT_LINES,
             stub=_naive_count([f"part-{i}.tsv" for i in range(1, 5)])),
        Task("transfer/chunk_lines",
             "Two files chunk_00.dat and chunk_01.dat are in the working directory. Return the total number of lines across them as result, using the shell tool. You have a budget of 1 shell call.",
             ("shell-tool", "tool-budget"), RESULT_INT, lambda r, w: r == 14, shell_budget=1, files=CHUNK_LINES,
             stub=_naive_count(["chunk_00.dat", "chunk_01.dat"])),
        # The paging convention, on a different API surface (`/records`, `/accounts`, not `/items`, `/users`).
        Task("transfer/paged_total",
             "GET /records from the API and return the sum of every item as result.", ("http-tool", "error-wrapping"),
             RESULT_INT, lambda r, w: r == 27, http_budget=4,
             routes={"/records": {"items": [4, 9, 2], "next": "/records?page=2"}, "/records?page=2": {"items": [7, 5], "next": None}},
             stub=_naive_paged_records),
        Task("transfer/paged_active",
             "GET /accounts from the API and return the number of accounts whose active field is true as result.", ("http-tool", "error-wrapping"),
             RESULT_INT, lambda r, w: r == 3, http_budget=5,
             routes={"/accounts": {"items": [{"id": 1, "active": True}, {"id": 2, "active": False}], "next": "/accounts?page=2"},
                     "/accounts?page=2": {"items": [{"id": 3, "active": True}, {"id": 4, "active": True}], "next": "/accounts?page=3"},
                     "/accounts?page=3": {"items": [{"id": 5, "active": False}], "next": None}},
             stub=_naive_paged_accounts),
        # The `/v2` move, on endpoints `conventions` never names (`/account/42`, `/health`, not `/users/7`, `/status`).
        Task("transfer/moved_account",
             "GET /account/42 and return the account holder's name as result.", ("http-tool", "error-wrapping"),
             RESULT_STR, lambda r, w: r == "Lin", http_budget=2,
             routes={"/account/42": {"$error": {"message": "GET /account/42 failed", "cause": "HTTP 410 Gone: this API serves /v2/account/42"}},
                     "/v2/account/42": {"id": 42, "name": "Lin"}},
             stub=_naive_moved_account),
        Task("transfer/moved_health",
             "GET /health and return the string 'ok' as result when the response's ok field is true.", ("http-tool", "error-wrapping"),
             RESULT_STR, lambda r, w: r == "ok", http_budget=2,
             routes={"/health": {"$error": {"message": "GET /health failed", "cause": "HTTP 410 Gone: this API serves /v2/health"}},
                     "/v2/health": {"ok": True}},
             stub=_naive_moved_health),
    ]
