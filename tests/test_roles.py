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


def test_every_role_prompt_states_the_reply_rule_and_the_schemas():
    for role in roles.ROLES:
        text = roles.prompt(role)
        assert roles.REPLY_RULE in text and "## Record shapes" in text


def test_the_reply_shapes_cover_every_request_the_stub_answers():
    from hgi.stub import HANDLERS

    assert set(HANDLERS) - {"free"} == set(roles.REPLIES)


def test_a_reply_wrapper_and_a_stringified_body_are_read():
    from hgi.model import Completion

    assert Completion('{"reply": {"nominations": []}}', "m", None).json() == {"nominations": []}
    assert Completion('{"reply": 1, "other": 2}', "m", None).json() == {"reply": 1, "other": 2}
    assert roles.body_of({"body": '{"decision": "x"}'}) == {"decision": "x"} and roles.body_of({"body": {"decision": "x"}}) == {"decision": "x"}
    assert roles.body_of({}) == {}


def test_the_schemas_keep_their_nested_definitions():
    assert '"$defs"' in roles.schemas() and "DecisionBody" in roles.schemas()


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
