"""A draft is declined only on an upheld premise kill. The adjudicator's ``decline`` with no landed ``premise:`` claim is
overridden to an admit — amended where it offered an amendment — with the attack still named on the entry and the override
on its outcome; the attacker projection reads it as a landing overruled. Defer and escalate are the adjudicator's as returned."""

from __future__ import annotations

from hgi import consolidate as _consolidate
from hgi import index as _index
from hgi import model as _model
from hgi.store import now
from hgi.types import Consolidation, Nomination
from tests.conftest import decision_body, draft
from tests.test_abstraction_amend import COPIED, _nominated
from tests.test_slice3 import CLEAN, FAULTED, NO_CAUSE, NOT_RETRIED

OVERRIDE = "a decline stands only on an upheld premise kill"


def _record(store) -> Consolidation:
    return Consolidation(id=store.mint("consolidation"), started_at=now(), after_pass=2, sessions_read=["S-0001", "S-0002"])


def _adjudicator_returns(monkeypatch, token: str, **reply):
    """The adjudicator's context replaced by a fixed reply; the examiner and the code's readings still run."""
    monkeypatch.setattr(_consolidate, "verdict", lambda *a, **k: (token, {"verdict": token, "amendment": None, "rationale": "fixed", **reply},
                                                                    _model.Completion(text="{}", model_id="fixed", call=None)))


def test_a_decline_with_no_landed_premise_is_overridden_to_an_admit_with_the_attack_named(store, monkeypatch):
    monkeypatch.setattr(_consolidate, "promote", lambda *a, **k: None)  # the abstraction claim stays landed on the judged draft
    _adjudicator_returns(monkeypatch, "decline(payload is a copied instance)")
    d, nomination = _nominated(store, [FAULTED], {"task_pass_rate": 0.5, "error_cause_present": 0.0}, NO_CAUSE, decision=COPIED)
    entry = _consolidate.adjudicate(store, _record(store), nomination, d, {"scores": {}})
    assert entry.outcome == f"admitted D-0001; the adjudicator's decline(payload is a copied instance) was overridden: {OVERRIDE}"
    assert entry.verdict == "survived-with-attack-named" and entry.rationale == "fixed" and entry.amendment is None
    assert next(c for c in entry.contradiction.attack.claims if c.target == "payload:abstraction").landed is True, "the attack stays named"
    decision = store.read("decision", "D-0001")
    assert decision.admission.verdict == "admit" and decision.decision == COPIED and store.drafts() == []
    a = _index.attacker(store)
    assert a["entries_with_landing"] == 1 and a["upheld"] == 0 and a["overruled"] == 1 and a["precision"] == 0.0


def test_an_overridden_decline_that_offered_an_amendment_admits_the_amended_text(store, monkeypatch):
    _adjudicator_returns(monkeypatch, "decline(names the task)", amendment="Errors that wrap a failed call carry the cause.")
    d, nomination = _nominated(store, [FAULTED], {"task_pass_rate": 0.5, "error_cause_present": 0.0}, NO_CAUSE)
    entry = _consolidate.adjudicate(store, _record(store), nomination, d, {"scores": {}})
    assert entry.outcome.startswith("admitted D-0001; the adjudicator's decline(names the task) was overridden")
    decision = store.read("decision", "D-0001")
    assert decision.decision == entry.amendment == "Errors that wrap a failed call carry the cause."
    assert decision.admission.verdict == "admit-amended(Errors that wrap a failed call carry the cause.)"


def test_a_decline_on_a_landed_premise_kill_stands_and_drops_the_draft(store, monkeypatch):
    _adjudicator_returns(monkeypatch, "decline(premise killed: p1)")
    warrant = decision_body()["warrant"] | {"premises": [{"id": "p1", "statement": "a transient fault clears on the next call",
                                                          "falsifier": "no transient fault in the trace store over the window", "status": "supported"}]}
    d, nomination = _nominated(store, [CLEAN], {"task_pass_rate": 1.0}, NOT_RETRIED, warrant=warrant)
    entry = _consolidate.adjudicate(store, _record(store), nomination, d, {"scores": {}})
    assert entry.verdict == "premise-killed" and entry.outcome == "declined; draft dropped"
    assert store.drafts() == [] and store.decisions() == [] and _index.attacker(store)["upheld"] == 1


def test_an_overridden_decline_still_meets_the_floor(store, monkeypatch):
    _adjudicator_returns(monkeypatch, "decline(reluctance)")
    d = draft(store)  # evidence names observations the store does not hold: one context, zero sessions
    store.write_draft(d)
    nomination = Nomination(rung="new-decision", rung_why="a test", subject="cause", evidence=list(d.evidence), draft=d.uid)
    entry = _consolidate.adjudicate(store, _record(store), nomination, d, {"scores": {}})
    assert entry.outcome == f"refused by the floor: 0 distinct session(s) in the evidence (none) against the bar 2; the adjudicator's decline(reluctance) was overridden: {OVERRIDE}"
    assert store.decisions() == [] and store.drafts() == []


def test_defer_and_escalate_are_the_adjudicators_as_returned(store, monkeypatch):
    _adjudicator_returns(monkeypatch, "escalate(ambiguous)")
    d, nomination = _nominated(store, [FAULTED], {"task_pass_rate": 0.5, "error_cause_present": 0.0}, NO_CAUSE)
    entry = _consolidate.adjudicate(store, _record(store), nomination, d, {"scores": {}})
    assert entry.outcome == "escalated to the human queue" and entry.verdict == "pending" and len(store.queue()) == 1
    _adjudicator_returns(monkeypatch, "defer(until the next run)", until=None)
    d2 = draft(store, "D-draft-2").model_copy(update={"evidence": list(d.evidence)})
    store.write_draft(d2)
    entry = _consolidate.adjudicate(store, _record(store), Nomination(rung="new-decision", rung_why="a test", subject="cause", evidence=list(d.evidence), draft=d2.uid), d2, {"scores": {}})
    assert entry.outcome.startswith("deferred; re-queued with its condition as a latch") and entry.verdict == "pending"
