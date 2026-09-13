"""Carry-forward item 16 — a watch's direction against the decision's stakes.

A revisit latch must fire when the oracle shows the failure the stakes name —
a low score — not when the record works. The examiner flags a watch that
fires on success (`task_pass_rate == 1.0`, the case seen in a nominate try)
and the adjudicator declines it.
"""

from __future__ import annotations

import pytest

from hgi import consolidate as _consolidate
from hgi import drafting as _drafting
from hgi.store import now
from hgi.types import Consolidation
from tests.conftest import decision_body, draft


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


# --- the examiner flags, the adjudicator declines ---------------------------------------------

def _evidence(scorer: str = "task_pass_rate") -> dict:
    """Minimal evidence: the independence, premise and abstraction attacks all miss, so the watch is the only landing claim."""
    return {"observation_sessions": ["S-0001", "S-0002"], "bar_independent": 2, "fault_rate": 0.0, "task_ids": [],
            "series": {}, "scores": {}, "evaluation": "suite-v1", "watch_scorer": scorer}


def _record(store) -> Consolidation:
    return Consolidation(id=store.mint("consolidation"), started_at=now(), after_pass=2, sessions_read=["S-0001", "S-0002"])


def test_a_success_direction_watch_is_flagged_by_the_examiner_and_declined(store):
    d = draft(store, latches=_watch("==", 1.0)["latches"])
    record, evidence = _record(store), _evidence()
    attack_payload, _ = _consolidate.attack(store, record, d, evidence)
    landed = next(c for c in attack_payload["claims"] if c["target"] == "warrant:watch-direction")
    assert landed["landed"] is True and "task_pass_rate == 1.0" in landed["evidence"][0]
    v, out, _ = _consolidate.verdict(store, record, d, attack_payload, evidence)
    assert v.startswith("decline(") and "fires on success" in v


def test_a_failure_direction_watch_survives_the_direction_check(store):
    d = draft(store, latches=_watch("<", 0.7)["latches"])
    record, evidence = _record(store), _evidence()
    attack_payload, _ = _consolidate.attack(store, record, d, evidence)
    flag = next(c for c in attack_payload["claims"] if c["target"] == "warrant:watch-direction")
    assert flag["landed"] is False
    v, _, _ = _consolidate.verdict(store, record, d, attack_payload, evidence)
    assert v == "admit"
