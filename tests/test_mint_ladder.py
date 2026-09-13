"""The mint ladder (§ 10.1, the miss stream climbing to activation): a class of off-map failure that recurs across the
independence bar of distinct sessions, and that no accepted record's hook covers, nominates new coverage — the complement
of recall, which nominates a hook-edit for a record the store already holds. A nominator, never a verdict; a single
off-map failure is one episode, two are the recurrence the bar reads."""

from __future__ import annotations

from hgi import index as _index
from hgi.store import now
from hgi.types import Consulted, Decision, Session
from tests.conftest import NOW, adjudicator, decision_body
from tests.test_slice3 import FAULTED


def _off_map(store, terms: list[str], task: str) -> Session:
    """A closed attached session that consulted nothing and failed one row — the raw off-map signal, classed by its work-shape."""
    row = {**FAULTED, "task": task}
    s = store.parse_as(Session, {"id": store.mint("session"), "pass": 1, "started_at": now().isoformat(),
                                 "closed_at": now().isoformat(), "attached": True, "work_shape": {"terms": terms, "escapes": []},
                                 "evaluation": {"evaluation": "suite-v1", "rows": [row],
                                                "scores": {"task_pass_rate": {"series": "suite-v1/task_pass_rate", "value": 0.0, "as_of": now().isoformat()}}}})
    store.write(s)
    return s


def _accepted(store) -> Decision:
    """An accepted decision hooked on http-tool / tool-call-retry — what the committer leaves, minted straight so the test needs no ledger dance."""
    d = store.parse_as(Decision, {"id": store.registry.mint("D"), "kind": "decision", "status": "accepted", "created_at": NOW.isoformat(),
                                  "lineage": {"supersedes": [], "superseded_by": [], "split_from": None, "folded_from": []},
                                  "admission": {"proposed_by": "S-0001", "ledger_entry": None, "verdict": "admit", "rung": "new-decision",
                                                "adjudicator": adjudicator().model_dump(), "committed_at": NOW.isoformat()},
                                  **decision_body()})
    store.write(d)
    return d


def test_two_off_map_sessions_on_one_class_nominate_new_coverage(store):
    s1 = _off_map(store, ["file-tool"], "read_config")
    s2 = _off_map(store, ["file-tool"], "list_dir")
    rows = _index.mint_ladder(store)
    assert len(rows) == 1
    r = rows[0]
    assert r["class"] == "file-tool" and r["distinct_sessions"] == 2 and r["reading"] == "at the bar"
    assert set(r["instances"]) == {f"{s1.id}/read_config", f"{s2.id}/list_dir"}
    assert "close lens" in r["nominates"] and "hook" in r["nominates"]


def test_a_single_off_map_failure_is_an_episode_not_a_nomination(store):
    _off_map(store, ["file-tool"], "read_config")
    assert _index.mint_ladder(store) == []


def test_two_off_map_failures_of_different_classes_neither_reaches_the_bar(store):
    _off_map(store, ["file-tool"], "read_config")
    _off_map(store, ["shell-tool"], "run_awk")
    assert _index.mint_ladder(store) == []


def test_a_class_an_accepted_hook_covers_is_recalls_not_the_ladders(store):
    accepted = _accepted(store)
    assert "http-tool" in accepted.consultation_terms  # the decision hooks on http-tool / tool-call-retry
    _off_map(store, ["http-tool"], "fetch_user_name")
    _off_map(store, ["http-tool"], "fetch_plan")
    assert _index.mint_ladder(store) == []  # the store already holds a hook for this work — recall's ground, not the ladder's


def test_a_pass_that_consulted_a_record_is_not_off_map(store):
    for task in ("read_config", "list_dir"):
        s = _off_map(store, ["file-tool"], task)
        s.consulted = [Consulted(record="D-0001")]
        store.write(s)
    assert _index.mint_ladder(store) == []
