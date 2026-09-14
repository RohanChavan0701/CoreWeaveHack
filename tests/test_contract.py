"""``hgi roles try`` builders: every request the loop dispatches is exercisable one at a time.

The two miss-stream requests — the noise filter ``triage`` and the port-miss ``ports`` — reach a role
in the loop but had no builder, so they could not be priced through ``roles try``; and ``dispose`` must
carry the same ``co_applying`` reading the close builds, or that content is never read back on a real model.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

from hgi import contract


class _Args:
    session = lens = draft = out = None


def test_the_miss_stream_requests_and_the_priced_requests_all_have_a_builder():
    for name in ("triage", "ports", "attack", "currency", "nominate", "dispose"):
        assert name in contract.BUILDERS


def test_triage_builds_the_noise_filter_over_the_group_with_the_most_sessions(store, monkeypatch):
    brief = {"groups": [{"shape": ["a"], "sessions": ["S-0001"]},
                        {"shape": ["shell-tool"], "sessions": ["S-0001", "S-0002", "S-0003"]}]}
    monkeypatch.setattr(contract, "_brief", lambda s: (None, brief, None))
    monkeypatch.setattr(contract._consolidate, "group_evidence", lambda s, g: {"observations": [{"name": "O-0001"}], "rows": [{"task": "t"}], "anchors": []})
    role, payload = contract.BUILDERS["triage"](store, _Args())
    p = json.loads(payload)
    assert role == "adjudicator" and p["request"] == "triage"
    assert p["shape"] == ["shell-tool"] and p["observations"] and p["rows"]
    assert p["vocabulary"] == store.registry.terms("reality-verdict")


def test_ports_builds_from_the_off_declaration_cluster_over_the_most_records(store, monkeypatch):
    clusters = [{"kind": "decision", "status": "superseded", "latch_type": "consultation", "records": ["D-1"], "occasions": [{"record": "D-1"}]},
                {"kind": "decision", "status": "superseded", "latch_type": "revisit", "records": ["D-2", "D-3"], "occasions": [{"record": "D-2"}, {"record": "D-3"}]}]
    monkeypatch.setattr(contract._reviews, "port_clusters", lambda s: clusters)
    role, payload = contract.BUILDERS["ports"](store, _Args())
    p = json.loads(payload)
    assert role == "adjudicator" and p["request"] == "ports"
    assert p["latch_type"] == "revisit" and p["mark"] == "forbidden" and len(p["occasions"]) == 2


def test_dispose_carries_the_co_applying_reading_and_the_fires_owed(store, monkeypatch):
    session = SimpleNamespace(id="S-0001", consulted=[SimpleNamespace(record="D-1")], evaluation=SimpleNamespace(rows=[]))
    monkeypatch.setattr(contract, "_session", lambda s, a: session)
    monkeypatch.setattr(contract._close, "_decision_view", lambda s, r: {"record": r})
    monkeypatch.setattr(contract._close, "fires_owed", lambda s, sess: [])
    monkeypatch.setattr(contract._boot, "co_applying", lambda s, records: [["D-1", "D-2"]])
    role, payload = contract.BUILDERS["dispose"](store, _Args())
    p = json.loads(payload)
    assert role == "pass"
    assert p["co_applying"] == [{"records": ["D-1", "D-2"], "reading": contract._boot.CO_APPLYING}]
    assert p["fires_owed"] == []
