"""Slice 2 acceptance: two consecutive passes run with the store attached; each session record lists its
consulted ids with dispositions; the second pass boots from the first's carry-forward and sees its
undischarged fires; a close with a missing disposition is refused."""

from __future__ import annotations

import pytest

from hgi import boot as _boot
from hgi import close as _close
from hgi import evaluate as _evaluate
from hgi import index as _index
from hgi import lint as _lint
from hgi.types import Fire
from tests.conftest import adjudicated_entry, adjudicator, draft


def _admit(store):
    d = draft(store)
    entry = adjudicated_entry(store, d.uid)
    entry.verdict = "admit"
    decision = store.admit(d, entry, adjudicator())
    _index.regenerate(store)
    return decision


def _pass(store, n: int):
    s = _boot.boot(store, None, n)
    _evaluate.evaluate_session(store, s.id, None, detached=False)
    _index.regenerate(store)
    return _close.close(store, s.id)


def test_two_passes_chain_through_the_store(store, capsys):
    decision = _admit(store)
    s1 = _pass(store, 1)
    assert s1.closed_at is not None
    assert [c.record for c in s1.consulted] == [decision.id]
    assert all(c.disposition and c.disposition.startswith("U-") for c in s1.consulted)
    assert s1.work_shape.terms and "http-tool" in s1.work_shape.terms
    assert s1.observations_filed, "the close lens files the naive agent's uncaused failures as observations"
    assert s1.carry_forward.startswith("pass 1 scored")
    _index.regenerate(store)
    assert _lint.run(store).green

    s2 = _pass(store, 2)
    out = capsys.readouterr().out
    assert f"carry-forward: {s1.carry_forward}" in out
    assert [c.record for c in s2.consulted] == [decision.id]
    dispositions = {u.id: u for u in store.all("disposition")}
    assert dispositions[s2.consulted[0].disposition].disposition == "applied"  # the cause lesson bore on the faulted tasks
    assert s2.observations_filed and {o.session for o in store.observations()} == {s1.id, s2.id}
    _index.regenerate(store)
    assert _lint.run(store).green


def test_second_boot_sees_undischarged_fires_owed_to_the_working_pass(store, capsys):
    decision = _admit(store)
    s1 = _pass(store, 1)
    fire = Fire(id=store.mint("fire"), fired_at=s1.closed_at, latch={"record": decision.id, "index": 0},
                edge_event={"evaluation": "suite-v1", "pass": 1, "scorer": "task_pass_rate", "observed": 0.5},
                guard_result=True, disposer=_boot.WORKING_PASS, disposition={"act": "check"})
    store.write(fire)
    _index.regenerate(store)
    s2 = _boot.boot(store, None, 2)
    out = capsys.readouterr().out
    assert fire.id in s2.fires_seen and f"fires owed to the working pass: 1 {fire.id}" in out


def test_close_refuses_a_missing_disposition(store, monkeypatch):
    _admit(store)
    s = _boot.boot(store, None, 1)
    _evaluate.evaluate_session(store, s.id, None, detached=False)
    from hgi import stub
    monkeypatch.setitem(stub.HANDLERS, "dispose", lambda req: {"dispositions": []})
    with pytest.raises(SystemExit, match="disposition-completeness"):
        _close.close(store, s.id)
    assert store.read("session", s.id).closed_at is None


def test_close_before_evaluate_is_refused(store):
    s = _boot.boot(store, None, 1)
    with pytest.raises(SystemExit, match="not been evaluated"):
        _close.close(store, s.id)


def test_a_fire_owed_to_the_working_pass_is_discharged_at_close_or_the_close_is_refused(store, monkeypatch):
    decision = _admit(store)
    s1 = _pass(store, 1)
    fire = Fire(id=store.mint("fire"), fired_at=s1.closed_at, latch={"record": decision.id, "index": 0},
                edge_event={"evaluation": "suite-v1", "pass": 1, "scorer": "task_pass_rate", "observed": 0.5},
                guard_result=True, disposer=_boot.WORKING_PASS, disposition={"act": "check"})
    store.write(fire)
    _index.regenerate(store)
    s2 = _boot.boot(store, None, 2)
    _evaluate.evaluate_session(store, s2.id, None, detached=False)
    _index.regenerate(store)
    from hgi import stub
    honest = stub.HANDLERS["dispose"]
    monkeypatch.setitem(stub.HANDLERS, "dispose", lambda req: {**honest(req), "fires": []})
    with pytest.raises(SystemExit, match=f"fire-completeness.*{fire.id}"):
        _close.close(store, s2.id)
    assert store.read("session", s2.id).closed_at is None and not store.read("fire", fire.id).disposition.discharged
    monkeypatch.setitem(stub.HANDLERS, "dispose", honest)
    closed = _close.close(store, s2.id)
    discharged = store.read("fire", fire.id)
    assert discharged.disposition.discharged and discharged.disposition.by == closed.id and discharged.disposition.outcome.startswith("check: ")
    assert _index.undischarged_fires(store) == []
    _index.regenerate(store)
    assert _lint.run(store).green


def test_the_lint_refuses_a_closed_session_that_left_its_fire_undischarged(store):
    decision = _admit(store)
    s1 = _pass(store, 1)
    fire = Fire(id=store.mint("fire"), fired_at=s1.closed_at, latch={"record": decision.id, "index": 0},
                edge_event={"evaluation": "suite-v1", "pass": 1, "scorer": "task_pass_rate", "observed": 0.5},
                guard_result=True, disposer=_boot.WORKING_PASS, disposition={"act": "check"})
    store.write(fire)
    s1.fires_seen.append(fire.id)
    store.write(s1)
    findings = [f for f in _lint.run(store, seams=("close",)).failures if f.check == "fire-completeness"]
    assert [f.record for f in findings] == [s1.id] and fire.id in findings[0].message
