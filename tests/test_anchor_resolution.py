"""The complement law's anchor check resolves: a counterfactual citing an observation or record the store does not hold is
priming wearing an anchor and warns — never fails, so an admitted record stays at the floor while its anchor is missing."""

from __future__ import annotations

from hgi import lint as _lint
from hgi.store import now
from hgi.types import LedgerEntry
from tests.conftest import decision_body, draft
from tests.test_lineage_ops import _observe


def _warnings(store, d):
    return [f for f in _lint.body_findings(d.name, d.body, store) if f.check == "complement-law" and f.level == "warn"]


def test_an_anchor_the_store_holds_passes_and_one_it_does_not_warns(store):
    d = draft(store)  # its counterfactual cites O-0001
    [w] = _warnings(store, d)
    assert "O-0001" in w.message and "names nothing in the store" in w.message
    assert not [f for f in _lint.body_findings(d.name, d.body, store) if f.level == "fail"], "a warning, never a failure"
    _observe(store, "O-0001", "S-0001")
    assert _warnings(store, d) == []


def test_every_kind_of_store_anchor_resolves(store):
    _observe(store, "O-0001", "S-0001")
    o = store.observation("O-0001")
    store.append(LedgerEntry(id=store.mint("hypothesis"), at=now(), species="currency", subject="D-0001", claim="x",
                             proposer={"role": "consolidator", "call": None}, contradiction={"source": {"role": "oracle", "call": "competence:D-0001"}}))
    assert store.lookup("O-0001") is not None and store.lookup(o.uid) is not None and store.lookup("H-0001") is not None
    assert store.lookup("O-0009") is None and store.lookup("H-0009") is None and store.lookup("D-0001") is None
    assert _lint.unresolved_anchors(store, "seen in O-0001, H-0001 and O-0009; bounded by commit:abc1234 and suite/tools.py:54 and weave:///p/call/1") == ["O-0009"]


def test_the_check_runs_over_the_store_and_the_committers_floor(store):
    d = draft(store, counterfactual="The overshoot is a retry storm — observed in O-0042.")
    assert any("O-0042" in f.message for f in _lint.check_draft(store, d))
    store.write_draft(d)
    findings = [f for f in _lint.run(store, seams=("write",)).findings if f.check == "complement-law"]
    assert [f.level for f in findings] == ["warn"] and "O-0042" in findings[0].message
