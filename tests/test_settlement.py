"""A settlement cites what licensed it: an adjudicated ledger entry, a dispositive fire, or the admitted successor.
A fire on a corroborating latch nominates and never settles; a consolidation or a pending entry is no licence;
the lint proves it on every settled latch."""

from __future__ import annotations

import pytest

from hgi import index as _index
from hgi import lint as _lint
from hgi.registry import read_json, write_json
from hgi.store import now
from hgi.types import Fire
from tests.conftest import NOW, adjudicated_entry, adjudicator, draft
from tests.test_lineage_ops import _observe


def _admit(store):
    """As the backward pass leaves it: the attack entry on the ledger, the admission stamped from a copy carrying the adjudicator's token."""
    _observe(store, "O-0001", "S-0001"), _observe(store, "O-0002", "S-0002")
    d = draft(store)
    entry = adjudicated_entry(store, d.uid)
    store.append(entry)
    return store.admit(d, entry.model_copy(update={"verdict": "admit"}), adjudicator())


def _fire(store, decision, index: int) -> Fire:
    f = Fire(id=store.mint("fire"), fired_at=now(), latch={"record": decision.id, "index": index},
             edge_event={"evaluation": "suite-v1", "pass": 2, "scorer": "error_cause_present", "observed": 0.0},
             guard_result=True, disposer="the backward pass", disposition={"act": "re-adjudicate"})
    store.write(f)
    return f


def test_a_corroborating_fire_cannot_settle_and_a_dispositive_one_can(store):
    d = _admit(store)
    latches = d.all_latches()
    retirement = _fire(store, d, latches.index(d.lifecycle.retirement))
    assert d.lifecycle.retirement.owed_act.role == "corroborating"
    with pytest.raises(PermissionError, match="corroborating latch, which nominates and never settles"):
        store.flip_status(d, "moot", by=retirement.id)
    with pytest.raises(PermissionError, match="nominates and never settles"):
        store.flip_premises(d, "disputed", by=retirement.id)
    assert store.read("decision", d.id).status == "accepted"
    revisit = _fire(store, d, next(i for i, l in enumerate(latches) if l.type == "revisit"))
    assert store.license(revisit.id) == f"dispositive fire {revisit.id}"
    flipped = store.flip_status(d, "moot", by=revisit.id)
    assert flipped.status == "moot" and {l.lifecycle.settled_by for l in flipped.all_latches() if l.lifecycle.status == "settled"} == {revisit.id}
    _index.regenerate(store)
    assert _lint.run(store).green


def test_only_an_adjudicated_entry_or_a_successor_licenses_a_flip(store):
    d = _admit(store)
    with pytest.raises(PermissionError, match="licenses no settlement"):
        store.flip_status(d, "moot", by="K-0001")
    with pytest.raises(PermissionError, match="cites what licensed it"):
        store.flip_status(d, "moot")
    pending = adjudicated_entry(store, d.id)
    pending.verdict, pending.adjudicator = "pending", None
    store.append(pending)
    with pytest.raises(PermissionError, match="carries no adjudicated verdict"):
        store.flip_premises(d, "disputed", by=pending.id)
    assert store.license(d.admission.ledger_entry).startswith("adjudicated entry")
    disputed = store.flip_premises(d, "reversed", "p1", by=d.admission.ledger_entry)
    assert [p.status for p in disputed.warrant.premises] == ["reversed"]
    assert store.license(d.id) == f"successor {d.id}"


def test_the_lint_refuses_a_settlement_with_no_licence(store):
    d = _admit(store)
    store.flip_status(d, "moot", by=d.admission.ledger_entry)
    path = store.path("decision", d.id)
    raw = read_json(path)
    raw["latches"][0]["lifecycle"]["settled_by"] = "K-0001"
    raw["latches"][1]["lifecycle"]["settled_by"] = None
    write_json(path, raw)
    findings = [f for f in _lint.run(store, seams=("write",)).failures if f.check == "settlement-authority"]
    assert [f.message for f in findings] == ["latch 0: 'K-0001' licenses no settlement: cite an adjudicated ledger entry, a dispositive fire, or the admitted successor",
                                             "latch 1 is settled by nothing"]
