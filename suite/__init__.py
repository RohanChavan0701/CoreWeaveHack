"""The task suite: the world the loop is judged on.

A tool-using agent runs over a fixed suite of small tasks, each graded by a
hidden check, through a tool layer with injected faults: an HTTP tool that
returns a transient 5xx on a fixed fraction of tasks, a shell tool with a
call budget, and a file tool. The faults and the world's conventions exist
so that lessons are learnable across passes and the oracle can score
whether they were learned.

A suite is composed from *families* (:mod:`suite.families`): the hand-written
genesis tasks, the world-convention tasks, and families transcribed from
public datasets into ``suite/data/``. Which families, how many tasks of
each, and which fault profile, is a :class:`suite.tasks.SuiteSpec` — carried
by the experiment file, or by ``$HGI_SUITE`` for a hand-run — and the
composition guard is the suite hash over every task's presentation and the
profile. The suite in scope is :func:`current`; an experiment installs its
own with :func:`use`, the way a store installs its registry.
"""

from __future__ import annotations

from contextvars import ContextVar
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from suite.tasks import Suite

EVALUATION = "suite-v1"

_current: ContextVar["Suite | None"] = ContextVar("hgi_suite", default=None)


def current() -> "Suite":
    """The suite in scope: the one installed by :func:`use`, else the one the environment names."""
    s = _current.get()
    if s is None:
        from suite.tasks import from_env

        s = from_env()
        _current.set(s)
    return s


def use(s: "Suite | None"):
    """Make ``s`` the suite in scope (a token to reset with :func:`reset`)."""
    return _current.set(s)


def reset(token) -> None:
    _current.reset(token)
