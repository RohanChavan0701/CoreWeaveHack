"""The genesis family: the six hand-written tasks the demonstration of spec § 14 ran on.

Each task carries its scripted policy for the deterministic stub: the naive
behaviour, applying a record in context by keyword — *retry* retries a
transient failure once, *cause* carries the cause on the error, *batch*
batches budgeted shell calls (see :class:`suite.agent.Script`).
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from suite.families import family
from suite.tasks import Task

if TYPE_CHECKING:
    from suite.agent import Script

RESULT_INT = {"type": "object", "required": ["result"], "properties": {"result": {"type": "integer"}}}
RESULT_STR = {"type": "object", "required": ["result"], "properties": {"result": {"type": "string"}}}


def result_object(*required: str) -> dict:
    return {"type": "object", "required": ["result"], "properties": {"result": {"type": "object", "required": list(required)}}}


LINES = {f"{c}.txt": "\n".join(f"line {i}" for i in range(n)) + "\n" for c, n in zip("abcde", (3, 5, 2, 7, 1))}


def _sum_numbers(s: "Script"):
    return sum(s.get("/numbers"))


def _fetch_user_name(s: "Script"):
    return s.get("/users/7")["name"]


def _status_ok(s: "Script"):
    return "ok" if s.get("/status")["ok"] else "not ok"


def _count_lines(s: "Script"):
    names = [f"{c}.txt" for c in "abcde"]
    if s.batch:
        out = s.shell("wc -l " + " ".join(names))
        return int(out.strip().splitlines()[-1].split()[0])
    return sum(int(s.shell(f"wc -l {n}").split()[0]) for n in names)


def _write_report(s: "Script"):
    config = json.loads(s.read("config.json"))
    report = {"title": config["title"], "count": len(config["items"])}
    s.write("report.json", json.dumps(report))
    return report


@family("genesis", source="hand-written; the demonstration suite of spec § 14")
def tasks() -> list[Task]:
    return [
        Task("genesis/sum_numbers", "GET /numbers from the API and return the sum of the list as result.", ("http-tool", "error-wrapping"),
             RESULT_INT, lambda r, w: r == 50, routes={"/numbers": [3, 5, 8, 13, 21]}, stub=_sum_numbers),
        Task("genesis/fetch_user_name", "GET /users/7 and return the user's name as result.", ("http-tool", "error-wrapping"),
             RESULT_STR, lambda r, w: r == "Ada", routes={"/users/7": {"id": 7, "name": "Ada"}}, stub=_fetch_user_name),
        Task("genesis/status_ok", "GET /status and return the string 'ok' as result when the response's ok field is true.", ("http-tool", "error-wrapping"),
             RESULT_STR, lambda r, w: r == "ok", routes={"/status": {"ok": True}}, stub=_status_ok),
        Task("genesis/count_lines", "Five files a.txt..e.txt are in the working directory. Return the total number of lines across them as result, using the shell tool. You have a budget of 2 shell calls.",
             ("shell-tool", "tool-budget"), RESULT_INT, lambda r, w: r == 18, shell_budget=2, files=LINES, stub=_count_lines),
        Task("genesis/write_report", "Read config.json, then write report.json containing {\"title\": <config.title>, \"count\": <length of config.items>} and return that object as result.",
             ("file-tool", "output-schema"), result_object("title", "count"),
             lambda r, w: isinstance(r, dict) and r.get("title") == "Q3" and r.get("count") == 3,
             files={"config.json": json.dumps({"title": "Q3", "items": ["a", "b", "c"]})}, stub=_write_report),
        Task("genesis/schema_answer", "Return result = {\"answer\": 42, \"unit\": \"n\"} exactly.", ("output-schema",),
             result_object("answer", "unit"), lambda r, w: r == {"answer": 42, "unit": "n"}, stub=lambda s: {"answer": 42, "unit": "n"}),
    ]
