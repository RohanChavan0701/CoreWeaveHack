"""Slice 0 acceptance: a hand-authored decision admits through the committer; a malformed record, a
proposal carrying a verdict, a fire without a disposer and an eighth constitution article are each
refused with the named check; ``hgi index`` is idempotent."""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from hgi import index as _index
from hgi import lint as _lint
from hgi.registry import write_json
from hgi.types import ConstitutionArticle, Fire
from tests.conftest import NOW, adjudicator, adjudicated_entry, decision_body, draft


def _write_observation(store, name: str, session: str):
    from hgi.types import Observation
    store.write(Observation(uid=store.new_uid(), name=name, noticed_at=NOW, session=session,
                            noticed="the http tool's retry wrapper drops the 502 body", anchor={"path": "suite/tools.py:41"}))


def test_decision_admits_through_committer(store):
    _write_observation(store, "O-0001", "S-0001")
    _write_observation(store, "O-0002", "S-0002")
    d = draft(store)
    store.write_draft(d)
    assert not [f for f in _lint.check_draft(store, d) if f.level == "fail"]
    entry = adjudicated_entry(store, d.uid)
    entry.verdict = "admit"
    decision = store.admit(d, entry, adjudicator())
    assert decision.id == "D-0001" and decision.status == "accepted"
    assert decision.admission.verdict == "admit" and decision.admission.adjudicator.role == "adjudicator"
    assert store.drafts() == []
    assert all(o.disposition.state == "promoted" and o.disposition.pointer == "D-0001" for o in store.observations(state=None))
    _index.regenerate(store)
    assert _lint.run(store).green
    assert "D-0001" in [c["record"] for c in _index.hooks(store)["tool-call-retry"]]


def test_committer_refuses_without_adjudicator_verdict(store):
    d = draft(store)
    entry = adjudicated_entry(store, d.uid)
    entry.verdict = "decline(premise killed)"
    with pytest.raises(PermissionError):
        store.admit(d, entry, adjudicator())
    with pytest.raises(PermissionError):
        store.mint("decision")


def test_malformed_record_refused_as_schema(store):
    write_json(store.path("decision", "D-0009"), {"id": "D-0009", "kind": "decision", "status": "accepted", "created_at": "2026-09-12T12:00:00+00:00"})
    findings = _lint.run(store, seams=("write",)).failures
    assert any(f.check == "schema" and f.record == "D-0009.json" for f in findings)


def test_closed_vocabulary_refused(store):
    body = decision_body()
    body["latches"][0]["guard"]["terms"] = ["a-term-nobody-registered"]
    with pytest.raises(ValidationError, match="closed vocabulary"):
        draft(store, **body)
    body["latches"][0]["guard"]["terms"] = ["other(streaming-tool)"]
    draft(store, **body)  # the escape is always legal


def test_proposal_carrying_a_verdict_refused(store):
    raw = store.parse_as(type(draft(store)), draft(store).model_dump(by_alias=True)).model_dump(by_alias=True, mode="json")
    raw["verdict"] = "admit"
    write_json(store.proposals_dir / "bad.json", raw)
    findings = _lint.run(store, seams=("write",)).failures
    assert any(f.check == "verdict-authority" for f in findings)


def test_attack_payload_carrying_a_verdict_refused(store):
    d = draft(store)
    entry = adjudicated_entry(store, d.uid).model_dump(by_alias=True, mode="json")
    entry["contradiction"]["attack"]["verdict"] = "attack-landed"
    with pytest.raises(ValidationError):
        store.parse("hypothesis", entry)
    entry["contradiction"]["attack"]["verdict"] = "pending"
    entry["adjudicator"] = None
    (store.path("hypothesis", "")).write_text(json.dumps(entry) + "\n")
    findings = _lint.run(store, seams=("write",)).failures
    assert any(f.check == "verdict-authority" and "no adjudicator" in f.message for f in findings)


def test_fire_without_disposer_refused(store):
    raw = {"id": "F-0001", "kind": "fire", "fired_at": NOW.isoformat(), "latch": {"record": "D-0001", "index": 1},
           "edge_event": {"evaluation": "suite-v1", "pass": 2, "scorer": "error_cause_present", "observed": 0.4},
           "guard_result": True, "disposer": "", "disposition": {"act": "re-adjudicate"}}
    with pytest.raises(ValidationError):
        Fire.model_validate(raw)
    write_json(store.path("fire", "F-0001"), raw)
    findings = _lint.run(store, seams=("write",)).failures
    assert any(f.check == "fire-disposer" for f in findings)


def test_eighth_article_refused_by_the_cap(store):
    eighth = ConstitutionArticle(id="C-0008", status="live", created_at=NOW,
                                 admission={"proposed_by": "genesis", "verdict": "admit", "committed_at": NOW},
                                 article="An eighth article.", counterfactual="The overshoot: none.", warrant={"evidence": "genesis"})
    findings = _lint.check_article_admissible(store, eighth)
    assert findings and findings[0].check == "constitution-cap" and "8th" in findings[0].message
    store.write(eighth)
    assert any(f.check == "constitution-cap" for f in _lint.run(store).failures)


def test_index_is_idempotent(store):
    first = _index.regenerate(store)
    files = {p.name: p.read_bytes() for p in store.index_dir.glob("*.json")}
    second = _index.regenerate(store)
    assert first == second
    assert files == {p.name: p.read_bytes() for p in store.index_dir.glob("*.json")}
    assert _index.check(store) == []


def test_settlement_test_refuses_a_compliable_cell(store, monkeypatch):
    monkeypatch.setitem(_index.PROJECTIONS, "leaky", lambda s: [{"record": "D-0001", "decision": "always retry"}])
    findings = _lint.check_settlement(store)
    assert findings and findings[0].check == "settlement-test"


def test_two_registries_over_one_store_never_mint_the_same_id(store):
    """A long-running runner and the commands it drives hold separate registry objects; the counters on disk decide."""
    from hgi import registry as _registry

    other = _registry.load(store.root)
    first = store.mint("session")
    second = other.mint("S")
    third = store.mint("session")
    assert (first, second, third) == ("S-0001", "S-0002", "S-0003")
    assert store.mint("consolidation") == "K-0001" and other.mint("K") == "K-0002"


def test_concurrent_minters_never_share_an_id(store):
    from concurrent.futures import ThreadPoolExecutor

    from hgi import registry as _registry

    registries = [_registry.load(store.root) for _ in range(8)]
    with ThreadPoolExecutor(max_workers=8) as pool:
        ids = list(pool.map(lambda r: [r.mint("S") for _ in range(5)], registries))
    flat = [i for group in ids for i in group]
    assert len(set(flat)) == 40 and store.mint("session") == "S-0041"
