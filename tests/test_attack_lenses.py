"""The examiner fan (spec § 8.3, the fan law and the host law): the attack's angles are examiner-hosted lenses, each walked
in its own context and contributing only the claims of its own class; a register with no examiner lens falls back to the
single-context attack."""

from __future__ import annotations

import json

from hgi import consolidate as _consolidate
from hgi import model as _model
from hgi.registry import read_json, write_json
from hgi.store import now
from hgi.types import MECHANICAL, Consolidation
from tests.conftest import draft
from tests.test_watch_direction import _evidence, _watch


def _calls(monkeypatch):
    seen = []
    real = _model.complete

    def spy(role, payload, **kw):
        seen.append((role, json.loads(payload)))
        return real(role, payload, **kw)

    monkeypatch.setattr(_model, "complete", spy)
    return seen


def test_each_examiner_lens_is_walked_in_its_own_context_and_owns_its_claims(store, monkeypatch):
    seen = _calls(monkeypatch)
    d = draft(store, latches=_watch("==", 1.0)["latches"])
    record = Consolidation(id=store.mint("consolidation"), started_at=now(), after_pass=2, sessions_read=[])
    payload, first = _consolidate.attack(store, record, d, _evidence())
    lenses = store.registry.lenses("examiner")
    assert [l.id for l in lenses] == ["L-0006", "L-0007"], "independence and watch direction crystallized into the code and are walked by nothing"
    walked = [(role, req["lens"]["id"]) for role, req in seen if req.get("request") == "attack"]
    assert walked == [("examiner", l.id) for l in lenses], "one call per angle, every angle in the examiner's context"
    by_lens = {}
    for c in payload["claims"]:
        by_lens.setdefault(c["lens"], []).append(c["target"])
        lens = next(l for l in lenses if l.id == c["lens"])
        assert any(c["target"].startswith(p) for p in lens.claims), "a claim carries only its own angle's class"
    assert by_lens == {"L-0006": ["premise:p1"], "L-0007": ["payload:abstraction"]}
    assert payload["verdict"] == "pending" and first is not None


def test_a_register_with_no_examiner_lens_attacks_in_one_context(store, monkeypatch):
    path = store.registry.path("lenses")
    write_json(path, [l for l in read_json(path) if l["host"] != "examiner"])
    seen = _calls(monkeypatch)
    d = draft(store)
    record = Consolidation(id=store.mint("consolidation"), started_at=now(), after_pass=2, sessions_read=[])
    payload, _ = _consolidate.attack(store, record, d, _evidence())
    assert [req.get("lens") for role, req in seen if req.get("request") == "attack"] == [None]
    assert {c["target"] for c in payload["claims"]} == {"premise:p1", "payload:abstraction"}
    assert all(c.get("lens") is None for c in payload["claims"])


def test_the_fan_lands_on_the_ledger_with_the_angle_named(store):
    from tests.test_slice3 import FAULTED, NO_CAUSE, _observe, _session
    s1 = _session(store, 1, [FAULTED], {"task_pass_rate": 0.5, "error_cause_present": 0.0})
    s2 = _session(store, 2, [FAULTED], {"task_pass_rate": 0.5, "error_cause_present": 0.0})
    _observe(store, s1, NO_CAUSE), _observe(store, s2, NO_CAUSE)
    record = _consolidate.consolidate(store)
    assert record.admitted == ["D-0001"]
    entry = next(e for e in store.all("hypothesis") if e.species == "attack")
    assert {c.lens for c in entry.contradiction.attack.claims if c.lens} == {"L-0006", "L-0007"}
    assert [c.target for c in entry.contradiction.attack.claims if c.lens is None] == list(MECHANICAL), "the code's readings join first, with no lens and no call"
