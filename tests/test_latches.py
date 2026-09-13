"""The latch fan walked: a defer(<until>) verdict re-queues the draft with its condition as a latch that the oracle or the
schedule fires and the backward pass re-adjudicates; wiring latches fire when a neighbour departs from the status last
seen, propagation checks the host in the same commit, and a rotted anchor goes to the adjudicator."""

from __future__ import annotations

from hgi import consolidate as _consolidate
from hgi import evaluate as _evaluate
from hgi import index as _index
from hgi import latches as _latches
from hgi import lint as _lint
from hgi import stub
from hgi.store import now
from hgi.types import Disposition, Session
from tests.conftest import adjudicated_entry, adjudicator, decision_body, draft
from tests.test_lineage_ops import _observe
from tests.test_slice3 import FAULTED, NO_CAUSE, _observe as _notice, _session


def test_a_deferral_keyed_on_the_oracle_fires_at_evaluate_and_is_readjudicated(store):
    s1 = _session(store, 1, [FAULTED], {"task_pass_rate": 0.5, "error_cause_present": 0.0})
    s2 = _session(store, 2, [FAULTED], {"task_pass_rate": 0.5, "error_cause_present": None})
    _notice(store, s1, NO_CAUSE), _notice(store, s2, NO_CAUSE)
    k1 = _consolidate.consolidate(store)
    assert k1.admitted == [] and len(k1.deferred) == 1 and store.queue() == []
    (p,) = store.drafts()
    attack = next(e for e in store.all("hypothesis") if e.species == "attack")
    assert p.deferral and p.deferral.ledger_entry == attack.id and p.deferral.until.key_space == "world-state"
    assert p.deferral.until.edge.predicate.scorer == "error_cause_present" and p.deferral.until.consumer == _latches.BACKWARD_PASS
    assert k1.nominations[0].outcome.startswith("deferred; re-queued with its condition as a latch: error_cause_present >= 0.0 over 2 run(s)")
    first_attack = next(e for e in store.all("hypothesis") if e.species == "attack")
    assert first_attack.verdict == "pending" or first_attack.outcome.startswith("deferred")
    trig = _index.triggers(store)
    assert [t["record"] for t in trig] == [p.uid] and _index.deferred(store)[0]["draft"] == p.uid
    _index.regenerate(store)
    assert _lint.run(store).green

    s3 = _session(store, 3, [FAULTED], {"task_pass_rate": 0.5, "error_cause_present": 0.0})
    assert _evaluate.emit_fires(store, s3) == []  # one evaluable run; persistence is two
    s4 = _session(store, 4, [FAULTED], {"task_pass_rate": 0.5, "error_cause_present": 0.0})
    (fire,) = _evaluate.emit_fires(store, s4)
    assert fire.latch.record == p.uid and fire.disposer == _latches.BACKWARD_PASS and fire.disposition.act == "re-adjudicate"
    store.write(s4)
    k2 = _consolidate.consolidate(store)
    assert k2.fires_discharged == [fire.id] and k2.admitted == ["D-0001"] and store.drafts() == []
    d = store.read("decision", "D-0001")
    assert d.admission.ledger_entry != "H-0001", "the re-adjudication is a fresh attack and verdict, not the deferring entry"
    assert store.read("fire", fire.id).disposition.outcome == "admitted D-0001"
    _index.regenerate(store)
    assert _lint.run(store).green and _index.triggers(store)[0]["record"] == "D-0001"


def test_a_deferral_keyed_on_the_schedule_fires_when_the_passes_have_elapsed(store, monkeypatch):
    s1 = _session(store, 1, [FAULTED], {"task_pass_rate": 0.5, "error_cause_present": 0.0})
    s2 = _session(store, 2, [FAULTED], {"task_pass_rate": 0.5, "error_cause_present": 0.0})
    _notice(store, s1, NO_CAUSE), _notice(store, s2, NO_CAUSE)
    verdicts = iter([{"verdict": "defer(until one more pass has run)", "amendment": None, "until": {"passes": 1}}, {"verdict": "admit", "amendment": None}])
    monkeypatch.setitem(stub.HANDLERS, "verdict", lambda req: next(verdicts))
    k1 = _consolidate.consolidate(store)
    (p,) = store.drafts()
    assert k1.deferred == [p.uid] and p.deferral.until.edge.kind == "schedule" and p.deferral.until.guard.over_passes == 1 and p.deferral.after_pass == 2
    assert _consolidate.consolidate(store, force=True).fires_discharged == [], "no pass has run since the deferral"
    _session(store, 3, [FAULTED], {"task_pass_rate": 0.5, "error_cause_present": 0.0})
    k3 = _consolidate.consolidate(store, force=True)
    (fire,) = [store.read("fire", f) for f in k3.fires_discharged]
    assert fire.edge_event.scorer == "passes_since_deferral" and fire.edge_event.observed == 1 and k3.admitted == ["D-0001"]


