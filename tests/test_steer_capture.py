"""The steer performs credit assignment (doctrine § 7.1): a human note naming a record indicts it, the slot read off the
note's words; a note naming nothing is a correction with its credit unassigned."""

from __future__ import annotations

from hgi import steers as _steers
from hgi.store import now
from hgi.types import Session
from tests.conftest import adjudicated_entry, adjudicator, draft


def _admit(store):
    d = draft(store)
    entry = adjudicated_entry(store, d.uid)
    entry.verdict = "admit"
    return store.admit(d, entry, adjudicator())


def test_a_note_naming_a_record_indicts_it_and_its_slot(store):
    d = _admit(store)
    assert _steers.indictment(store, f"{d.id} fired on every http task; its hook is too broad") == {"record": d.id, "slot": "activation", "signature": "human-corrected"}
    assert _steers.indictment(store, f"the retry in {d.id} is wrong: one retry is not enough") == {"record": d.id, "slot": "payload", "signature": "human-corrected"}
    assert _steers.indictment(store, "D-9999 is wrong") is None and _steers.indictment(store, "looks fine") is None


def test_capture_writes_the_indictment_and_the_matrix_cell(store, monkeypatch):
    d = _admit(store)
    s = Session(id="S-0001", pass_=1, started_at=now())
    monkeypatch.setattr(_steers, "notes_for", lambda session: [{"call": "weave:///t/call/1", "note": f"{d.id} premise p1 no longer holds"},
                                                              {"call": "weave:///t/call/2", "note": "the task list is stale"}])
    [a, b] = _steers.capture(store, s)
    assert a.indicts.record == d.id and a.indicts.slot == "warrant" and a.matrix_cell == "system-misses/human-catches" and a.source.kind == "human"
    assert b.indicts is None and s.steers_filed == [a.id, b.id]
