"""The stream: a pool of tasks dealt into batches the loop meets one pass at a time.

A stream experiment does not run the same suite every pass. Its pool — the
tasks of the families it names — is dealt into ``batches`` batches of
``batch`` tasks, balanced over the lessons the tasks carry (a task with no
lesson is dealt under its family's name), and pass *k* evaluates batch *k*
at first sight: nothing in the store was learned on those tasks, so the
pass's score is a validation score, and the close that follows makes the
batch training. That is the prequential shape — every batch is a test set
once and a training set afterwards — and the curve it draws is first-sight
performance on unseen tasks as the store grows. An arm with no store meets
the same batches in the same order, so the comparison is paired per batch.
``revisit`` names batches the attached arm meets again after the stream,
which measures retention on tasks it has seen rather than transfer to ones
it has not.

The deal is seeded: two arms of one experiment, and a report reading an
arm back, deal the same batches from the same pool.
"""

from __future__ import annotations

import random
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from suite.faults import FaultProfile
from suite.tasks import Suite, SuiteSpec, Task, build


class StreamSpec(BaseModel):
    """The experiment file's ``[stream]`` table."""

    families: list[str] = Field(default_factory=lambda: ["curriculum"])
    batch: int = Field(default=8, ge=1)
    """Tasks a pass meets."""
    batches: int = Field(default=10, ge=1)
    """Passes in the stream; each meets a batch nothing before it has seen."""
    seed: int = 0
    faults: FaultProfile = Field(default_factory=lambda: FaultProfile(http_fault_fraction=0.0))
    """The world's fault profile; the default faults nothing, so the lessons are the conventions alone."""
    revisit: list[int] = Field(default_factory=list)
    """Batch numbers the attached arm meets again after the stream, in this order; each a pass with no consolidation after it."""

    model_config = ConfigDict(extra="forbid")

    @property
    def pool_spec(self) -> SuiteSpec:
        return SuiteSpec(families=self.families, faults=self.faults, seed=self.seed)


def key_of(task: Task) -> str:
    """What a task is balanced under: its lesson, else its family."""
    return task.lesson or task.family


def partition(spec: StreamSpec) -> list[Suite]:
    """Deal the pool into ``spec.batches`` suites of ``spec.batch`` tasks, balanced over lessons, by the seed."""
    pool = build(spec.pool_spec).tasks
    need = spec.batch * spec.batches
    if len(pool) < need:
        raise SystemExit(f"stream needs {need} tasks ({spec.batches} batches of {spec.batch}); the pool {'+'.join(spec.families)} holds {len(pool)}")
    for r in spec.revisit:
        if not 1 <= r <= spec.batches:
            raise SystemExit(f"stream revisits batch {r}, which is not in 1..{spec.batches}")
    groups: dict[str, list[Task]] = {}
    for t in pool:
        groups.setdefault(key_of(t), []).append(t)
    keys = sorted(groups)
    random.Random(f"{spec.seed}:keys").shuffle(keys)
    queues = {k: sorted(groups[k], key=lambda t: t.id) for k in keys}
    for k in keys:
        random.Random(f"{spec.seed}:{k}").shuffle(queues[k])
    dealt: list[Task] = []
    while len(dealt) < need:  # round-robin over the keys, so every batch holds each lesson about equally
        progressed = False
        for k in keys:
            if queues[k]:
                dealt.append(queues[k].pop())
                progressed = True
                if len(dealt) == need:
                    break
        if not progressed:
            break
    return [Suite(spec=spec.pool_spec, tasks=sorted(dealt[i * spec.batch:(i + 1) * spec.batch], key=lambda t: t.id)) for i in range(spec.batches)]


def lessons_of(suite: Suite) -> dict[str, int]:
    out: dict[str, int] = {}
    for t in suite.tasks:
        out[key_of(t)] = out.get(key_of(t), 0) + 1
    return out


def describe(spec: StreamSpec, batches: list[Suite]) -> str:
    keys = sorted({key_of(t) for b in batches for t in b.tasks})
    return (f"stream {'+'.join(spec.families)}: {spec.batches} batches × {spec.batch} tasks over {len(keys)} lessons ({', '.join(keys)}), seed {spec.seed}"
            + (f"; revisit {spec.revisit}" if spec.revisit else "") + f"; faults {spec.faults.model_dump_json()}")


def batch_record(n: int, suite: Suite) -> dict[str, Any]:
    """What ``arm.json`` records of a batch: its number, hash, tasks and lesson counts."""
    return {"batch": n, "hash": suite.hash, "tasks": [t.id for t in suite.tasks], "lessons": lessons_of(suite)}
