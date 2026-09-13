"""The task suite as an object: tasks composed from families under one fault profile, pinned by hash.

A :class:`Task` states its presentation (the work-shape terms a boot may
classify it under), its prompt, its budgets, its output schema, the world it
runs in (files in the working directory, routes on the mock API), a hidden
check over the agent's result, and — for the deterministic harness — an
optional scripted policy. A :class:`Suite` is the tasks a :class:`SuiteSpec`
composes: which families, how many tasks of each (a seeded sample), and the
:class:`suite.faults.FaultProfile` every tool call runs under.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import random
import tomllib
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

from pydantic import BaseModel, ConfigDict, Field

from suite import EVALUATION
from suite.faults import FaultProfile

if TYPE_CHECKING:
    from suite.agent import Script

Check = Callable[[Any, Path], bool]
"""The hidden test: the agent's ``result`` and its working directory after the task."""

Scripted = Callable[["Script"], Any]
"""A scripted policy for the deterministic stub: reads the same records the model would, applies them by keyword."""


@dataclass(frozen=True)
class Task:
    id: str
    """``<family>/<name>``; unique across the suite."""
    prompt: str
    shapes: tuple[str, ...]
    """The presentation, in registry work-shape terms — what a boot classifies, never what a hook reads."""
    schema: dict[str, Any]
    check: Check
    shell_budget: int | None = None
    http_budget: int | None = None
    files: dict[str, str] = field(default_factory=dict)
    """The working directory's text files at task start."""
    blobs: dict[str, str] = field(default_factory=dict)
    """The working directory's binary files at task start, base64-encoded — for an asset no text can carry (a SQLite
    database). Hashed by the digest of their bytes, not the bytes, so the composition guard stays small and stable."""
    routes: dict[str, Any] = field(default_factory=dict)
    """The mock API: path → JSON body, or ``{"$error": {"message", "cause"}}`` for a route that answers with an error."""
    stub: Scripted | None = None
    lesson: str | None = None
    """The lesson of the world the task turns on (:data:`suite.lessons.LESSONS`), when it turns on one; not part of the presentation or the hash."""
    knowing: dict[str, int] | None = None
    """The calls per budgeted tool a policy that knows the world needs — the floor the economy scorers grade against; ``None`` leaves them unevaluable."""
    twin: "Task | None" = None
    """A metamorphic twin: the same names, columns and routes over different data, with its own gold — the world a solution's
    method is replayed in by the ``method_transfer`` scorer. Never in a suite of its own."""

    @property
    def family(self) -> str:
        return self.id.split("/", 1)[0]

    @property
    def http(self) -> bool:
        return bool(self.routes)

    def row(self) -> dict[str, Any]:
        """What the oracle's dataset holds and the agent is shown: the presentation, never the hidden test."""
        return {"task": self.id, "prompt": self.prompt, "schema": self.schema, "shell_budget": self.shell_budget,
                "http_budget": self.http_budget, "http": self.http}

    def world(self) -> dict[str, Any]:
        """The part of the task the agent reaches only through tools; hashed with the presentation.

        A binary blob is hashed by the digest of its bytes rather than the bytes themselves, so a megabyte-scale
        asset guards the composition without bloating the hash payload. The ``blobs`` key is present only when the
        task carries one, so a task with none hashes exactly as it did before binary assets existed.
        """
        world = {"files": self.files, "routes": self.routes}
        if self.blobs:
            world["blobs"] = {name: hashlib.sha256(base64.b64decode(b)).hexdigest() for name, b in self.blobs.items()}
        return world

    def setup(self, workdir: Path) -> None:
        workdir.mkdir(parents=True, exist_ok=True)
        for name, content in self.files.items():
            (workdir / name).write_text(content)
        for name, b in self.blobs.items():
            (workdir / name).write_bytes(base64.b64decode(b))


class SuiteSpec(BaseModel):
    """What composes a suite; the experiment file's ``[suite]`` table, or ``$HGI_SUITE`` for a hand-run."""

    families: list[str] = Field(default_factory=lambda: ["genesis"])
    size: int | None = Field(default=None, ge=1)
    """Tasks taken from each family — a sample seeded by ``seed`` — or every task when absent."""
    seed: int = 0
    faults: FaultProfile = Field(default_factory=FaultProfile)

    model_config = ConfigDict(extra="forbid")


@dataclass
class Suite:
    spec: SuiteSpec
    tasks: list[Task]

    @cached_property
    def by_id(self) -> dict[str, Task]:
        return {t.id: t for t in self.tasks}

    @property
    def faults(self) -> FaultProfile:
        return self.spec.faults

    @property
    def name(self) -> str:
        return "+".join(self.spec.families)

    @cached_property
    def hash(self) -> str:
        """The composition guard: a digest of every task's presentation and world, and the fault profile."""
        payload = json.dumps({"tasks": [{**t.row(), "world": t.world()} for t in self.tasks], "faults": self.spec.faults.model_dump()}, sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()[:12]

    def rows(self) -> list[dict[str, Any]]:
        return [t.row() for t in self.tasks]

    def presentations(self) -> list[dict[str, Any]]:
        """What the boot classifies: the task prompts, without their hidden tests."""
        return [{"task": t.id, "prompt": t.prompt} for t in self.tasks]

    def dataset_name(self) -> str:
        return f"{EVALUATION}-{self.hash}"

    def families(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for t in self.tasks:
            out[t.family] = out.get(t.family, 0) + 1
        return out

    def describe(self) -> str:
        return f"suite {self.name} ({self.hash}): {len(self.tasks)} tasks " + ", ".join(f"{f}={n}" for f, n in self.families().items()) + \
               f"; faults {json.dumps(self.spec.faults.model_dump(), sort_keys=True)}"


def build(spec: SuiteSpec) -> Suite:
    """Compose the suite the spec names: each family's tasks, sampled to ``size`` by the seed, in id order."""
    from suite.families import FAMILIES

    tasks: list[Task] = []
    for name in spec.families:
        if name not in FAMILIES:
            raise SystemExit(f"no task family {name!r}; families are {sorted(FAMILIES)}")
        family = sorted(FAMILIES[name].tasks(), key=lambda t: t.id)
        if not family:
            raise SystemExit(f"task family {name!r} holds no tasks; " + (FAMILIES[name].how_to_fetch or "it is empty"))
        if spec.size is not None and len(family) > spec.size:
            family = sorted(random.Random(f"{spec.seed}:{name}").sample(family, spec.size), key=lambda t: t.id)
        tasks += family
    ids = [t.id for t in tasks]
    if len(set(ids)) != len(ids):
        raise SystemExit(f"duplicate task ids across families: {sorted({i for i in ids if ids.count(i) > 1})}")
    return Suite(spec=spec, tasks=tasks)


def load_spec(path: Path | str) -> SuiteSpec:
    """A suite spec from a TOML file: its ``[suite]`` table, or the whole document when there is none."""
    with Path(path).open("rb") as f:
        raw = tomllib.load(f)
    return SuiteSpec(**raw.get("suite", raw))


def from_env() -> Suite:
    """The suite ``$HGI_SUITE`` names (a TOML file), else the genesis family under the default profile."""
    path = os.environ.get("HGI_SUITE")
    return build(load_spec(path) if path else SuiteSpec())