def test_an_escape_verdict_is_requeued_at_the_next_backward_pass(store, monkeypatch):
    s1 = _session(store, 1, [FAULTED], {"task_pass_rate": 0.5, "error_cause_present": 0.0})
    s2 = _session(store, 2, [FAULTED], {"task_pass_rate": 0.5, "error_cause_present": 0.0})
    _notice(store, s1, NO_CAUSE), _notice(store, s2, NO_CAUSE)
    monkeypatch.setitem(stub.HANDLERS, "verdict", lambda req: {"verdict": "other(the adjudicator wants a third reading)", "amendment": None})
    k1 = _consolidate.consolidate(store)
    (p,) = store.drafts()
    assert k1.deferred == [p.uid] and p.deferral.until.guard.over_passes == store.registry.bars["consolidation_every_passes"]


def _admit(store, name="A", **overrides):
    d = draft(store, name, **overrides)
    entry = adjudicated_entry(store, d.uid)
    entry.verdict = "admit"
    return store.admit(d, entry, adjudicator())


def _retire_by_ratio(store, decision, first_pass: int):
    window = store.registry.bars["retirement"]["window_passes"]
    for n in range(first_pass, first_pass + window):
        s = Session(id=store.mint("session"), pass_=n, started_at=now(), closed_at=now(), attached=True,
                    evaluation={"evaluation": "suite-v1", "scores": {"task_pass_rate": {"series": "suite-v1/task_pass_rate", "value": 0.5, "as_of": now()}}, "rows": []})
        store.write(s)
        store.append(Disposition(id=store.mint("disposition"), session=s.id, record=decision.id, considered=True, guard_passed=True,
                                 disposition="considered-not-applicable"))


def test_a_tombstone_is_checked_when_its_successor_moves(store):
    _observe(store, "O-0001", "S-0001"), _observe(store, "O-0002", "S-0002")
    a = _admit(store, "A")
    b_draft = draft(store, "B").model_copy(update={"supersedes": [a.id]})
    entry = adjudicated_entry(store, b_draft.uid)
    entry.verdict = "admit"
    b = store.admit(b_draft, entry, adjudicator())
    tomb = store.read("decision", a.id)
    (wire,) = [l for l in tomb.latches if l.type == "wiring"]
    assert wire.guard.records == [b.id] and wire.guard.statuses == {b.id: "accepted"} and wire.consumer == _latches.PROPAGATION
    assert _index.wiring(store) == [{"record": a.id, "status": "superseded", "latch_index": tomb.latches.index(wire), "neighbours": [b.id],
                                     "seen": {b.id: "accepted"}, "owed_act": "check", "disposer": _latches.PROPAGATION}]
    _retire_by_ratio(store, b, 1)
    k = _consolidate.consolidate(store, force=True)
    assert k.flipped == [b.id] and store.read("decision", b.id).status == "moot"
    (fire,) = [store.read("fire", f) for f in k.fires_discharged]
    assert fire.latch.record == a.id and fire.disposer == _latches.PROPAGATION and fire.edge_event == fire.edge_event.model_copy(
        update={"evaluation": "neighbor", "scorer": f"{b.id}.status", "observed": "moot", "source": k.id})
    assert fire.disposition.discharged and fire.disposition.outcome.startswith(f"check: {b.id} is now moot; the tombstone {a.id} keeps its pointer")
    assert _consolidate.consolidate(store, force=True).fires_discharged == [], "a departure fires once; the ledger remembers what was seen"
    _index.regenerate(store)
    assert _lint.run(store).green and _index.undischarged_fires(store) == []


def test_a_warrant_citing_a_record_is_wired_to_it_and_a_rotted_anchor_goes_to_the_adjudicator(store):
    _observe(store, "O-0001", "S-0001"), _observe(store, "O-0002", "S-0002")
    a = _admit(store, "A")
    body = decision_body()
    body["warrant"]["anchors"] = ["O-0001", a.id]
    body["decision"] = "A retried tool call is reported with its cause when it fails again."
    c = _admit(store, "C", **body)
    (wire,) = [l for l in c.latches if l.type == "wiring"]
    assert wire.guard.records == [a.id] and wire.guard.statuses == {a.id: "accepted"} and wire.owed_act.role == "corroborating"
    _retire_by_ratio(store, a, 1)
    k = _consolidate.consolidate(store, force=True)
    assert a.id in k.flipped
    (fire,) = [store.read("fire", f) for f in k.fires_discharged]
    assert fire.latch.record == c.id and "cites a retired record" in fire.disposition.outcome
    entry = [e for e in store.all("hypothesis") if e.species == "currency" and e.subject == c.id][-1]
    assert entry.verdict == "reversed" and entry.contradiction.coding == {"fire": fire.id, "rotted": [a.id]} and entry.adjudicator.role == "adjudicator"
    assert fire.disposition.outcome.endswith(f"{entry.id}: reversed: every premise of {c.id} disputed")
    disputed = store.read("decision", c.id)
    assert disputed.status == "accepted" and {p.status for p in disputed.warrant.premises} == {"disputed"}, "reversed disputes the warrant; the record stands until superseded"
    _index.regenerate(store)
    assert _lint.run(store).green
