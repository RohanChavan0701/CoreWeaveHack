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
from hgi import roles

_typesafe: _model.Backend | None = None


def _backend() -> _model.Backend | None:
    global _typesafe
    if _typesafe is None and os.environ.get("TYPESAFE_BASE_URL") and os.environ.get("TYPESAFE_MODEL_ID"):
        _typesafe = _model.OpenAICompatible(os.environ["TYPESAFE_BASE_URL"], os.environ.get("TYPESAFE_API_KEY", "none"), os.environ["TYPESAFE_MODEL_ID"])
    return _typesafe


def _ask(name: str, *, session: str | None = None, pass_: int | None = None, **content: Any) -> _model.Completion:
    payload = roles.request(name, **content)
    vendor = _backend()
    if vendor is None:
        return _model.complete("coder", payload, session=session, pass_=pass_)
    with _model.override("coder", vendor):
        return _model.complete("coder", payload, session=session, pass_=pass_)


def guard(work_shape: dict[str, Any], hook: dict[str, Any], presentations: list[dict[str, Any]], **trace) -> tuple[bool, str, str | None]:
    """Whether ``hook`` fires for ``work_shape`` — the guard result, its reason, and the call URI."""
    c = _ask("guard", work_shape=work_shape, hook=hook, presentations=presentations, **trace)
    out = c.json()
    return bool(out.get("passed")), str(out.get("why", "")), c.call


def coding_observations(observations: list[dict[str, Any]], rows: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """Each observation enriched with its anchored row's ``result`` and ``commands`` — the query text and output where the
    wrong literal actually appears — so the blind coder reads the world the attempt produced, not only the noticing prose
    (carry-forward item 49b). ``rows`` maps a trace call URI to its evaluation row; the anchor is dropped from the payload
    (it is the resolution key, never the coder's evidence)."""
    out = []
    for o in observations:
        anchor = o.get("anchor") if isinstance(o.get("anchor"), dict) else {}
        row = (rows.get(anchor.get("call")) if anchor else None) or {}
        out.append({k: v for k, v in o.items() if k != "anchor"} | {"result": row.get("result"), "commands": row.get("commands") or []})
    return out


def code(observations: list[dict[str, Any]], terms: list[str], *, rows: dict[str, dict[str, Any]] | None = None, **trace) -> tuple[dict[str, list[str]], str | None]:
    """Blind coding: ``{observation name: [terms]}``. The coverage question is put to the anchored row's ``result`` and
    ``commands`` (the query text) as well as the noticing prose when ``rows`` is given (:func:`coding_observations`) — the
    wrong literal lives in the query, not always in the prose; without ``rows`` the noticing text stands alone."""
    payload = coding_observations(observations, rows) if rows is not None else observations
    c = _ask("coding", observations=payload, terms=terms, **trace)
    out = c.json()
    return {k: list(v) for k, v in out.items()}, c.call
