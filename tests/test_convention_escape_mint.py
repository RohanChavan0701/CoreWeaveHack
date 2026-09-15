"""Carry-forward item 57 part 3 — the escape→mint lifecycle feeding the open ``convention`` axis.

The grouping axis is open and instance-grown: a recurring ``other(<what>)`` the backward pass's grouping stamps on
observations across independent sessions nominates ``<what>`` as a registered ``convention`` term through the same
owner-gated ladder the ``work-shape`` escapes climb (:func:`hgi.reviews.escape_events`, :func:`hgi.reviews.vocabulary`).
The machine nominates; the blind coder contradicts and the adjudicator verdicts — nothing auto-admits.
"""

from __future__ import annotations

from hgi import reviews as _reviews
from hgi import stub
from hgi.store import now
from hgi.types import Consolidation, Observation, Session


def _record(store) -> Consolidation:
    return Consolidation(id=store.mint("consolidation"), started_at=now(), after_pass=2, sessions_read=[])


def _session(store, pass_: int) -> Session:
    s = Session(id=store.mint("session"), pass_=pass_, started_at=now(), closed_at=now(), attached=True)
    store.write(s)
    return s


def _observe(store, session: Session, shape: list[str], happened: str, state: str = "open") -> Observation:
    o = Observation(uid=store.new_uid(), name=store.next_name("O"), noticed_at=now(), session=session.id,
                    happened=happened, anchor={"call": f"weave:///c/{session.id}"}, shape=shape)
    if state != "open":
        o.disposition.state = state
    store.write(o)
    return o


# --- the convention axis is a reviewable, escape-carrying vocabulary --------------------------

def test_the_convention_axis_is_reviewable(store):
    assert "convention" in _reviews.reviewable_vocabularies(store)


def test_convention_escapes_cluster_across_independent_sessions(store):
    s1, s2 = _session(store, 1), _session(store, 2)
    _observe(store, s1, ["other(paging cursor)"], "task t failed reading a cursor-paged listing")
    _observe(store, s2, ["other(Paging-Cursor)"], "task u failed reading a cursor-paged listing")
    (cluster,) = _reviews.escape_clusters(store, "convention")
    assert cluster["vocabulary"] == "convention" and cluster["term"] == "paging-cursor"
    assert cluster["sessions"] == [s1.id, s2.id]
    assert _reviews.escape_clusters(store, "work-shape") == [], "a convention escape is not a work-shape escape"


def test_two_convention_escapes_in_one_session_are_one_datum(store):
    s1 = _session(store, 1)
    _observe(store, s1, ["other(paging-cursor)"], "task t failed on a cursor")
    _observe(store, s1, ["other(paging-cursor)"], "task u failed on a cursor")
    assert [c["sessions"] for c in _reviews.escape_clusters(store, "convention")] == [[s1.id]], "one pass is one datum"


def test_a_registered_convention_shape_does_not_escape(store):
    s1, s2 = _session(store, 1), _session(store, 2)
    _observe(store, s1, ["listing-paged"], "task t returned one page at a time")
    _observe(store, s2, ["listing-paged"], "task u returned one page at a time")
    assert _reviews.escape_clusters(store, "convention") == [], "a shape already a registered term is no escape"


def test_a_consumed_or_dismissed_observation_is_not_recounted(store):
    s1, s2 = _session(store, 1), _session(store, 2)
    _observe(store, s1, ["other(paging-cursor)"], "task t failed on a cursor", state="promoted")
    _observe(store, s2, ["other(paging-cursor)"], "task u failed on a cursor", state="dismissed")
    assert _reviews.escape_clusters(store, "convention") == [], "an observation out of the open pool no longer nominates"


# --- the recurrence grows the axis, owner-gated ----------------------------------------------

def test_a_recurring_convention_escape_grows_the_convention_vocabulary(store, monkeypatch):
    s1, s2 = _session(store, 1), _session(store, 2)
    _observe(store, s1, ["other(paging cursor)"], "task t failed reading a cursor-paged listing")
    _observe(store, s2, ["other(paging cursor)"], "task u failed reading a cursor-paged listing")
    # the blind coder re-reads the presentations with the candidate withheld and still escapes: no registered term covers it
    monkeypatch.setitem(stub.HANDLERS, "coding", lambda req: {name: ["other(a cursor-keyed page walk the axis lacks)"] for name in (o["name"] for o in req["observations"])})
    record = _record(store)
    noms = _reviews.vocabulary(store, record, "convention")
    n = next(n for n in noms if n.subject == "convention/paging-cursor")
    assert n.outcome == "minted convention/paging-cursor" and record.minted == ["convention/paging-cursor"]
    assert "paging-cursor" in store.registry.terms("convention")
    entry = next(e for e in store.all("hypothesis") if e.id == n.ledger_entry)
    assert entry.species == "coding" and entry.verdict == "agree" and entry.contradiction.source.role == "coder"
    assert entry.adjudicator.role == "adjudicator", "nothing auto-admits: the adjudicator gated the mint"


def test_the_default_review_runs_the_convention_axis(store, monkeypatch):
    s1, s2 = _session(store, 1), _session(store, 2)
    _observe(store, s1, ["other(paging-cursor)"], "task t failed on a cursor")
    _observe(store, s2, ["other(paging-cursor)"], "task u failed on a cursor")
    monkeypatch.setitem(stub.HANDLERS, "coding", lambda req: {name: ["other(uncovered)"] for name in (o["name"] for o in req["observations"])})
    record = _record(store)
    noms = _reviews.vocabulary(store, record)  # no vocab named: every reviewable one, the convention axis included
    assert any(n.subject == "convention/paging-cursor" for n in noms)
    assert "convention/paging-cursor" in record.minted
