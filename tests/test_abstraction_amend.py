"""A landed ``payload:abstraction`` is amend-only. With no premise kill beside it and the bar met, the consolidator is
re-asked once to promote the payload to the transferable shape (the instances stay as anchors), the abstraction angle is
walked again over the promoted draft, and the adjudicator judges that draft; when no promotion comes back, the
adjudicator's own ``admit-amended(<amendment>)`` restates the payload and the committer admits the amended text. An
abstraction claim never declines a draft by itself."""

from __future__ import annotations

import json

from hgi import consolidate as _consolidate
from hgi import model as _model
from hgi.store import now
from hgi.types import Consolidation, Nomination
from tests.conftest import decision_body, draft
from tests.test_slice3 import CLEAN, FAULTED, NO_CAUSE, NOT_RETRIED, _observe, _session

COPIED = "The sum_numbers task's wrapper carries the HTTP cause on rethrow."


def _record(store) -> Consolidation:
    return Consolidation(id=store.mint("consolidation"), started_at=now(), after_pass=2, sessions_read=["S-0001", "S-0002"])


def _nominated(store, rows, scores, noticed, **overrides):
    s1, s2 = _session(store, 1, rows, scores), _session(store, 2, rows, scores)
    o1, o2 = _observe(store, s1, noticed), _observe(store, s2, noticed)
    d = draft(store, **overrides).model_copy(update={"evidence": [o1.name, o2.name]})
    store.write_draft(d)
    return d, Nomination(rung="new-decision", rung_why="a test", subject="cause", evidence=[o1.name, o2.name], draft=d.uid)


def _requests(monkeypatch):
    seen = []
    real = _model.complete

    def spy(role, payload, **kw):
        seen.append((role, json.loads(payload)))
        return real(role, payload, **kw)

    monkeypatch.setattr(_model, "complete", spy)
    return seen


def test_a_copied_instance_is_promoted_once_and_the_promoted_payload_is_admitted(store, monkeypatch):
    seen = _requests(monkeypatch)
    d, nomination = _nominated(store, [FAULTED], {"task_pass_rate": 0.5, "error_cause_present": 0.0}, NO_CAUSE, decision=COPIED)
    entry = _consolidate.adjudicate(store, _record(store), nomination, d, {"scores": {}})
    promotes = [req for role, req in seen if req.get("request") == "promote"]
    assert [role for role, req in seen if req.get("request") == "promote"] == ["consolidator"] and promotes[0]["decision"] == COPIED
    assert promotes[0]["instances"] == [NO_CAUSE, NO_CAUSE] and "genesis/sum_numbers" in promotes[0]["task_ids"]
    walks = [req["lens"]["id"] for role, req in seen if req.get("request") == "attack"]
    assert walks == ["L-0006", "L-0007", "L-0007"], "the abstraction angle is walked again over the promoted draft; the premise angle stands"
    assert entry.outcome == "admitted D-0001; the payload was promoted on the examiner's abstraction claim"
    assert entry.verdict == "survived-with-attack-named" and entry.claim == COPIED
    promoted = store.read("decision", "D-0001").decision
    assert "sum_numbers" not in promoted and promoted == entry.amendment == "The task's wrapper carries the HTTP cause on rethrow."
    assert entry.contradiction.coding["promotion"]["decision"] == COPIED
    assert [c["landed"] for c in entry.contradiction.coding["promotion"]["claims"]] == [True]
    final = [c for c in entry.contradiction.attack.claims if c.target == "payload:abstraction"]
    assert len(final) == 1 and final[0].landed is False and final[0].lens == "L-0007"


def test_with_no_promotion_the_adjudicator_amends_and_the_committer_admits_the_amended_text(store, monkeypatch):
    monkeypatch.setattr(_consolidate, "promote", lambda *a, **k: None)
    d, nomination = _nominated(store, [FAULTED], {"task_pass_rate": 0.5, "error_cause_present": 0.0}, NO_CAUSE, decision=COPIED)
    entry = _consolidate.adjudicate(store, _record(store), nomination, d, {"scores": {}})
    assert entry.outcome == "admitted D-0001" and entry.verdict == "survived-with-attack-named"
    assert entry.contradiction.coding is None and entry.claim == COPIED
    assert entry.amendment == "The task's wrapper carries the HTTP cause on rethrow."
    assert store.read("decision", "D-0001").decision == entry.amendment
    assert store.read("decision", "D-0001").admission.verdict.startswith("admit-amended(")
    assert next(c for c in entry.contradiction.attack.claims if c.target == "payload:abstraction").landed is True


def test_a_premise_kill_beside_the_abstraction_claim_promotes_nothing_and_declines(store, monkeypatch):
    seen = _requests(monkeypatch)
    warrant = decision_body()["warrant"] | {"premises": [{"id": "p1", "statement": "a transient fault clears on the next call",
                                                          "falsifier": "no transient fault in the trace store over the window", "status": "supported"}]}
    d, nomination = _nominated(store, [CLEAN], {"task_pass_rate": 1.0}, NOT_RETRIED, decision=COPIED, warrant=warrant)
    entry = _consolidate.adjudicate(store, _record(store), nomination, d, {"scores": {}})
    assert not [req for role, req in seen if req.get("request") == "promote"]
    assert entry.verdict == "premise-killed" and entry.outcome == "declined; draft dropped"
    assert {c.target for c in entry.contradiction.attack.claims if c.landed} == {"premise:p1", "payload:abstraction"}


def test_a_promotion_that_returns_the_same_text_is_no_promotion(store, monkeypatch):
    from hgi import stub as _stub
    monkeypatch.setitem(_stub.HANDLERS, "promote", lambda req: {"decision": req["decision"]})
    d, nomination = _nominated(store, [FAULTED], {"task_pass_rate": 0.5, "error_cause_present": 0.0}, NO_CAUSE, decision=COPIED)
    entry = _consolidate.adjudicate(store, _record(store), nomination, d, {"scores": {}})
    assert entry.contradiction.coding is None and entry.outcome == "admitted D-0001"
    assert store.read("decision", "D-0001").decision == entry.amendment == "The task's wrapper carries the HTTP cause on rethrow."
