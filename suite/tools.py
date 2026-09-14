"""The tool layer with injected faults. Every tool call is a traced op.

Faults are deterministic in the task so that two runs over the same suite
hash see the same world (:class:`suite.faults.FaultProfile`): the HTTP tool
fails the leading calls of a task with a transient 502 on a fixed fraction
of tasks and refuses calls past a budget; the shell tool refuses calls past
its budget and may truncate its output; the file tool is honest. A route
may answer with an error of its own — the world's conventions live there.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import weave

from suite.faults import FaultProfile

CAUSE_MARKERS = ("HTTP ", "call budget", "exited", "[truncated]")
"""Every cause the tool layer raises opens with one of these; the oracle's cause scorer reads them."""

BUDGET_SENTINEL = ".hgi_budget_exceeded"
"""A refused over-budget call drops this marker in the working directory, naming the overage. A hidden check that
grades the answer alone — as :mod:`suite.families.reasoning_core` does, where a witness can be produced unaided — reads
it to fail a row whose answer was bought past budget; a check that grades data (mbpp, curriculum) never looks and the
marker is inert."""


class ToolError(Exception):
    def __init__(self, message: str, cause: str | None = None, transient: bool = False):
        super().__init__(message)
        self.cause = cause
        self.transient = transient


@dataclass
class Tools:
    task: str
    workdir: Path
    profile: FaultProfile = field(default_factory=FaultProfile)
    routes: dict[str, Any] = field(default_factory=dict)
    shell_budget: int | None = None
    http_budget: int | None = None
    calls: dict[str, int] = field(default_factory=lambda: {"http": 0, "shell": 0, "file": 0})
    errors: list[dict[str, Any]] = field(default_factory=list)
    """Every ToolError raised, in order — what a reader of the trace would see."""
    commands: list[str] = field(default_factory=list)
    """Every shell command issued, in order — the replayable part of the pass's method."""

    def __post_init__(self):
        if self.http_budget is None:
            self.http_budget = self.profile.http_budget

    def _raise(self, message: str, cause: str | None = None, transient: bool = False):
        self.errors.append({"message": message, "cause": cause, "transient": transient})
        raise ToolError(message, cause=cause, transient=transient)

    def _mark_over_budget(self, cause: str) -> None:
        """Record an over-budget refusal in the working directory (:data:`BUDGET_SENTINEL`), so a hidden check that
        grades the answer alone can still fail a row whose answer was bought past budget."""
        try:
            (self.workdir / BUDGET_SENTINEL).write_text(cause + "\n")
        except OSError:  # a working directory that cannot be written is the task's failure to report, not the marker's
            pass

    @property
    def total_calls(self) -> int:
        return sum(self.calls.values())

    @property
    def budgets(self) -> dict[str, int]:
        return {k: v for k, v in {"shell": self.shell_budget, "http": self.http_budget}.items() if v is not None}

    def budget_respected(self) -> bool:
        return all(self.calls[tool] <= budget for tool, budget in self.budgets.items())

    @weave.op(name="tool.http_get")
    def http_get(self, path: str) -> Any:
        self.calls["http"] += 1
        if self.http_budget is not None and self.calls["http"] > self.http_budget:
            cause = f"call budget of {self.http_budget} exceeded at call {self.calls['http']}"
            self._mark_over_budget(cause)
            self._raise("http call refused", cause=cause)
        if self.calls["http"] <= self.profile.http_fault_calls and self.profile.faulted(self.task):
            self._raise(f"GET {path} failed", cause=f"HTTP 502 Bad Gateway from {path} (transient)", transient=True)
        if path not in self.routes:
            self._raise(f"GET {path} failed", cause=f"HTTP 404 Not Found for {path}")
        body = self.routes[path]
        if isinstance(body, dict) and "$error" in body:
            err = body["$error"]
            self._raise(err.get("message", f"GET {path} failed"), cause=err.get("cause"), transient=bool(err.get("transient")))
        return body

    @weave.op(name="tool.shell")
    def shell(self, command: str) -> str:
        self.calls["shell"] += 1
        self.commands.append(command)
        if self.shell_budget is not None and self.calls["shell"] > self.shell_budget:
            cause = f"call budget of {self.shell_budget} exceeded at call {self.calls['shell']}"
            self._mark_over_budget(cause)
            self._raise("shell call refused", cause=cause)
        try:
            proc = subprocess.run(command, shell=True, cwd=self.workdir, capture_output=True, text=True, timeout=30)
        except subprocess.TimeoutExpired:
            self._raise("shell timed out", cause="exited by timeout after 30s")
        if proc.returncode != 0:
            self._raise(f"shell exited {proc.returncode}", cause=f"exited {proc.returncode}: {proc.stderr.strip()[:200]}")
        out = proc.stdout
        limit = self.profile.shell_output_limit
        if limit is not None and len(out) > limit:
            out = out[:limit] + "\n[truncated]"
        return out

    @weave.op(name="tool.read_file")
    def read_file(self, name: str) -> str:
        self.calls["file"] += 1
        return (self.workdir / name).read_text()

    @weave.op(name="tool.write_file")
    def write_file(self, name: str, content: str) -> str:
        self.calls["file"] += 1
        (self.workdir / name).write_text(content)
        return f"wrote {len(content)} bytes to {name}"

    # --- the OpenAI tool schema, derived from the methods above ---------------------
    SCHEMA = [
        {"type": "function", "function": {"name": "http_get", "description": "GET a path from the task's API; may fail transiently. Calls may be budgeted.",
                                          "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
        {"type": "function", "function": {"name": "shell", "description": "Run a shell command in the task's working directory. Calls may be budgeted.",
                                          "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}}},
        {"type": "function", "function": {"name": "read_file", "description": "Read a file in the working directory.",
                                          "parameters": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}}},
        {"type": "function", "function": {"name": "write_file", "description": "Write a file in the working directory.",
                                          "parameters": {"type": "object", "properties": {"name": {"type": "string"}, "content": {"type": "string"}}, "required": ["name", "content"]}}},
    ]

    def dispatch(self, name: str, arguments: str) -> str:
        try:
            args = json.loads(arguments or "{}")
            return json.dumps(getattr(self, name)(**args))
        except ToolError as e:
            return json.dumps({"error": str(e), "cause": e.cause, "transient": e.transient})
        except (json.JSONDecodeError, TypeError, AttributeError, OSError) as e:
            return json.dumps({"error": f"bad tool call: {type(e).__name__}: {e}", "cause": None, "transient": False})
