"""The key-space law as a floor (doctrine § 9): a neighbour key resolves, a world-state key names a series the oracle runs."""

from __future__ import annotations

from hgi import lint as _lint
from tests.conftest import adjudicated_entry, adjudicator, decision_body, draft


def _admit(store, name, **overrides):
    d = draft(store, name, **overrides)
    entry = adjudicated_entry(store, d.uid)
    entry.verdict = "admit"
    return store.admit(d, entry, adjudicator())


def test_a_watch_on_a_scorer_the_oracle_does_not_run_is_refused(store):
    body = decision_body()
    for l in body["latches"]:
        if l["type"] == "revisit":
            l["edge"]["predicate"]["scorer"] = "latency_p95"
    d = _admit(store, "P-alias", latches=body["latches"])
    findings = [f for f in _lint.run(store, seams=("write",)).failures if f.check == "key-space"]
    assert len(findings) == 1 and findings[0].record == d.id and "latency_p95" in findings[0].message


def test_a_neighbour_that_resolves_to_nothing_is_refused_and_a_real_one_passes(store):
    d1 = _admit(store, "P-a")
    body = decision_body()
    body["latches"].append({"type": "wiring", "slot": "lifecycle", "key_space": "neighbor", "edge": {"kind": "edge"},
                            "guard": {"records": ["D-9999"], "statuses": {}}, "consumer": "propagation",
                            "owed_act": {"class": "check", "role": "corroborating"}, "lifecycle": {"status": "live"}})
    d2 = _admit(store, "P-dangling", latches=body["latches"])
    findings = [f for f in _lint.run(store, seams=("write",)).failures if f.check == "key-space"]
    assert [f.record for f in findings] == [d2.id] and "D-9999" in findings[0].message
    body["latches"][-1]["guard"]["records"] = [d1.id]
    _admit(store, "P-wired", latches=body["latches"])
    assert [f.record for f in _lint.run(store, seams=("write",)).failures if f.check == "key-space"] == [d2.id]
