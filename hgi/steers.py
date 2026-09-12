"""The steer channel: feedback attached to calls in the trace store.

A human note on any call carrying the session's ``hgi.session`` attribute
becomes a steer with ``source.kind = human`` at close, before the context
that understood it is destroyed. An oracle-attributed steer — a regression
whose credit assignment the adjudicator performed — is written by the
backward pass (:mod:`hgi.consolidate`), never by the pass that produced it.
"""

from __future__ import annotations

from typing import Any

from hgi import tracing
from hgi.store import Store, now
from hgi.types import Session, Steer


def notes_for(session: Session) -> list[dict[str, Any]]:
    """Every feedback note on a call of this session, as ``{call, note}``; empty when untraced."""
    client = tracing.client()
    if client is None:
        return []
    try:
        calls = list(client.get_calls(
            query={"$expr": {"$eq": [{"$getField": "attributes.hgi.session"}, {"$literal": session.id}]}},
            include_feedback=True,
        ))
        if not calls:  # the attribute index can lag the write; fall back to every call in the session's traces
            roots = [tracing.call_id(u) for u in [session.trace_root, *(a.call for a in session.lens_answers)] if u]
            trace_ids = {client.get_call(r).trace_id for r in roots}
            calls = list(client.get_calls(filter={"trace_ids": sorted(trace_ids)}, include_feedback=True)) if trace_ids else []
        out = []
        for call in calls:
            for fb in ((call.summary or {}).get("weave", {}).get("feedback") or []):
                note = (fb.get("payload") or {}).get("note")
                if fb.get("feedback_type") == "wandb.note.1" and note:
                    out.append({"call": tracing.call_uri(call), "note": note})
        return out
    except Exception as e:  # the steer channel is best-effort at close; a failed read is reported, not fatal
        print(f"steer channel unavailable: {e}")
        return []


def capture(store: Store, session: Session) -> list[Steer]:
    steers = []
    for n in notes_for(session):
        steer = Steer(id=store.mint("steer"), at=now(), source={"kind": "human", "anchor": n["call"]}, correction=n["note"],
                      matrix_cell="system-misses/human-catches")
        store.append(steer)
        steers.append(steer)
        session.steers_filed.append(steer.id)
    return steers
