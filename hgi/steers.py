"""The steer channel: feedback attached to calls in the trace store.

A human note on any call carrying the session's ``hgi.session`` attribute
becomes a steer with ``source.kind = human`` at close, before the context
that understood it is destroyed. An oracle-attributed steer — a regression
whose credit assignment the adjudicator performed — is written by the
backward pass (:mod:`hgi.consolidate`), never by the pass that produced it.
"""

from __future__ import annotations

import re
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


SLOT_WORDS = {"activation": ("hook", "fire", "fired", "activation", "recall", "not_this", "not-this"), "warrant": ("premise", "warrant", "anchor", "falsif"),
              "enforcement": ("floor", "lint", "residue", "enforcement"), "lifecycle": ("retire", "moot", "lifecycle", "consumer")}
"""What a human's note says about which slot it indicts; the payload is the slot a correction lands on when it names none."""


def indictment(store: Store, note: str) -> dict[str, str] | None:
    """The credit assignment a human steer performs: the record its note names, and the slot its words indict.

    A steer decides which artifact absorbs the lesson (doctrine § 7.1); a note naming no record in the store is a
    correction with its credit unassigned, and the backward pass reads it without an indictment.
    """
    ids = [rid for rid in re.findall(r"\b[A-Z]-\d{4,}\b", note) if store.find(rid) is not None]
    if not ids:
        return None
    lower = note.lower()
    slot = next((slot for slot, words in SLOT_WORDS.items() if any(w in lower for w in words)), "payload")
    return {"record": ids[0], "slot": slot, "signature": "human-corrected"}


def capture(store: Store, session: Session) -> list[Steer]:
    steers = []
    for n in notes_for(session):
        indicts = indictment(store, n["note"])
        fired = indicts is not None and any(store.read("fire", f).latch.record == indicts["record"] for f in session.fires_seen if store.exists("fire", f))  # type: ignore[attr-defined]
        steer = Steer(id=store.mint("steer"), at=now(), source={"kind": "human", "anchor": n["call"]}, correction=n["note"], indicts=indicts,
                      matrix_cell="system-catches/human-catches" if fired else "system-misses/human-catches")
        store.append(steer)
        steers.append(steer)
        session.steers_filed.append(steer.id)
    return steers
