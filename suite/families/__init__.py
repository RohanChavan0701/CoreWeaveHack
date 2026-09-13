"""Task families: each a source of :class:`suite.tasks.Task` under one name.

A family is hand-written (``genesis``, ``conventions``) or transcribed from
a public dataset into a pinned file under ``suite/data/`` (``mbpp``, …). A
transcribed family declares ``fetch``, the transcriber from the dataset's
rows to the pinned records, which ``hgi suite fetch <family>`` runs once;
its ``tasks`` then reads the pinned file, so a run needs no network and the
suite hash is stable. A family may also be *derived* — no ``fetch`` of its
own, its ``tasks`` reading another family's pinned records and presenting
them differently (``api`` over ``tables``). The registry is
:data:`FAMILIES`; a family registers itself by importing here.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from suite.tasks import Task

DATA = Path(__file__).resolve().parents[1] / "data"


@dataclass(frozen=True)
class Family:
    name: str
    tasks: Callable[[], list[Task]]
    source: str
    """Where the tasks come from, for the reader."""
    fetch: Callable[[int], list[dict[str, Any]]] | None = None
    """The transcriber: dataset rows → pinned records, at most ``n``; ``None`` for a hand-written family."""

    @property
    def data_path(self) -> Path:
        return DATA / f"{self.name}.jsonl"

    @property
    def how_to_fetch(self) -> str | None:
        return f"run `hgi suite fetch {self.name}` to transcribe it into {self.data_path.relative_to(DATA.parents[1])}" if self.fetch else None

    def records(self) -> list[dict[str, Any]]:
        """The pinned records, in file order; empty when the family has not been fetched."""
        if not self.data_path.exists():
            return []
        return [json.loads(line) for line in self.data_path.read_text().splitlines() if line.strip()]

    def pin(self, records: list[dict[str, Any]]) -> Path:
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        self.data_path.write_text("".join(json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n" for r in records))
        return self.data_path


FAMILIES: dict[str, Family] = {}


def family(name: str, source: str, fetch: Callable[[int], list[dict[str, Any]]] | None = None):
    """Register the decorated ``tasks`` loader as family ``name``."""

    def deco(tasks: Callable[[], list[Task]]):
        FAMILIES[name] = Family(name=name, tasks=tasks, source=source, fetch=fetch)
        return tasks

    return deco


from suite.families import api, conventions, curriculum, genesis, mbpp, reasoning_core, tables, transfer  # noqa: E402,F401 — registration
