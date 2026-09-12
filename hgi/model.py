"""The frozen model, priced.

One client serves every role — the pass, the consolidator, the examiner, the
adjudicator, the coder — and each role runs in its own context: a fresh
``complete`` call with the role's prompt as the system message and nothing
shared but the store's schemas. Independence is structural, not instructed.

Backends:

- :class:`OpenAICompatible` — the CoreWeave inference endpoint (or any
  OpenAI-compatible server), configured by ``$HGI_INFERENCE_BASE_URL``,
  ``$HGI_INFERENCE_API_KEY`` and ``$HGI_MODEL_ID``.
- :class:`Stub` — a deterministic answerer used when no endpoint is
  configured. It classifies work-shape lexically, answers every lens with the
  empty finding, and attacks and adjudicates by fixed rules stated in its
  methods. It exists so the loop's mechanics run and are testable offline; it
  is not evidence that a model learned anything.

Every call records its model id; every lens and decision records the model
it was priced for, and the lint warns on a mismatch at boot.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any

import weave

from hgi import tracing
from hgi.roles import prompt as role_prompt


@dataclass
class Completion:
    text: str
    model_id: str
    call: str | None
    """The Weave call URI, joinable from ledger entries and admission stamps."""

    def json(self) -> Any:
        """Parse the completion as JSON, tolerating a fenced block around it."""
        text = self.text.strip()
        m = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
        if m:
            text = m.group(1).strip()
        return json.loads(text)


class Backend:
    model_id: str

    def chat(self, messages: list[dict[str, Any]], *, json_mode: bool, tools: list[dict] | None = None) -> dict[str, Any]:
        raise NotImplementedError


class OpenAICompatible(Backend):
    def __init__(self, base_url: str, api_key: str, model_id: str):
        from openai import OpenAI

        self.client = OpenAI(base_url=base_url, api_key=api_key)
        self.model_id = model_id

    def chat(self, messages, *, json_mode, tools=None):
        kwargs: dict[str, Any] = {"model": self.model_id, "messages": messages, "temperature": 0}
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        if tools:
            kwargs["tools"] = tools
        resp = self.client.chat.completions.create(**kwargs)
        msg = resp.choices[0].message
        return {"content": msg.content or "", "tool_calls": [
            {"id": tc.id, "name": tc.function.name, "arguments": tc.function.arguments} for tc in (msg.tool_calls or [])
        ]}


class Stub(Backend):
    """Deterministic answers, keyed on the role in the system prompt. See :mod:`hgi.stub` for the rules."""

    model_id = "stub"

    def chat(self, messages, *, json_mode, tools=None):
        from hgi.stub import answer

        return {"content": answer(messages, tools), "tool_calls": []}


_backend: Backend | None = None


def backend() -> Backend:
    global _backend
    if _backend is None:
        base_url = os.environ.get("HGI_INFERENCE_BASE_URL")
        if base_url and os.environ.get("HGI_MODEL_ID"):
            _backend = OpenAICompatible(base_url, os.environ.get("HGI_INFERENCE_API_KEY", "none"), os.environ["HGI_MODEL_ID"])
        else:
            _backend = Stub()
    return _backend


def use(b: Backend | None) -> None:
    global _backend
    _backend = b


def model_id() -> str:
    return backend().model_id


@weave.op(name="hgi.complete")
def _complete(role: str, system: str, user: str, json_mode: bool) -> dict[str, Any]:
    return backend().chat([{"role": "system", "system_role": role, "content": system}, {"role": "user", "content": user}], json_mode=json_mode)


def complete(role: str, user: str, *, json_mode: bool = True, session: str | None = None, pass_: int | None = None,
             records_in_context: list[str] | None = None) -> Completion:
    """One fresh context for ``role``: its prompt file as the system message, ``user`` as the whole conversation."""
    system = role_prompt(role)
    with tracing.attributes(session=session, pass_=pass_, role=role, records_in_context=records_in_context):
        result, call = _complete.call(role, system, user, json_mode)
    return Completion(text=result["content"], model_id=backend().model_id, call=tracing.call_uri(call))


def chat_with_tools(role: str, messages: list[dict[str, Any]], tools: list[dict], *, session: str | None = None,
                    pass_: int | None = None, records_in_context: list[str] | None = None) -> tuple[dict[str, Any], str | None]:
    """One turn of a tool-using conversation for the agent under test; returns (message, call uri)."""
    with tracing.attributes(session=session, pass_=pass_, role=role, records_in_context=records_in_context):
        result, call = _turn.call(role, messages, tools)
    return result, tracing.call_uri(call)


@weave.op(name="hgi.turn")
def _turn(role: str, messages: list[dict[str, Any]], tools: list[dict]) -> dict[str, Any]:
    return backend().chat(messages, json_mode=False, tools=tools)
