"""The port calculus's miss stream (doctrine § 9, the port law): a latch admitted off its declaration carries a warrant, and the
channel recurring across independent records nominates widening the mark; the adjudicator decides and the registry is
corrected in place."""

from __future__ import annotations

from hgi import consolidate as _consolidate
from hgi import lint as _lint
from hgi import registry as _registry
from hgi import reviews as _reviews
from hgi.store import Store
from tests.conftest import adjudicated_entry, adjudicator, decision_body, draft
from tests.test_slice3 import CLEAN, _session

OFF = {"type": "floor", "slot": "enforcement", "key_space": "diff", "edge": {"kind": "level", "at": "commit"}, "guard": {}, "consumer": "the committer's lint",
       "owed_act": {"class": "check", "role": "corroborating"}, "lifecycle": {"status": "live"}, "warrant": "the decision's shape is lint-checkable at commit; the floor latch names the check"}


def _admit_with_floor_latch(store: Store, name: str, proposed_by: str):
    body = decision_body()
    body["latches"].append(OFF)
    d = draft(store, name, latches=body["latches"])
    d = d.model_copy(update={"proposed_by": proposed_by})
    entry = adjudicated_entry(store, d.uid)
    entry.verdict = "admit"
    return store.admit(d, entry, adjudicator())


def test_a_recurring_off_declaration_channel_widens_the_mark_on_the_adjudicators_verdict(store):
    _session(store, 1, [CLEAN], {"task_pass_rate": 1.0}), _session(store, 2, [CLEAN], {"task_pass_rate": 1.0})
    d1 = _admit_with_floor_latch(store, "P-a", "S-0001")
    assert store.registry.port("decision", "accepted", "floor") == "forbidden"
    assert not [f for f in _lint.run(store, seams=("write",)).failures if f.check == "ports"], "a warranted off-declaration latch is admitted"
    [c] = _reviews.port_clusters(store)
    assert c["subject"] == "port/decision/accepted/floor" and c["records"] == [d1.id]
    record = _consolidate.consolidate(store)
    assert not [n for n in record.nominations if n.subject.startswith("port/")], "one record is one datum"
    d2 = _admit_with_floor_latch(store, "P-b", "S-0002")
    _session(store, 3, [CLEAN], {"task_pass_rate": 1.0}), _session(store, 4, [CLEAN], {"task_pass_rate": 1.0})
    record = _consolidate.consolidate(store)
    n = next(n for n in record.nominations if n.subject == "port/decision/accepted/floor")
    assert n.evidence == [d1.id, d2.id] and n.outcome.endswith("widened from forbidden to optional")
    assert store.registry.port("decision", "accepted", "floor") == "optional"
    assert _registry.load(store.root).port("decision", "accepted", "floor") == "optional", "the register was corrected in place"
    entry = next(e for e in store.all("hypothesis") if e.id == n.ledger_entry)
    assert entry.species == "currency" and entry.verdict == "reversed" and entry.contradiction.source.role == "oracle" and entry.adjudicator.role == "adjudicator"
    assert _reviews.port_clusters(store) == [], "a widened port is no longer off-declaration"
    assert "port/decision/accepted/floor" in record.minted


def test_a_declined_widening_is_renominated_only_by_new_recurrence(store, monkeypatch):
    from hgi import stub
    _session(store, 1, [CLEAN], {"task_pass_rate": 1.0}), _session(store, 2, [CLEAN], {"task_pass_rate": 1.0})
    _admit_with_floor_latch(store, "P-a", "S-0001"), _admit_with_floor_latch(store, "P-b", "S-0002")
    monkeypatch.setitem(stub.HANDLERS, "ports", lambda req: {"verdict": "decline(the warrants restate the purpose)", "why": "stands"})
    record = _consolidate.consolidate(store)
    n = next(n for n in record.nominations if n.subject.startswith("port/"))
    assert "the declaration stands" in n.outcome and store.registry.port("decision", "accepted", "floor") == "forbidden"
    assert _reviews.port_clusters(store) == [], "the adjudicated occasions do not count again"
