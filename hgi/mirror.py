"""Mirror the ledgers to Weave as datasets, so the analyst (ARIA) can read them.

``hgi mirror`` publishes one ``weave.Dataset`` per ledger — dispositions,
sessions with their facts, observations, steers, the competence table — and
prints each ref URI. ARIA reads runs, metrics and traces at scale and drafts
the consolidation brief from them; it nominates, never verdicts, and its
report URI is recorded on the consolidation record with
``hgi consolidate --analyst-report <uri>``.
"""

from __future__ import annotations

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


def register(add, store_of, finish) -> None:
    p = add("mirror", "publish the ledgers to Weave as datasets for the analyst")
    p.set_defaults(fn=lambda args: (mirror(store_of(args)) and 0) or 0)
