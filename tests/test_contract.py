"""``hgi roles try`` builders: every request the loop dispatches is exercisable one at a time.

``dispose`` must carry the same ``co_applying`` reading the close builds, or that content is never
read back on a real model through ``roles try``.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

from hgi import contract


class _Args:
    session = lens = draft = out = None


def test_the_priced_requests_all_have_a_builder():
    for name in ("attack", "currency", "nominate", "dispose"):
        assert name in contract.BUILDERS


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
