"""The steer channel: feedback attached to calls in the trace store.

A human note on any call carrying the session's ``hgi.session`` attribute
becomes a steer with ``source.kind = human`` at close, before the context
that understood it is destroyed. A note left on an earlier session's call
after that session closed is captured by the next close's sweep over every
earlier closed attached session, filed once — a call URI no existing steer's
``source.anchor`` carries — and stamped with the session it belongs to. An
oracle-attributed steer — a regression whose credit assignment the
adjudicator performed — is written by the backward pass
(:mod:`hgi.consolidate`), never by the pass that produced it. The channel is
best-effort: an unavailable trace store is reported, never fatal.
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
    """The credit assignment a human steer performs: the artifact its note names, and the slot its words indict.

    A steer decides which artifact absorbs the lesson (doctrine § 7.1). The artifact is a store record — resolved by
    :meth:`hgi.store.Store.find` — or a registered lens, which lives in the register rather than as a record kind and so
    is resolved through ``store.registry``. Records come first: a note naming both takes the record, the way it always
    has, and only a note that names no store record but does name a registered lens is credited to the lens. A note
    naming neither is a correction with its credit unassigned, and the backward pass reads it without an indictment.
    """
    named = re.findall(r"\b[A-Z]-\d{4,}\b", note)
    ids = [rid for rid in named if store.find(rid) is not None]
    if not ids:
        lens_ids = {l.id for l in store.registry.lenses(status=None)}
        ids = [rid for rid in named if rid in lens_ids]
    if not ids:
        return None
    lower = note.lower()
    slot = next((slot for slot, words in SLOT_WORDS.items() if any(w in lower for w in words)), "payload")
    return {"record": ids[0], "slot": slot, "signature": "human-corrected"}


def file_note(store: Store, session: Session, note: dict[str, Any], filed_by: Session) -> Steer:
    """One note on one of ``session``'s calls as a steer: its credit assignment, its matrix cell (a fire on the indicted record seen
    by that session is a redundant catch), the session it belongs to, and the id on the closing session that filed it."""
    indicts = indictment(store, note["note"])
    fired = indicts is not None and any(store.read("fire", f).latch.record == indicts["record"] for f in session.fires_seen if store.exists("fire", f))  # type: ignore[attr-defined]
    steer = Steer(id=store.mint("steer"), at=now(), source={"kind": "human", "anchor": note["call"]}, session=session.id, correction=note["note"], indicts=indicts,
                  matrix_cell="system-catches/human-catches" if fired else "system-misses/human-catches")
    store.append(steer)
    filed_by.steers_filed.append(steer.id)
    return steer


def capture(store: Store, session: Session) -> list[Steer]:
    """Every note on the closing session's calls, then the late sweep: every earlier closed attached session's calls, filing each
    note whose call URI no existing steer already carries. A note is one steer however many closes see it."""
    steers = [file_note(store, session, n, session) for n in notes_for(session)]
    return steers + sweep(store, session)


def sweep(store: Store, closing: Session) -> list[Steer]:
    """The late sweep: notes left on earlier closed attached sessions after their close, captured now and stamped with their session."""
    carried = {t.source.anchor for t in store.all("steer") if t.source.anchor}  # type: ignore[attr-defined]
    steers = []
    earlier = sorted((s for s in store.all("session") if s.attached and s.closed_at is not None and s.id != closing.id and s.pass_ < closing.pass_), key=lambda s: s.pass_)  # type: ignore[attr-defined]
    for s in earlier:
        for n in notes_for(s):
            if n["call"] in carried:
                continue
            carried.add(n["call"])
            steers.append(file_note(store, s, n, closing))
    return steers
