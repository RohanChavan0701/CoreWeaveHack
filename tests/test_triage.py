"""§ 10.2 — noise-filter before updating process. Every recurrence at the bar is classified reducible or irreducible by the
adjudicator before the consolidator may nominate on it; an irreducible group is dismissed with a pointer to its reality
entry and no slot updates on it."""

from __future__ import annotations

from hgi import consolidate as _consolidate
from hgi import index as _index
from hgi import lint as _lint
from tests.test_slice3 import FAULTED, NO_CAUSE, _observe, _session

HARNESS = {"task": "mbpp/430", "error": {"message": "model call failed", "cause": "endpoint APIConnectionError: read timeout"}, "applied": [],
           "tool_errors": [], "call": "weave:///t/call/harness"}
NOT_OURS = "task mbpp/430 failed because the model call failed on the endpoint (read timeout); the world was not touched"


def test_an_irreducible_recurrence_is_dismissed_before_nomination(store):
    s1 = _session(store, 1, [HARNESS], {"task_pass_rate": 0.0})
    s2 = _session(store, 2, [HARNESS], {"task_pass_rate": 0.0})
    for s in (s1, s2):
        o = _observe(store, s, NOT_OURS)
        o.anchor.call = "weave:///t/call/harness"
        store.write(o)
    record = _consolidate.consolidate(store)
    [entry] = [e for e in store.all("hypothesis") if e.species == "reality"]
    assert entry.verdict == "irreducible" and entry.adjudicator.role == "adjudicator"
    assert entry.proposer.role == "pass" and entry.contradiction.source.role == "oracle" and entry.contradiction.source.call == "weave:///t/call/harness"
    assert set(record.dismissed) == {o.name for o in store.observations(state=None)}
    assert all(o.disposition.state == "dismissed" and o.disposition.pointer == entry.id for o in store.observations(state=None))
    assert record.admitted == [] and store.drafts() == [] and record.brief["groups"] == []
    assert record.brief["triage"][0]["act"] == "dismiss"
    assert not [e for e in store.all("hypothesis") if e.species == "attack"], "nothing reached the examiner"
    _index.regenerate(store)
    assert _lint.run(store).green


def test_a_reducible_recurrence_is_routed_on_to_nomination(store):
    s1 = _session(store, 1, [FAULTED], {"task_pass_rate": 0.5, "error_cause_present": 0.0})
    s2 = _session(store, 2, [FAULTED], {"task_pass_rate": 0.5, "error_cause_present": 0.0})
    _observe(store, s1, NO_CAUSE), _observe(store, s2, NO_CAUSE)
    record = _consolidate.consolidate(store)
    [entry] = [e for e in store.all("hypothesis") if e.species == "reality"]
    assert entry.verdict == "reducible" and record.brief["triage"][0]["act"] == "route"
    assert record.admitted == ["D-0001"] and record.dismissed == []


def test_a_group_below_the_bar_is_not_triaged(store):
    s1 = _session(store, 1, [HARNESS], {"task_pass_rate": 0.0})
    _observe(store, s1, NOT_OURS)
    _session(store, 2, [HARNESS], {"task_pass_rate": 0.0})
    record = _consolidate.consolidate(store)
    assert record.brief["triage"] == [] and not [e for e in store.all("hypothesis") if e.species == "reality"]
    assert all(o.disposition.state == "open" for o in store.observations(state=None))
