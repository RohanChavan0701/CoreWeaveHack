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
