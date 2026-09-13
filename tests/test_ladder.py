"""The ladder's rungs and their operators (spec § 10.3): a nomination at a rung this roster cannot execute is refused
and recorded, never drafted as a decision wearing the rung's name."""

from __future__ import annotations

from hgi import consolidate as _consolidate
from tests.test_slice3 import CLEAN, _session


def test_a_rung_with_no_operator_is_refused_and_recorded(store, monkeypatch):
    _session(store, 1, [CLEAN], {"task_pass_rate": 1.0})
    _session(store, 2, [CLEAN], {"task_pass_rate": 1.0})
    raws = [{"rung": rung, "rung_why": "a test", "subject": rung, "evidence": [], "supersedes": [], "sketch": {}}
            for rung in ("floor", "article", "rule-enrollment", "adoption-row")]
    monkeypatch.setattr(_consolidate, "nominate", lambda store, record, brief: raws)
    record = _consolidate.consolidate(store)
    assert store.drafts() == [] and record.admitted == []
    outcomes = {n.subject: n.outcome for n in record.nominations if n.subject in {r["rung"] for r in raws}}
    assert set(outcomes) == {"floor", "article", "rule-enrollment", "adoption-row"}
    assert all(o.startswith("refused: the rung") and "no operator" in o for o in outcomes.values())
    assert not [e for e in store.all("hypothesis") if e.species == "attack"], "nothing reached the examiner"


def test_the_operated_rungs_are_the_case_leg(store):
    assert _consolidate.unoperated("new-decision") is None and _consolidate.unoperated("hook-edit") is None
    assert _consolidate.unoperated("counterfactual-edit") is None
    assert _consolidate.unoperated("other(no rung)").startswith("refused")
