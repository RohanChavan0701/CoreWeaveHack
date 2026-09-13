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


def test_a_late_note_on_an_earlier_session_is_swept_at_the_next_close_once(store, monkeypatch):
    d = _admit(store)
    earlier = Session(id="S-0001", pass_=1, started_at=now(), closed_at=now())
    store.write(earlier)
    # the earlier session's own close saw one note; a second lands on its calls only after it closed
    notes = {"S-0001": [{"call": "weave:///t/call/1", "note": f"{d.id} is wrong: one retry is not enough"}], "S-0002": []}
    monkeypatch.setattr(_steers, "notes_for", lambda session: list(notes.get(session.id, [])))
    [early] = _steers.capture(store, earlier)
    assert early.session == "S-0001"
    notes["S-0001"].append({"call": "weave:///t/call/late", "note": f"{d.id} fired on every http task; its hook is too broad"})
    closing = Session(id="S-0002", pass_=2, started_at=now())
    [late] = _steers.capture(store, closing)
    assert late.session == "S-0001" and late.source.anchor == "weave:///t/call/late" and late.indicts.slot == "activation"
    assert closing.steers_filed == [late.id] and earlier.steers_filed == [early.id]
    # a later close sweeps again and files nothing: both calls already carry a steer
    third = Session(id="S-0003", pass_=3, started_at=now())
    assert _steers.capture(store, third) == [] and third.steers_filed == []
    assert [t.source.anchor for t in store.all("steer")] == ["weave:///t/call/1", "weave:///t/call/late"]


def test_an_unavailable_trace_store_is_reported_never_fatal(store, monkeypatch, capsys):
    from hgi import tracing

    class Broken:
        def get_calls(self, **kw):
            raise RuntimeError("weave is down")

    monkeypatch.setattr(tracing, "client", lambda: Broken())
    store.write(Session(id="S-0001", pass_=1, started_at=now(), closed_at=now()))
    assert _steers.capture(store, Session(id="S-0002", pass_=2, started_at=now())) == []
    assert "steer channel unavailable" in capsys.readouterr().out
