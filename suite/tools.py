"""The tool layer with injected faults. Every tool call is a traced op.

Faults are deterministic in ``(pass, task, call number)`` so that two runs
over the same suite hash see the same world: the HTTP tool fails the first
call of a task with a transient 502 on a fixed fraction of tasks; the shell
tool refuses calls past its budget; the file tool is honest.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import weave

FAULT_FRACTION = 0.5
"""The fraction of HTTP tasks whose first call returns a transient 502."""


class ToolError(Exception):
    def __init__(self, message: str, cause: str | None = None, transient: bool = False):
        super().__init__(message)
        self.cause = cause
        self.transient = transient


def _faulted(pass_: int, task: str) -> bool:
    h = int(hashlib.sha256(f"{task}".encode()).hexdigest(), 16)
    return (h % 100) < FAULT_FRACTION * 100


ROUTES: dict[str, Any] = {
    "/numbers": [3, 5, 8, 13, 21],
    "/users/7": {"id": 7, "name": "Ada"},
    "/status": {"ok": True},
}


@dataclass
class Tools:
    pass_: int
    task: str
    workdir: Path
    shell_budget: int | None = None
    calls: dict[str, int] = field(default_factory=lambda: {"http": 0, "shell": 0, "file": 0})
    errors: list[dict[str, Any]] = field(default_factory=list)
    """Every ToolError raised, in order — what a reader of the trace would see."""

    def _raise(self, message: str, cause: str | None = None, transient: bool = False):
        self.errors.append({"message": message, "cause": cause, "transient": transient})
        raise ToolError(message, cause=cause, transient=transient)

    @property
    def total_calls(self) -> int:
        return sum(self.calls.values())

    @weave.op(name="tool.http_get")
    def http_get(self, path: str) -> Any:
        self.calls["http"] += 1
        if self.calls["http"] == 1 and _faulted(self.pass_, self.task):
            self._raise(f"GET {path} failed", cause=f"HTTP 502 Bad Gateway from {path} (transient)", transient=True)
        if path not in ROUTES:
            self._raise(f"GET {path} failed", cause=f"HTTP 404 Not Found for {path}")
        return ROUTES[path]

    @weave.op(name="tool.shell")
    def shell(self, command: str) -> str:
        self.calls["shell"] += 1
        if self.shell_budget is not None and self.calls["shell"] > self.shell_budget:
            self._raise("shell call refused", cause=f"call budget of {self.shell_budget} exceeded at call {self.calls['shell']}")
        proc = subprocess.run(command, shell=True, cwd=self.workdir, capture_output=True, text=True, timeout=10)
        if proc.returncode != 0:
            self._raise(f"shell exited {proc.returncode}", cause=proc.stderr.strip()[:200])
        return proc.stdout

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
        {"type": "function", "function": {"name": "http_get", "description": "GET a path from the task's API; may fail transiently.",
                                          "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
        {"type": "function", "function": {"name": "shell", "description": "Run a shell command in the task's working directory. Calls are budgeted.",
                                          "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}}},
        {"type": "function", "function": {"name": "read_file", "description": "Read a file in the working directory.",
                                          "parameters": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}}},
        {"type": "function", "function": {"name": "write_file", "description": "Write a file in the working directory.",
                                          "parameters": {"type": "object", "properties": {"name": {"type": "string"}, "content": {"type": "string"}}, "required": ["name", "content"]}}},
    ]

    def dispatch(self, name: str, arguments: str) -> str:
        args = json.loads(arguments or "{}")
        try:
            return json.dumps(getattr(self, name)(**args))
        except ToolError as e:
            return json.dumps({"error": str(e), "cause": e.cause, "transient": e.transient})
