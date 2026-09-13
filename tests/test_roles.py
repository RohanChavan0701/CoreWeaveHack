"""The request contract: every role request states its reply shape, and every prompt carries the rule to answer in it."""

from __future__ import annotations

import json

import pytest

from hgi import roles


def test_a_request_carries_its_name_its_content_and_its_reply_shape():
    payload = json.loads(roles.request("classify", presentations=[{"task": "t", "prompt": "GET /x"}], terms=["http-tool"]))
    assert payload["request"] == "classify" and payload["terms"] == ["http-tool"]
    assert set(payload["reply"]) == {"terms", "escapes"}


def test_an_unknown_request_has_no_shape_and_is_refused():
    with pytest.raises(KeyError, match="no reply shape"):
        roles.request("oracle")


def test_every_role_prompt_states_the_reply_rule_and_the_shapes_it_reads():
    for role in roles.ROLES:
        text = roles.prompt(role)
        assert roles.REPLY_RULE in text and ("## Record shapes" in text) == bool(roles.role_models(role))


def test_the_reply_shapes_cover_every_request_the_stub_answers():
    from hgi.stub import HANDLERS

    assert set(HANDLERS) - {"free"} == set(roles.REPLIES)


def test_a_reply_wrapper_and_a_stringified_sketch_are_read(store):
    from hgi.model import Completion
    from hgi.stub import sketch

    assert Completion('{"reply": {"nominations": []}}', "m", None).json() == {"nominations": []}
    assert Completion('{"reply": 1, "other": 2}', "m", None).json() == {"reply": 1, "other": 2}
    raw = {"rung": "new-decision", "rung_why": "the fork is undecided", "subject": "cause", "evidence": ["O-0001"], "sketch": json.dumps(sketch("cause", ["http-tool"], ["O-0001"]))}
    draft = roles.draft_of(store, raw, proposed_by="K-0001", name="P-0001", model_id="stub")
    assert draft.body.decision.startswith("Errors that wrap") and draft.body.latches[0].guard.terms == ["http-tool"] and draft.body.priced_for.model_id == "stub"
    assert draft.body.lifecycle.retirement.guard.over_passes == store.registry.bars["retirement"]["window_passes"]
    with pytest.raises(ValueError, match="sketch"):
        roles.draft_of(store, {"rung": "new-decision"}, proposed_by="K-0001", name="P-0002", model_id="stub")


def test_a_sketch_missing_its_judgment_is_refused_field_by_field(store):
    from hgi.drafting import sketch_of

    with pytest.raises(ValueError) as e:
        sketch_of({"decision": "x", "terms": [], "not_this": []}, store.registry)
    text = roles.refusal(e.value)
    # not_this is no longer a floor field — an empty one is allowed, and precision review grows it (fix A).
    assert "terms" in text and "counterfactual" in text and "premises" in text and "not_this" not in text


def test_each_role_receives_only_the_shapes_it_reads():
    assert "Sketch" in roles.schemas("consolidator") and "DecisionBody" not in roles.schemas("consolidator")
    assert "Draft" in roles.schemas("examiner") and "LedgerEntry" in roles.schemas("adjudicator")
    assert roles.schemas("coder") == ""


def test_the_schemas_keep_their_nested_definitions():
    assert '"$defs"' in roles.schemas("examiner") and "DecisionBody" in roles.schemas("examiner")


def test_only_objects_count_as_drafts_and_no_placeholder_sits_inside_a_list():
    assert roles.drafts_in({"nominations": ["<a copied placeholder>", {"rung": "new-decision"}]}, "nominations") == [{"rung": "new-decision"}]
    assert roles.drafts_in("not an object", "drafts") == []

    def lists(x):
        if isinstance(x, dict):
            for v in x.values():
                yield from lists(v)
        elif isinstance(x, list):
            yield x
            for v in x:
                yield from lists(v)

    for name, shape in roles.REPLIES.items():
        for items in lists(shape):
            assert not (len(items) > 1 and any(isinstance(i, str) for i in items) and any(isinstance(i, dict) for i in items)), name


def test_a_refusal_names_every_failing_field(store):
    from hgi.types import Draft

    try:
        store.parse_as(Draft, {"uid": "u", "name": "P-x", "drafted_at": "2026-09-12T00:00:00Z", "proposed_by": "K-1", "rung": "sideways", "rung_why": "", "body": {}})
    except ValueError as e:
        text = roles.refusal(e)
    assert "rung: 'sideways' is not in the closed vocabulary" in text and "body" in text
