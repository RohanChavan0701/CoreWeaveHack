"""§ 9.5 — the machine-native answerer: the blind second coder and the guard evaluator.

Two roles that want a deterministic, non-narrative answer, kept out of the
context that would otherwise decide for itself:

- ``code`` classifies raw anchored observations against the registry's
  work-shape terms *without seeing* the consolidator's candidate labels;
- ``guard`` returns a hook's guard result for a work-shape classification,
  so the context that will apply the payload does not decide whether it fires.

The vendor is a coordinate: TypeSafe AI's System1 is used when
``$TYPESAFE_BASE_URL``, ``$TYPESAFE_API_KEY`` and ``$TYPESAFE_MODEL_ID`` are
set (an OpenAI-compatible surface is assumed); otherwise the fallback is a
second, separately prompted frozen-model context with the labels withheld —
the ``coder`` role of :mod:`hgi.model`.
"""

from __future__ import annotations

import json
import os
from typing import Any

from hgi import model as _model

_typesafe: _model.Backend | None = None


def _backend() -> _model.Backend | None:
    global _typesafe
    if _typesafe is None and os.environ.get("TYPESAFE_BASE_URL") and os.environ.get("TYPESAFE_MODEL_ID"):
        _typesafe = _model.OpenAICompatible(os.environ["TYPESAFE_BASE_URL"], os.environ.get("TYPESAFE_API_KEY", "none"), os.environ["TYPESAFE_MODEL_ID"])
    return _typesafe


def _ask(request: dict[str, Any], **trace) -> _model.Completion:
    vendor = _backend()
    if vendor is None:
        return _model.complete("coder", json.dumps(request), **trace)
    previous = _model.backend()
    _model.use(vendor)
    try:
        return _model.complete("coder", json.dumps(request), **trace)
    finally:
        _model.use(previous)


def guard(work_shape: dict[str, Any], hook: dict[str, Any], presentations: list[dict[str, Any]], **trace) -> tuple[bool, str, str | None]:
    """Whether ``hook`` fires for ``work_shape`` — the guard result, its reason, and the call URI."""
    c = _ask({"request": "guard", "work_shape": work_shape, "hook": hook, "presentations": presentations}, **trace)
    out = c.json()
    return bool(out.get("passed")), str(out.get("why", "")), c.call


def code(observations: list[dict[str, Any]], terms: list[str], **trace) -> tuple[dict[str, list[str]], str | None]:
    """Blind coding: ``{observation name: [terms]}`` from the noticing text alone."""
    c = _ask({"request": "coding", "observations": observations, "terms": terms}, **trace)
    out = c.json()
    return {k: list(v) for k, v in out.items()}, c.call
