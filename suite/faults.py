"""The fault profile: what the world does to the agent, fixed per suite.

Faults are deterministic in the task so that two runs over the same suite
hash see the same world. The profile is part of the suite hash: a harder
world is a different suite, and the report keys on the arm.
"""

from __future__ import annotations

import hashlib

from pydantic import BaseModel, ConfigDict, Field


class FaultProfile(BaseModel):
    http_fault_fraction: float = Field(default=0.5, ge=0.0, le=1.0)
    """The fraction of HTTP-using tasks whose leading calls return a transient 502."""
    http_fault_calls: int = Field(default=1, ge=0)
    """How many leading HTTP calls of a faulted task fail before the route answers — one is a retry lesson, two is a persistence lesson."""
    http_budget: int | None = Field(default=None, ge=1)
    """A call budget on the HTTP tool for every task that names none of its own; ``None`` is unbudgeted."""
    shell_output_limit: int | None = Field(default=None, ge=1)
    """Bytes of shell output returned before truncation, marked ``[truncated]``; ``None`` returns everything."""

    model_config = ConfigDict(extra="forbid")

    def faulted(self, task: str) -> bool:
        """Whether ``task``'s leading HTTP calls fail: a fixed digest of the task's name within its family, so the same
        task faults in every pass and a family keeps its faults whatever it is composed with."""
        h = int(hashlib.sha256(task.rsplit("/", 1)[-1].encode()).hexdigest(), 16)
        return (h % 100) < self.http_fault_fraction * 100
