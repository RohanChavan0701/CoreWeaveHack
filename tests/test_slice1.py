"""Slice 1 acceptance: one evaluation run lands as facts; a decision with a revisit watch fires when the
fact crosses over its persistence window; the fire names the backward pass; a scorer that cannot run
yields unevaluable; a fact of zero from a missing value is refused."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from hgi import evaluate as _evaluate
from hgi import index as _index
from hgi.store import now
from hgi.types import Fact, Session
from tests.conftest import NOW, adjudicated_entry, adjudicator, draft


def _admit(store):
    d = draft(store)
    entry = adjudicated_entry(store, d.uid)
    entry.verdict = "admit"
    return store.admit(d, entry, adjudicator())


def _booted(store, pass_: int, records: list[str]) -> Session:
    s = Session(id=store.mint("session"), pass_=pass_, started_at=now(), attached=True,
                considered=[{"record": r, "terms_matched": ["http-tool"], "via": "index", "guard_passed": True, "owed_act": "apply"} for r in records])
    store.write(s)
    return s


def test_evaluation_lands_as_facts(store):
    s = _booted(store, 1, [])
    s = _evaluate.run(store, s)
    facts = s.evaluation.scores
    assert set(facts) == {"task_pass_rate", "error_cause_present", "tool_budget_respected", "output_schema_valid", "suite_hash"}
    assert facts["suite_hash"].value == 1.0 and facts["task_pass_rate"].value == 0.5
    assert all(f.series.startswith("suite-v1/") and f.as_of is not None for f in facts.values())
    assert s.evaluation.suite_hash and len(s.evaluation.rows) == 6


def test_watch_fires_over_persistence_and_names_the_backward_pass(store):
    decision = _admit(store)
    s1 = _evaluate.run(store, _booted(store, 1, []))
    assert _evaluate.emit_fires(store, s1) == []  # persistence 2 needs two runs
    store.write(s1)
    s2 = _evaluate.run(store, _booted(store, 2, []))
    fires = _evaluate.emit_fires(store, s2)
    assert len(fires) == 1
    fire = fires[0]
    assert fire.latch.record == decision.id and fire.edge_event.scorer == "error_cause_present" and fire.edge_event.observed == 0.0
    assert fire.disposer == "the backward pass" and fire.disposition.act == "re-adjudicate" and not fire.disposition.discharged
    store.write(s2)
    assert [f["id"] for f in _index.undischarged_fires(store)] == [fire.id]
    s3 = _evaluate.run(store, _booted(store, 3, []))
    assert _evaluate.emit_fires(store, s3) == []  # an undischarged fire is not re-emitted


def test_unevaluable_scorer_reads_unevaluable_and_never_fires(store):
    decision = _admit(store)
    # with the retry and batch lessons in context every task passes, so error_cause_present has no evaluable row
    retry = store.parse_as(type(decision), {**decision.model_dump(by_alias=True, mode="json"),
                                            "decision": "A transient tool failure is retried once and reported with its cause; "
                                                        "under a call budget, independent calls are issued as one batched call."})
    store.write(retry)
    s = _evaluate.run(store, _booted(store, 1, [decision.id]))
    fact = s.evaluation.scores["error_cause_present"]
    assert fact.value is None and fact.unevaluable
    assert s.evaluation.scores["task_pass_rate"].value == 1.0
    store.write(s)
    s2 = _evaluate.run(store, _booted(store, 2, [decision.id]))
    assert _evaluate.emit_fires(store, s2) == []


def test_zero_from_missing_value_is_refused():
    with pytest.raises(ValidationError):
        Fact(series="suite-v1/x", value=0.0, unevaluable="scorer could not run", as_of=NOW)
    with pytest.raises(ValidationError):
        Fact(series="suite-v1/x", as_of=NOW)
    assert Fact(series="suite-v1/x", unevaluable="no rows", as_of=NOW).value is None


def test_detached_pass_records_no_context(store):
    _admit(store)
    s = _evaluate.evaluate_session(store, None, 1, detached=True)
    assert not s.attached and s.closed_at is not None and s.considered == [] and s.fires_seen == []
    assert s.evaluation.scores["task_pass_rate"].value == 0.5
