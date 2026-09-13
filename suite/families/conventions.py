"""The conventions family: a world with conventions the model cannot know before it enters.

Each task turns on a fact of this world that a general model gets wrong on
first contact and that a record could carry to the next pass — a file with
no trailing newline that ``wc -l`` undercounts, an API that pages, an API
that has moved under ``/v2``, a CSV with quoted commas, a config with a byte
order mark. The lesson is a convention of the world, not a fact about one
task: the same convention recurs across tasks so a promoted record has
anchors and a hook. Budgets make a convention cost a call, so the oracle can
score whether it was learned.

The scripted policies are naive: they do what a first contact does, so the
stub's curve on this family is flat and honest.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from suite.families import family
from suite.families.genesis import RESULT_INT, RESULT_STR, result_object
from suite.tasks import Task

if TYPE_CHECKING:
    from suite.agent import Script


def _no_newline(counts: dict[str, int]) -> dict[str, str]:
    """Files whose last line carries no newline — ``wc -l`` counts one fewer per file."""
    return {name: "\n".join(f"row {i}" for i in range(n)) for name, n in counts.items()}


NO_NEWLINE = _no_newline({"a.txt": 4, "b.txt": 6, "c.txt": 1, "d.txt": 5, "e.txt": 2})   # 18 lines; wc -l says 13
NO_NEWLINE_2 = _no_newline({"x.log": 7, "y.log": 3, "z.log": 9})                          # 19 lines; wc -l says 16

PEOPLE = "name,city,age\n\"Doe, Jane\",Berlin,34\nAda Lovelace,London,36\n\"Smith, John\",Berlin,41\nGrace Hopper,New York,85\n\"Turing, Alan\",Berlin,41\nLinus Torvalds,Helsinki,54\n"
ORDERS = "order,customer,total\n1001,\"Acme, Inc.\",250.00\n1002,Globex,99.50\n1003,\"Initech, LLC\",1200.00\n1004,Globex,15.25\n1005,\"Acme, Inc.\",75.00\n"

BOM = "﻿"


def _naive_count(names: list[str]):
    def policy(s: "Script"):
        out = s.shell("wc -l " + " ".join(names))
        return int(out.strip().splitlines()[-1].split()[0])
    return policy


def _naive_paged(s: "Script"):
    return sum(s.get("/items")["items"])


def _naive_versioned(s: "Script"):
    return s.get("/users/7")["name"]


def _naive_csv(column: int, value: str):
    def policy(s: "Script"):
        return int(s.shell(f"awk -F, 'NR>1 && ${column}==\"{value}\"' people.csv | wc -l").strip())
    return policy


def _naive_bom(s: "Script"):
    config = json.loads(s.read("config.json"))  # raises on the byte order mark
    report = {"title": config["title"], "count": len(config["items"])}
    s.write("report.json", json.dumps(report))
    return report


@family("conventions", source="hand-written; conventions of this world a model meets on first contact")
def tasks() -> list[Task]:
    return [
        Task("conventions/lines_without_newline",
             "Five files a.txt..e.txt are in the working directory; none ends with a newline. Return the total number of lines across them as result, using the shell tool. You have a budget of 2 shell calls.",
             ("shell-tool", "tool-budget"), RESULT_INT, lambda r, w: r == 18, shell_budget=2, files=NO_NEWLINE,
             stub=_naive_count([f"{c}.txt" for c in "abcde"])),
        Task("conventions/log_lines",
             "Three log files x.log, y.log, z.log are in the working directory. Return the total number of lines across them as result, using the shell tool. You have a budget of 1 shell call.",
             ("shell-tool", "tool-budget"), RESULT_INT, lambda r, w: r == 19, shell_budget=1, files=NO_NEWLINE_2,
             stub=_naive_count(["x.log", "y.log", "z.log"])),
        Task("conventions/paged_sum",
             "GET /items from the API and return the sum of every item as result.", ("http-tool", "error-wrapping"),
             RESULT_INT, lambda r, w: r == 50, http_budget=4,
             routes={"/items": {"items": [3, 5, 8], "next": "/items?page=2"}, "/items?page=2": {"items": [13, 21], "next": None}},
             stub=_naive_paged),
        Task("conventions/paged_count",
             "GET /users from the API and return the number of users whose active field is true as result.", ("http-tool", "error-wrapping"),
             RESULT_INT, lambda r, w: r == 3, http_budget=5,
             routes={"/users": {"items": [{"id": 1, "active": True}, {"id": 2, "active": False}], "next": "/users?page=2"},
                     "/users?page=2": {"items": [{"id": 3, "active": True}, {"id": 4, "active": True}], "next": "/users?page=3"},
                     "/users?page=3": {"items": [{"id": 5, "active": False}], "next": None}},
             stub=lambda s: sum(1 for u in s.get("/users")["items"] if u["active"])),
        Task("conventions/versioned_user",
             "GET /users/7 and return the user's name as result.", ("http-tool", "error-wrapping"),
             RESULT_STR, lambda r, w: r == "Ada", http_budget=2,
             routes={"/users/7": {"$error": {"message": "GET /users/7 failed", "cause": "HTTP 410 Gone: this API serves /v2/users/7"}},
                     "/v2/users/7": {"id": 7, "name": "Ada"}},
             stub=_naive_versioned),
        Task("conventions/versioned_status",
             "GET /status and return the string 'ok' as result when the response's ok field is true.", ("http-tool", "error-wrapping"),
             RESULT_STR, lambda r, w: r == "ok", http_budget=2,
             routes={"/status": {"$error": {"message": "GET /status failed", "cause": "HTTP 410 Gone: this API serves /v2/status"}},
                     "/v2/status": {"ok": True}},
             stub=lambda s: "ok" if s.get("/status")["ok"] else "not ok"),
        Task("conventions/csv_quoted_city",
             "people.csv is in the working directory. Return the number of people whose city is Berlin as result, using the shell tool. You have a budget of 2 shell calls.",
             ("shell-tool", "file-tool", "tool-budget"), RESULT_INT, lambda r, w: r == 3, shell_budget=2, files={"people.csv": PEOPLE},
             stub=_naive_csv(2, "Berlin")),
        Task("conventions/csv_quoted_total",
             "orders.csv is in the working directory. Return the sum of the total column over the orders whose customer is \"Acme, Inc.\" as result, using the shell tool. You have a budget of 2 shell calls.",
             ("shell-tool", "file-tool", "tool-budget"), {"type": "object", "required": ["result"], "properties": {"result": {"type": "number"}}},
             lambda r, w: isinstance(r, (int, float)) and abs(r - 325.0) < 1e-6, shell_budget=2, files={"orders.csv": ORDERS},
             stub=lambda s: float(s.shell("awk -F, 'NR>1 && $2==\"Acme, Inc.\" {t+=$3} END {print t+0}' orders.csv").strip())),
        Task("conventions/bom_config",
             "Read config.json, then write report.json containing {\"title\": <config.title>, \"count\": <length of config.items>} and return that object as result.",
             ("file-tool", "output-schema"), result_object("title", "count"),
             lambda r, w: isinstance(r, dict) and r.get("title") == "Q4" and r.get("count") == 4 and _report_ok(w, "Q4", 4),
             files={"config.json": BOM + json.dumps({"title": "Q4", "items": ["a", "b", "c", "d"]})}, stub=_naive_bom),
        Task("conventions/bom_settings",
             "Read settings.json, then return {\"name\": <settings.name>, \"enabled\": <number of entries in settings.features whose value is true>} as result.",
             ("file-tool", "output-schema"), result_object("name", "enabled"),
             lambda r, w: r == {"name": "edge", "enabled": 2},
             files={"settings.json": BOM + json.dumps({"name": "edge", "features": {"a": True, "b": False, "c": True}})},
             stub=lambda s: {"name": json.loads(s.read("settings.json"))["name"], "enabled": 2}),
    ]


def _report_ok(workdir, title: str, count: int) -> bool:
    try:
        return json.loads((workdir / "report.json").read_text()) == {"title": title, "count": count}
    except Exception:
        return False
