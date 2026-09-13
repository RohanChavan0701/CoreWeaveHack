"""A refused draft leaves its evidence in the open pile. Only ``store.admit`` promotes an observation; decline/drop,
floor-refusal and escalate all drop the draft (``store.drop_draft`` only unlinks the proposal file) and touch no
observation. So an observation a refused draft rested on is still ``open`` afterwards and regroups with a later
same-shape observation at higher N — the recurrence keeps accruing across passes, it is not spent by one refusal.

Deferral is the intended exception (``group_observations`` claims a deferred draft's evidence while it lives); it is
covered elsewhere and is not a refusal."""

from __future__ import annotations

from hgi import consolidate as _consolidate
from hgi import model as _model
from hgi.store import now
from hgi.types import Consolidation, Nomination
from tests.conftest import decision_body, draft
from tests.test_slice3 import CLEAN, FAULTED, NO_CAUSE, NOT_RETRIED, _observe, _session


def _record(store) -> Consolidation:
    return Consolidation(id=store.mint("consolidation"), started_at=now(), after_pass=2, sessions_read=["S-0001", "S-0002"])


def _open_names(store) -> set[str]:
    return {o.name for o in store.observations("open")}


def _premise_declined(store):
    """A draft that declines on an upheld premise kill and is dropped: evidence on two sessions, a supported premise the
    stub examiner refutes off the CLEAN rows / NOT_RETRIED noticing."""
    s1, s2 = _session(store, 1, [CLEAN], {"task_pass_rate": 1.0}), _session(store, 2, [CLEAN], {"task_pass_rate": 1.0})
    o1, o2 = _observe(store, s1, NOT_RETRIED), _observe(store, s2, NOT_RETRIED)
    warrant = decision_body()["warrant"] | {"premises": [{"id": "p1", "statement": "a transient fault clears on the next call",
                                                          "falsifier": "no transient fault in the trace store over the window", "status": "supported"}]}
    d = draft(store, warrant=warrant).model_copy(update={"evidence": [o1.name, o2.name]})
    store.write_draft(d)
    nomination = Nomination(rung="new-decision", rung_why="a test", subject="cause", evidence=[o1.name, o2.name], draft=d.uid)
    return d, nomination, [o1.name, o2.name]


def test_a_declined_draft_leaves_its_evidence_open_and_it_regroups_at_higher_n(store):
    d, nomination, names = _premise_declined(store)
    entry = _consolidate.adjudicate(store, _record(store), nomination, d, {"scores": {}})
    assert entry.outcome == "declined; draft dropped" and store.drafts() == []
    # the two observations the dropped draft rested on are still in the open pile
    assert set(names) <= _open_names(store)
    for name in names:
        assert store.observation(name).disposition.state == "open"
    # a subsequent consolidation with one more same-shape observation regroups them at higher N
    _observe(store, _session(store, 3, [CLEAN], {"task_pass_rate": 1.0}), NOT_RETRIED)
    groups = _consolidate.group_observations(store, _record(store))
    regrouped = max(groups, key=lambda g: len(g["sessions"]))
    assert len(regrouped["sessions"]) == 3, "the declined evidence rejoins the group and the recurrence grows"


def test_a_floor_refused_draft_leaves_its_evidence_open(store, monkeypatch):
    """One session is below the bar: admit is routed but the floor refuses. The refusal drops the draft and leaves the
    single observation open."""
    monkeypatch.setattr(_consolidate, "verdict", lambda *a, **k: ("admit", {"verdict": "admit", "amendment": None, "rationale": "ok"},
                                                                  _model.Completion(text="{}", model_id="fixed", call=None)))
    o = _observe(store, _session(store, 1, [FAULTED], {"task_pass_rate": 0.5, "error_cause_present": 0.0}), NO_CAUSE)
    d = draft(store).model_copy(update={"evidence": [o.name]})
    store.write_draft(d)
    nomination = Nomination(rung="new-decision", rung_why="a test", subject="cause", evidence=[o.name], draft=d.uid)
    entry = _consolidate.adjudicate(store, _record(store), nomination, d, {"scores": {}})
    assert entry.outcome.startswith("refused by the floor") and store.decisions() == []
    assert o.name in _open_names(store) and store.observation(o.name).disposition.state == "open"


def test_an_escalated_draft_leaves_its_evidence_open(store, monkeypatch):
    monkeypatch.setattr(_consolidate, "verdict", lambda *a, **k: ("escalate(ambiguous)", {"verdict": "escalate(ambiguous)", "amendment": None, "rationale": "unsure"},
                                                                  _model.Completion(text="{}", model_id="fixed", call=None)))
    s1, s2 = _session(store, 1, [FAULTED], {"task_pass_rate": 0.5}), _session(store, 2, [FAULTED], {"task_pass_rate": 0.5})
    o1, o2 = _observe(store, s1, NO_CAUSE), _observe(store, s2, NO_CAUSE)
    d = draft(store).model_copy(update={"evidence": [o1.name, o2.name]})
    store.write_draft(d)
    nomination = Nomination(rung="new-decision", rung_why="a test", subject="cause", evidence=[o1.name, o2.name], draft=d.uid)
    entry = _consolidate.adjudicate(store, _record(store), nomination, d, {"scores": {}})
    assert entry.outcome == "escalated to the human queue" and len(store.queue()) == 1
    assert {o1.name, o2.name} <= _open_names(store)
    for name in (o1.name, o2.name):
        assert store.observation(name).disposition.state == "open"
