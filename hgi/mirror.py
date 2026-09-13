"""Mirror the ledgers to Weave as datasets, so the analyst (ARIA) can read them.

``hgi mirror`` publishes one ``weave.Dataset`` per ledger — dispositions,
sessions with their facts, observations, steers, the competence table — and
prints each ref URI. ARIA reads runs, metrics and traces at scale and drafts
the consolidation brief from them; it nominates, never verdicts, and its
report URI is recorded on the consolidation record with
``hgi consolidate --analyst-report <uri>``.

That URI is also the read side of the programmatic surface: :func:`read_report`
resolves it back to the report ARIA drafted, which the backward pass reads as
the consolidation brief's primary input (:mod:`hgi.consolidate`). A URI that
resolves to no machine-readable report — an interactive chat report recorded
only as provenance — leaves the consolidator to derive the brief itself.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import weave

from hgi import index as _index
from hgi import tracing
from hgi.store import Store, dump


def rows(store: Store) -> dict[str, list[dict[str, Any]]]:
    sessions = []
    for s in store.all("session"):
        scores = {k: f.value for k, f in (s.evaluation.scores if s.evaluation else {}).items()}  # type: ignore[attr-defined]
        sessions.append({"id": s.id, "pass": s.pass_, "attached": s.attached, "model_id": s.model_id, "trace_root": s.trace_root,  # type: ignore[attr-defined]
                         "consulted": [c.record for c in s.consulted], "work_shape": s.work_shape.terms, "escapes": s.work_shape.escapes, **scores})  # type: ignore[attr-defined]
    return {
        "sessions": sessions,
        "dispositions": [dump(u) for u in store.all("disposition")],
        "observations": [dump(o) for o in store.all("observation")],
        "steers": [dump(t) for t in store.all("steer")],
        "competence": _index.competence(store),
        "matrix": [{"cell": k, "count": len(v)} for k, v in _index.matrix(store).items() if isinstance(v, list)],
    }


def mirror(store: Store) -> dict[str, str]:
    if tracing.init() is None:
        raise SystemExit("set HGI_WEAVE_PROJECT (and WANDB_ENTITY) to mirror the ledgers to Weave")
    refs = {}
    for name, data in rows(store).items():
        if not data:
            continue
        ref = weave.publish(weave.Dataset(name=f"hgi-{name}", rows=data))
        refs[name] = ref.uri()
        print(f"{name}: {len(data)} rows → {refs[name]}")
    return refs


def read_report(uri: str | None) -> dict[str, Any] | None:
    """The analyst's report read back from its URI as the consolidation brief, or ``None`` when the URI names none.

    The programmatic surface's read side (§ 9.3): a Weave ref (``weave:///…``) is the report ARIA published over the
    runs :func:`mirror` exposed; a filesystem path or ``file://`` URI is an exported or an offline report. A URI that
    resolves to no machine-readable report — an interactive chat report recorded only as provenance, or a ref that
    cannot be fetched — is ``None``, and the consolidator derives the brief itself.
    """
    if not uri:
        return None
    report = _fetch(uri)
    return report if isinstance(report, dict) else None


def _fetch(uri: str) -> Any:
    """Resolve a report URI to whatever it holds: a Weave object, or the JSON at a filesystem path."""
    if uri.startswith("weave://"):
        try:
            return weave.ref(uri).get()
        except Exception:
            return None  # not initialized, no such ref, or no network — the consolidator falls back to its own derivation
    path = Path(uri[len("file://"):] if uri.startswith("file://") else uri)
    try:
        return json.loads(path.read_text()) if path.is_file() else None
    except (OSError, ValueError):
        return None


def register(add, store_of, finish) -> None:
    p = add("mirror", "publish the ledgers to Weave as datasets for the analyst")
    p.set_defaults(fn=lambda args: (mirror(store_of(args)) and 0) or 0)
