"""Carry-forward item 16 — a watch's direction against the decision's stakes.

A revisit latch must fire when the oracle shows the failure the stakes name —
a low score — not when the record works. The code reads the direction before
any context opens: a watch that fires on success (`task_pass_rate == 1.0`, the
case seen in a nominate try) is dropped from the draft — the watch is
optional, the draft is not — and the claim lands on the ledger with the drop
as its evidence.
"""

from __future__ import annotations

import json

import pytest

from hgi import consolidate as _consolidate
from hgi import drafting as _drafting
from hgi import model as _model
from hgi.store import now
from hgi.types import Consolidation, Nomination
from tests.conftest import decision_body, draft
from tests.test_slice3 import FAULTED, NO_CAUSE, _observe, _session


def _watch(comparator: str, value: float) -> dict:
    """A decision body whose revisit watch is on ``task_pass_rate`` with the given direction."""
    body = decision_body()
    for latch in body["latches"]:
        if latch["type"] == "revisit":
            latch["edge"]["predicate"] = {"evaluation": "suite-v1", "scorer": "task_pass_rate",
                                          "comparator": comparator, "value": value, "persistence": 2}
    return body


# --- the pure direction rule ------------------------------------------------------------------

@pytest.mark.parametrize("comparator,value,on_success", [
    ("==", 1.0, True),   # the nominate-try case: fires only when the record is perfect
    (">=", 0.9, True),   # fires on a high score, silent on a regression
    (">", 0.8, True),
    ("<", 0.7, False),   # fires when the score falls: the stakes' failure
    ("<=", 0.5, False),
    ("!=", 1.0, False),  # fires on any imperfection — still catches the regression
    (">=", 0.0, False),  # fires always, the regression included
    ("==", 0.0, False),  # fires only on total failure
])
def test_fires_on_success_classifies_direction(comparator, value, on_success):
    assert _drafting.fires_on_success(comparator, value) is on_success


def test_revisit_watch_reads_the_world_state_latch_off_a_body():
    body = _watch("==", 1.0)
    assert _drafting.revisit_watch(body)["comparator"] == "=="
    # a body whose only latch is the consultation hook exposes no watch
    body["latches"] = [l for l in body["latches"] if l["type"] != "revisit"]
    assert _drafting.revisit_watch(body) is None


# --- the code drops a success-direction watch; the adjudicator never sees it ------------------

def _evidence(scorer: str = "task_pass_rate") -> dict:
    """Minimal evidence for a direct attack: two independent sessions, no transient fault, no task id to copy."""
    return {"observation_sessions": ["S-0001", "S-0002"], "bar_independent": 2, "fault_rate": 0.0, "task_ids": [],
            "series": {}, "scores": {}, "evaluation": "suite-v1", "watch_scorer": scorer}


def _record(store) -> Consolidation:
    return Consolidation(id=store.mint("consolidation"), started_at=now(), after_pass=2, sessions_read=["S-0001", "S-0002"])


def _anchored(store, comparator: str, value: float):
    """A draft with the given watch, resting on observations from two sessions, and the nomination that carries it."""
    s1 = _session(store, 1, [FAULTED], {"task_pass_rate": 0.5, "error_cause_present": 0.0})
    s2 = _session(store, 2, [FAULTED], {"task_pass_rate": 0.5, "error_cause_present": 0.0})
    o1, o2 = _observe(store, s1, NO_CAUSE), _observe(store, s2, NO_CAUSE)
    d = draft(store, latches=_watch(comparator, value)["latches"])
    d = d.model_copy(update={"evidence": [o1.name, o2.name]})
    store.write_draft(d)
    return d, Nomination(rung="new-decision", rung_why="a test", subject="cause", evidence=[o1.name, o2.name], draft=d.uid)


def _drafts_attacked(monkeypatch):
    seen = []
    real = _model.complete

    def spy(role, payload, **kw):
        req = json.loads(payload)
        if req.get("request") == "attack":
            seen.append(req["draft"])
        return real(role, payload, **kw)

    monkeypatch.setattr(_model, "complete", spy)
    return seen


def test_a_success_direction_watch_is_dropped_before_the_attack_and_the_draft_admitted_unwatched(store, monkeypatch):
    attacked = _drafts_attacked(monkeypatch)
    d, nomination = _anchored(store, "==", 1.0)
    entry = _consolidate.adjudicate(store, _record(store), nomination, d, {"scores": {}})
    assert entry.outcome == "admitted D-0001" and entry.verdict == "survived-with-attack-named"
    claim = next(c for c in entry.contradiction.attack.claims if c.target == "warrant:watch-direction")
    assert claim.landed is True and claim.lens is None and claim.call is None
    assert claim.evidence[0] == "task_pass_rate == 1.0 fires on success" and "dropped" in claim.evidence[1]
    assert attacked and all(_drafting.revisit_watch(x["body"]) is None for x in attacked), "the examiner read the draft without its watch"
    admitted = store.read("decision", "D-0001").body().model_dump(by_alias=True, mode="json")
    assert _drafting.revisit_watch(admitted) is None and [l["type"] for l in admitted["latches"]] == ["consultation"]


def test_a_failure_direction_watch_is_kept_and_the_claim_does_not_land(store):
    d, nomination = _anchored(store, "<", 0.7)
    entry = _consolidate.adjudicate(store, _record(store), nomination, d, {"scores": {}})
    assert entry.outcome == "admitted D-0001"
    claim = next(c for c in entry.contradiction.attack.claims if c.target == "warrant:watch-direction")
    assert claim.landed is False and claim.evidence == ["task_pass_rate < 0.7 fires on the failure"]
    assert _drafting.revisit_watch(store.read("decision", "D-0001").body().model_dump(by_alias=True, mode="json"))["comparator"] == "<"


def test_the_attack_carries_no_watch_direction_angle_and_the_stub_examiner_answers_none(store):
    d = draft(store, latches=_watch("==", 1.0)["latches"])
    attack_payload, _ = _consolidate.attack(store, _record(store), d, _evidence())
    assert not any(c["target"] == "warrant:watch-direction" for c in attack_payload["claims"])
    v, _, _ = _consolidate.verdict(store, _record(store), d, attack_payload, _evidence())
    assert v == "admit"
