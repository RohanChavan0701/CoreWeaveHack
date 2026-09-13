"""The trace store binding: W&B Weave.

``init`` opens the project named by ``$HGI_WEAVE_PROJECT`` (under
``$WANDB_ENTITY`` when set) and returns the client, or ``None`` when no
project is configured — every ``@weave.op`` then runs untraced and every call
URI reads ``None``. ``attributes`` puts ``hgi.session``, ``hgi.pass``,
``hgi.role`` and ``hgi.records_in_context`` on every call made inside it (as a
nested ``hgi`` attribute, so the trace store can be queried by
``attributes.hgi.session``), so any trace call can be joined back to what the
pass was conditioned on. ``run`` names the experiment and arm the process is
executing; both ride on every call as ``hgi.experiment`` and ``hgi.arm`` and
prefix every evaluation's display name, so arms of one experiment are told
apart inside one project.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any, Iterator

import weave

_client = None
_initialised = False
_run: dict[str, Any] = {}


def project_name() -> str | None:
    project = os.environ.get("HGI_WEAVE_PROJECT")
    if not project:
        return None
    entity = os.environ.get("WANDB_ENTITY")
    return f"{entity}/{project}" if entity and "/" not in project else project


def init():
    """Open the Weave project once per process; ``None`` when tracing is off."""
    global _client, _initialised
    if _initialised:
        return _client
    _initialised = True
    name = project_name()
    if name:
        _client = weave.init(name)
    return _client


def client():
    return _client if _initialised else init()


def enabled() -> bool:
    return client() is not None


def run(experiment: str | None = None, arm: str | None = None) -> None:
    """Name the experiment and arm every call from now on belongs to; ``run()`` clears it."""
    _run.clear()
    _run.update({k: v for k, v in {"experiment": experiment, "arm": arm}.items() if v is not None})


def run_label() -> str:
    """``experiment/arm `` for display names, empty outside an experiment."""
    return "/".join(v for v in (_run.get("experiment"), _run.get("arm")) if v) + " " if _run else ""


@contextmanager
def attributes(session: str | None = None, pass_: int | None = None, role: str | None = None,
               records_in_context: list[str] | None = None, **extra: Any) -> Iterator[None]:
    hgi: dict[str, Any] = {k: v for k, v in {
        **_run, "session": session, "pass": pass_, "role": role, "records_in_context": records_in_context, **extra,
    }.items() if v is not None}
    with weave.attributes({"hgi": hgi}):
        yield


def current_call_uri() -> str | None:
    """The URI of the call currently executing, or ``None`` untraced."""
    call = weave.get_current_call()
    if call is None:
        return None
    try:
        return call.ref.uri()
    except Exception:
        return None


def call_uri(call: Any) -> str | None:
    try:
        return call.ref.uri()
    except Exception:
        return None


def call_id(uri: str | None) -> str | None:
    """``weave:///entity/project/call/<id>`` → ``<id>``."""
    return uri.rsplit("/", 1)[1] if uri and "/call/" in uri else None
