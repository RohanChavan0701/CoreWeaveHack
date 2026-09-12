"""Shared fixtures: a fresh seeded store per test, and hand-authored bodies that satisfy the contract."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from hgi import registry as _registry
from hgi.genesis import seed
from hgi.store import Store
from hgi.types import Draft, LedgerEntry, RoleCall

NOW = datetime(2026, 9, 12, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
def store(tmp_path) -> Store:
    root = tmp_path / "store"
    reg = seed(root, model_id="stub", now=NOW)
    token = _registry.use(reg)
    yield Store(root, registry=reg)
    _registry.reset(token)


def decision_body(**overrides) -> dict:
    """A decision body satisfying every slot of the entry contract; override fields to break it deliberately."""
    body = {
        "scopes": ["tools/http"],
        "summary": {
            "latch": "a tool call that can time out; a retry wrapper; an HTTP client in the tool layer",
            "not_this": ["a retry inside the model's own reasoning loop"],
            "stakes": "a silent retry hides the cause the oracle scores on",
        },
        "context": "the http tool's retry wrapper dropped the 502 body on rethrow in two independent passes",
        "options": [
            {"name": "A — retry with cause preserved", "judged": "chosen", "why": "the scorer reads the final error"},
            {"name": "B — retry and swallow", "judged": "rejected", "why": "hides the cause"},
        ],
        "decision": "A wrapper that retries a tool call carries the underlying cause on every rethrow.",
        "counterfactual": "The overshoot is a wrapper that carries the cause but never retries — observed in O-0001.",
        "warrant": {
            "anchors": ["O-0001", "O-0002"],
            "premises": [
                {"id": "p1", "statement": "the oracle's scorer reads the final error message",
                 "falsifier": "a scorer change that grades on exit code only", "status": "supported"},
            ],
            "adjudication": {"ledger_entry": None, "species": "attack", "verdict": "pending"},
        },
        "latches": [
            {"type": "consultation", "slot": "payload", "key_space": "work-shape",
             "edge": {"kind": "level", "at": "boot"},
             "guard": {"terms": ["tool-call-retry", "http-tool"], "not_this": ["reasoning-loop-retry"]},
             "consumer": "the working pass", "owed_act": {"class": "apply", "role": "dispositive"},
             "lifecycle": {"status": "live"}},
            {"type": "revisit", "slot": "warrant", "key_space": "world-state",
             "edge": {"kind": "edge", "predicate": {"evaluation": "suite-v1", "scorer": "error_cause_present",
                                                    "comparator": "<", "value": 0.5, "persistence": 2}},
             "guard": {}, "consumer": "the backward pass",
             "owed_act": {"class": "re-adjudicate", "role": "dispositive"}, "lifecycle": {"status": "live"}},
        ],
        "enforcement": {"floor": ["schema", "complement-law"], "residue": ["whether the retry policy is right is judgment"]},
        "lifecycle": {
            "consumer": "the working pass, at boot, on a matching work-shape",
            "moot_when": "the tool layer stops exposing retryable calls",
            "retirement": {"type": "retirement", "slot": "lifecycle", "key_space": "competence",
                           "edge": {"kind": "schedule", "at": "consolidation"},
                           "guard": {"applied_over_considered_below": 0.1, "over_passes": 6},
                           "consumer": "the lifecycle review", "owed_act": {"class": "retire", "role": "corroborating"},
                           "lifecycle": {"status": "live"}},
        },
        "priced_for": {"model_id": "stub"},
    }
    body.update(overrides)
    return body


def draft(store: Store, name: str = "D-draft", **overrides) -> Draft:
    return store.parse_as(Draft, {
        "uid": store.new_uid(), "name": name, "kind": "decision", "drafted_at": NOW.isoformat(),
        "proposed_by": "S-0001", "rung": "new-decision",
        "rung_why": "no existing record's counterfactual, hook or register absorbs the fork",
        "body": decision_body(**overrides), "evidence": ["O-0001", "O-0002"],
    })


def adjudicated_entry(store: Store, subject: str, verdict: str = "admit") -> LedgerEntry:
    """A ledger entry as the adjudicator leaves it: the attack pending inside, the verdict stamped with the adjudicator's call."""
    return store.parse_as(LedgerEntry, {
        "id": store.mint("hypothesis"), "kind": "hypothesis", "at": NOW.isoformat(), "species": "attack",
        "subject": subject, "claim": "errors that wrap carry their cause",
        "proposer": {"role": "consolidator", "model_id": "stub", "call": "weave:///t/call/proposer"},
        "contradiction": {"source": {"role": "examiner", "model_id": "stub", "call": "weave:///t/call/examiner"},
                          "attack": {"claims": [{"target": "premise:p1", "refutation": "the scorer reads the exit code",
                                                 "reading_taken": True, "landed": False, "evidence": ["weave:///t/eval/1"]}]}},
        "verdict": "survived-with-attack-named",
        "adjudicator": {"role": "adjudicator", "model_id": "stub", "call": "weave:///t/call/adjudicator"},
        "outcome": None,
    }) if verdict == "admit" else None


def adjudicator() -> RoleCall:
    return RoleCall(role="adjudicator", model_id="stub", call="weave:///t/call/adjudicator")
