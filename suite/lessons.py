"""Lessons of the world, and the symptom a failed row shows.

A *lesson* is a convention of the world that a general model gets wrong on
first contact and that a record could carry to the next pass. A task that
turns on one names it in ``Task.lesson``; the ``conventions`` and
``transfer`` families carry the hand-written instances and the
``curriculum`` family generates many clothes for each. Every lesson is
tiered by how its failure shows in the trace:

- ``loud`` — the tool error names the convention (a 410 naming the ``/v2``
  route, a 401 naming the token file, a parse error on the byte order mark);
- ``visible`` — the failure is silent but the convention is in the tool
  output the pass already read (a ``next`` field on the page it stopped at,
  a quoted comma or a footer row in the file it counted);
- ``invisible`` — nothing in the trace shows it (a file with no trailing
  newline reads the same as one with).

The **naive outcome** of a task is what its scripted first-contact policy
(:attr:`suite.tasks.Task.stub`) returns against a fault-free world — the
answer or the error a policy that does not know the lesson produces. It is
derived by running the policy, never stored beside the gold, so a task
whose policy is naive carries its own same-shape detector: a failed row
whose result equals the naive outcome, or whose error names the naive
error's class, is a **naive-shape** failure — the lesson missed in exactly
the way first contact misses it — and needs no judge to say so. Any other
failure is ``wrong`` (a different wrong answer) or ``error:<class>`` (a
harness or tool failure), and a passed row is ``pass``.
"""

from __future__ import annotations

import re
import tempfile
from functools import cache
from pathlib import Path
from typing import TYPE_CHECKING, Any

from suite.faults import FaultProfile

if TYPE_CHECKING:
    from suite.tasks import Task

LESSONS: dict[str, dict[str, Any]] = {
    "trailing-newline": {"tier": "invisible", "means": "files whose last line carries no newline; `wc -l` counts one fewer per file",
                         "keywords": ("newline", "wc -l", "trailing", "last line", "awk")},
    "paged-api": {"tier": "visible", "means": "a listing route pages; each page names the next or null",
                  "keywords": ("page", "pagin", "next")},
    "moved-v2": {"tier": "loud", "means": "a route answers 410 Gone naming its successor under /v2",
                 "keywords": ("/v2", "410", "moved", "gone")},
    "csv-quoted": {"tier": "visible", "means": "a CSV field may be quoted and hold a comma; splitting on commas shifts its columns",
                   "keywords": ("quot", "csv", "comma", "fpat", "csv module")},
    "footer-row": {"tier": "visible", "means": "an exported CSV ends with a TOTAL row that is not a record",
                   "keywords": ("footer", "total row", "summary row", "last row", "trailer")},
    "token-route": {"tier": "loud", "means": "routes under /secure answer 401 unless ?token= carries the token in token.txt",
                    "keywords": ("token", "401", "unauthori", "secure")},
    "bom": {"tier": "loud", "means": "a JSON file opens with a byte order mark that a strict parser refuses",
            "keywords": ("bom", "byte order", "﻿", "utf-8-sig")},
}
"""Every lesson the suite's families name, its tier, and the words a record that carries it would use — the
mention heuristic the evolution log reads over the records a pass had in context."""

TIERS = ("loud", "visible", "invisible")


def tier(lesson: str | None) -> str | None:
    return LESSONS[lesson]["tier"] if lesson in LESSONS else None


def mentions(lesson: str, text: str) -> bool:
    """Whether ``text`` (a record's decision, latch and context) uses the lesson's words — a heuristic, logged as such."""
    t = text.lower()
    return any(k in t for k in LESSONS[lesson]["keywords"])


# --- the naive outcome ----------------------------------------------------------------------

_HTTP = re.compile(r"HTTP (\d{3})")
_CLASSES = (("HTTP 410", "http-410"), ("HTTP 401", "http-401"), ("HTTP 404", "http-404"), ("HTTP 502", "http-502"),
            ("call budget", "budget"), ("exited", "shell-exit"), ("timed out", "shell-timeout"), ("turn limit", "turn-limit"),
            ("model call failed", "model-call"), ("not JSON", "not-json"), ("JSONDecodeError", "json-decode"), ("no scripted policy", "no-policy"))


def error_class(error: dict[str, Any] | None) -> str:
    """The class of a row's error, read off its message and cause by the tool layer's own markers."""
    if not error:
        return "none"
    text = f"{error.get('message') or ''} {error.get('cause') or ''}"
    for marker, cls in _CLASSES:
        if marker in text:
            return cls
    return "other"


@cache
def naive_outcome(task_id: str) -> dict[str, Any] | None:
    """What the task's naive policy produces against a fault-free world: ``{"result": …}`` or ``{"error": …}``; ``None``
    when the task carries no scripted policy. Derived by running the policy, cached per task id."""
    import suite as _suite
    from suite.agent import Script
    from suite.tools import ToolError, Tools

    spec: Task = _suite.current().by_id[task_id]
    if spec.stub is None:
        return None
    workdir = Path(tempfile.mkdtemp(prefix="hgi-naive-"))
    spec.setup(workdir)
    tools = Tools(task=spec.id, workdir=workdir, profile=FaultProfile(http_fault_fraction=0.0), routes=spec.routes,
                  shell_budget=spec.shell_budget, http_budget=spec.http_budget)
    try:
        return {"result": spec.stub(Script(tools, []))}
    except ToolError as e:
        return {"error": {"message": str(e), "cause": e.cause}}
    except Exception as e:  # the naive policy tripping over the world, as the stub agent reports it
        return {"error": {"message": f"{type(e).__name__}: {e}"[:200], "cause": None}}


def _same(a: Any, b: Any) -> bool:
    if isinstance(a, bool) or isinstance(b, bool):
        return a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(a - b) < 1e-6
    if isinstance(a, str) and isinstance(b, (int, float)) or isinstance(b, str) and isinstance(a, (int, float)):
        try:
            return abs(float(a) - float(b)) < 1e-6
        except ValueError:
            return False
    return a == b


def symptom(task: Task, row: dict[str, Any]) -> str:
    """``pass``, ``naive`` (the row reproduces the naive outcome), ``wrong`` (another wrong answer) or ``error:<class>``."""
    from hgi.index import row_passed

    if row_passed(row):
        return "pass"
    naive = naive_outcome(task.id)
    error = row.get("error")
    if naive is not None:
        if "result" in naive and not error and _same(row.get("result"), naive["result"]):
            return "naive"
        if "error" in naive and error and error_class(error) == error_class(naive["error"]) and error_class(error) != "other":
            return "naive"
    if error:
        return f"error:{error_class(error)}"
    return "wrong"
