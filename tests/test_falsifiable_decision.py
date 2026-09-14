"""Carry-forward item 49a — a propose/nominate sketch is refused when the decision sentence names no falsifiable
world-content (a value, column, dialect token, command, path or world-mechanism term). A decision with no checkable fact
about the world is an instruction, not a lesson. The check errs toward admitting: any one concrete signal passes it."""

from __future__ import annotations

import pytest

from hgi import drafting as _drafting
from hgi.drafting import names_world_content, sketch_of


def _sketch(decision: str) -> dict:
    return {
        "decision": decision,
        "counterfactual": "The overshoot is doing it everywhere — observed in O-0001.",
        "latch": "a query against a coded column",
        "terms": ["output-schema"],
        "not_this": [],
        "stakes": "the answer scores zero while the query looks right",
        "context": "seen in S-0001, S-0002",
        "options": [{"name": "A — read the code", "judged": "chosen", "why": "the column stores a code"}],
        "premises": [{"id": "p1", "statement": "the column stores a coded value", "falsifier": "a schema change to a text status"}],
        "watch": None,
        "residue": [],
        "moot_when": "the column stops storing a code",
        "scopes": [],
    }


def test_names_world_content_admits_concrete_and_rejects_vacuous(store):
    reg = store.registry
    # concrete: a quoted literal, a path, a command/identifier, an all-caps code, a registered mechanism term
    assert names_world_content("status is coded 'A' not 'approved'", reg)
    assert names_world_content("call the named /v2 route", reg)
    assert names_world_content("a date stored as text needs STRFTIME, not a range comparison", reg)
    assert names_world_content("the count uses COUNT(*) over the joined rows", reg)
    assert names_world_content("read error_cause_present off the final error", reg)
    assert names_world_content("Errors that wrap a failed tool call carry the underlying cause.", reg)  # stub lesson
    assert names_world_content("Under a call budget, independent calls are issued as one batched call.", reg)  # stub lesson
    # vacuous / self-referential: no falsifiable world-content
    assert not names_world_content("a SQL solution must correctly translate the task's logical requirements", reg)
    assert not names_world_content("correctly translate the logical requirements", reg)
    assert not names_world_content("consult the store's rules first", reg)


def test_a_concrete_sketch_is_admitted(store):
    s = sketch_of(_sketch("status is stored as the coded literal 'A', not 'approved'"), store.registry)
    assert s.decision.startswith("status is stored")


def test_a_content_free_sketch_is_refused(store):
    with pytest.raises(ValueError, match="falsifiable world-content"):
        sketch_of(_sketch("a SQL solution must correctly translate the task's logical requirements"), store.registry)


def test_the_refusal_flows_through_propose_as_a_draft_refusal(store, capsys):
    # A pass whose propose reply carries a content-free draft files nothing; the draft is refused, not raised.
    from hgi import close as _close
    from hgi import roles
    from tests.test_slice3 import FAULTED, _session
    s = _session(store, 1, [FAULTED], {"task_pass_rate": 0.5})
    raw = {"rung": "new-decision", "rung_why": "undecided", "subject": "vacuous", "evidence": ["O-0001"],
           "sketch": _sketch("the solution must be correct")}
    with pytest.raises(ValueError, match="falsifiable world-content"):
        roles.draft_of(store, raw, proposed_by=s.id, name="P-0001", model_id="stub")
