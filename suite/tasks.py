"""The fixed task suite. Each task states its presentation (the work-shape terms a boot may classify it
under), its prompt, its budget, its output schema, and a hidden test over the agent's result."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from suite import EVALUATION


@dataclass(frozen=True)
class Task:
    id: str
    prompt: str
    shapes: tuple[str, ...]
    """The presentation, in registry work-shape terms — what a boot classifies, never what a hook reads."""
    schema: dict[str, Any]
    check: Callable[[Any], bool]
    shell_budget: int | None = None
    files: dict[str, str] = field(default_factory=dict)
    http: bool = False

    def row(self) -> dict[str, Any]:
        return {"task": self.id, "prompt": self.prompt, "schema": self.schema, "shell_budget": self.shell_budget, "http": self.http}

    def setup(self, workdir: Path) -> None:
        workdir.mkdir(parents=True, exist_ok=True)
        for name, content in self.files.items():
            (workdir / name).write_text(content)


_LINES = {f"{c}.txt": "\n".join(f"line {i}" for i in range(n)) + "\n" for c, n in zip("abcde", (3, 5, 2, 7, 1))}

TASKS: list[Task] = [
    Task("sum_numbers", "GET /numbers from the API and return the sum of the list as result.", ("http-tool", "error-wrapping"),
         {"type": "object", "required": ["result"], "properties": {"result": {"type": "integer"}}}, lambda r: r == 50, http=True),
    Task("fetch_user_name", "GET /users/7 and return the user's name as result.", ("http-tool", "error-wrapping"),
         {"type": "object", "required": ["result"], "properties": {"result": {"type": "string"}}}, lambda r: r == "Ada", http=True),
    Task("status_ok", "GET /status and return the string 'ok' as result when the response's ok field is true.", ("http-tool", "error-wrapping"),
         {"type": "object", "required": ["result"], "properties": {"result": {"type": "string"}}}, lambda r: r == "ok", http=True),
    Task("count_lines", "Five files a.txt..e.txt are in the working directory. Return the total number of lines across them as result, using the shell tool. You have a budget of 2 shell calls.",
         ("shell-tool", "tool-budget"), {"type": "object", "required": ["result"], "properties": {"result": {"type": "integer"}}},
         lambda r: r == 18, shell_budget=2, files=_LINES),
    Task("write_report", "Read config.json, then write report.json containing {\"title\": <config.title>, \"count\": <length of config.items>} and return that object as result.",
         ("file-tool", "output-schema"), {"type": "object", "required": ["result"], "properties": {"result": {"type": "object", "required": ["title", "count"]}}},
         lambda r: isinstance(r, dict) and r.get("title") == "Q3" and r.get("count") == 3,
         files={"config.json": json.dumps({"title": "Q3", "items": ["a", "b", "c"]})}),
    Task("schema_answer", "Return result = {\"answer\": 42, \"unit\": \"n\"} exactly.", ("output-schema",),
         {"type": "object", "required": ["result"], "properties": {"result": {"type": "object", "required": ["answer", "unit"]}}},
         lambda r: r == {"answer": 42, "unit": "n"}),
]

BY_ID = {t.id: t for t in TASKS}


def suite_hash() -> str:
    """The composition guard: a digest of every task's presentation, prompt, schema and budget."""
    payload = json.dumps([t.row() for t in TASKS], sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()[:12]


def presentations() -> list[dict[str, Any]]:
    """What the boot classifies: the suite's task prompts, without their hidden tests."""
    return [{"task": t.id, "prompt": t.prompt} for t in TASKS]


def dataset_name() -> str:
    return f"{EVALUATION}-{suite_hash()}"
