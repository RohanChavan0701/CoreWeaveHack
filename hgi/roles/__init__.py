"""The role prompts, one file each, each priced; and the request contract.

A prompt file is Markdown with a leading ``priced_for:`` line naming the
model it was authored against. ``prompt(role)`` returns the body; the four
contexts of the backward pass share no prompt text beyond the store's
schemas, which every role receives through :func:`schemas`.

Every request a role receives is one JSON object built by :func:`request`:
its ``request`` field names the request, its ``reply`` field states the
exact shape of the answer (:data:`REPLIES`, one entry per request), and the
rest is the request's content. The reply shape travels with the request
rather than living in the prompt, so a model that has never seen the code
answers in the shape the code reads, and the stub — which answers by the
``request`` field — is the same contract by example.
"""

from __future__ import annotations

import json
from functools import cache
from pathlib import Path
from typing import Any

HERE = Path(__file__).parent

ROLES = ("pass", "consolidator", "examiner", "adjudicator", "coder")

_DRAFT_BODY = ("<a JSON object, not a string: the Draft schema's `body` (DecisionBody) with every required field in the type the schema gives it, "
               "latches as latch objects, options as {name, judged, why} objects, premises as {id, statement, falsifier, status} objects; every field the "
               "schema names as a vocabulary term (latch type, slot, key_space, edge kind, owed_act class and role, premise status, latch status) takes a "
               "term listed under that vocabulary in the request's `vocabularies`, and a consultation latch's guard.terms are work-shape terms; "
               "priced_for.model_id = the request's model_id>")

REPLIES: dict[str, Any] = {
    "classify": {"terms": ["<a term from `terms` that at least one presentation's prompt plainly instantiates; the union over all tasks; a term that merely might apply is left out>"],
                 "escapes": ["other(<a shape a presentation has and the vocabulary lacks>)"]},
    "guard": {"passed": "<true if the hook's terms match the work-shape and no `not_this` applies to the presentations>", "why": "<one sentence>"},
    "lens": {"answer": "<one sentence answering the lens's angle from the subject; empty string when nothing is found>",
             "findings": ["<one object per finding, with exactly the fields the lens's `product` names; an anchor is {call: <a row's `call` URI>, path: <a file path>}; empty list is a legal answer>"]},
    "dispose": {"dispositions": [{"record": "<a consulted record id>", "disposition": "<applied | considered-not-applicable | fired-off-map>",
                                  "note": "<which rows it bore on, or why it did not>"}],
                "fires": [{"fire": "<a fire id from `fires_owed`>", "outcome": "<what the pass did about the owed act, read from the rows; one sentence>"}]},
    "propose": {"drafts": [{"kind": "decision", "rung": "<a ladder rung from `rungs`>", "rung_why": "<why the cheaper rungs do not suffice>",
                            "evidence": ["<observation names from `observations`>"], "supersedes": [], "body": _DRAFT_BODY}]},
    "coding": {"<observation name>": ["<work-shape term or other(<what>)>"]},
    "nominate": {"nominations": [{"rung": "<a ladder rung from `rungs`>", "rung_why": "<why the cheaper rungs do not suffice>", "subject": "<one word naming the lesson>",
                                  "evidence": ["<observation names from the brief's groups>"], "supersedes": ["<accepted decision ids this retires>"],
                                  "split_from": "<the fused accepted decision this draft is one leaf of (a row of the brief's `fusion`), or null>",
                                  "folded_from": ["<the accepted decisions whose payloads this draft contracts into one (a row of the brief's `convergence`); empty unless folding>"],
                                  "edit": {"terms": ["<for hook-edit: the registered work-shape terms the successor's consultation hook keys on>"],
                                           "not_this": ["<for hook-edit or counterfactual-edit: the successor's exclusions>"],
                                           "counterfactual": "<for counterfactual-edit: the successor's counterfactual, anchored; else null>"},
                                  "body": _DRAFT_BODY + " — or null for a hook-edit or counterfactual-edit, whose body is derived from the one record in `supersedes` with `edit` applied"}]},
    "attack": {"claims": [{"target": "<premise:<id> | payload:<aspect> | activation | warrant:independence>", "refutation": "<what reading of the evidence would show it false>",
                           "reading_taken": "<true if you took that reading>", "landed": "<true if the reading showed it false>", "evidence": ["<what you read>"]}]},
    "verdict": {"verdict": "<admit | admit-amended(<amendment>) | decline(<why>) | defer(<until>) | escalate(<why>)>", "amendment": "<the amended decision text, or null>",
                "until": {"scorer": "<for defer keyed on the oracle: the scorer of `oracle.evaluation` whose next readings settle it; else null>",
                          "comparator": "<one of < <= > >= == !=; else null>", "value": "<a number; else null>", "persistence": "<consecutive runs the reading must hold; else null>",
                          "passes": "<for defer keyed on the schedule: passes to wait before re-adjudication; else null>"}},
    "credit": {"steers": [{"record": "<record id>", "slot": "<payload | activation | warrant>", "signature": "recalled-applied-still-corrected",
                           "correction": "<what the record got wrong>", "why_not_caught": "<why no floor caught it>"}]},
    "anchor": {"anchors": [{"article": "<a C- id from `articles`>", "anchor": "<one id or URI from `instances` that exemplifies the article>",
                            "why": "<how that instance instantiates the article's claim>"}]},
    "exemplifies": {"verdict": "<still-holds if the instance exemplifies the article; reversed if it contradicts it; moot if it does not bear on it>", "why": "<one sentence>"},
    "vocabulary": {"verdict": "<admit if the escapes name one shape no registered term covers and the blind coder also escaped; else decline(<why>)>",
                   "means": "<for admit: one sentence defining the term, as the registry will carry it>"},
    "currency": {"verdict": "<still-holds | reversed | moot>", "why": "<one sentence; a record whose cited anchor (`rotted`) retired still holds only if the anchor's successor stands for it>",
                 "premise": "<for reversed: the id of the premise the reading reversed; null when the warrant as a whole is disputed>"},
}


def request(name: str, **content: Any) -> str:
    """The JSON a role receives for request ``name``: the content, and the reply shape it must answer in."""
    if name not in REPLIES:
        raise KeyError(f"no reply shape for request {name!r}; requests are {sorted(REPLIES)}")
    return json.dumps({"request": name, **content, "reply": REPLIES[name]}, default=str)


EMPTY_IS_LEGAL = "an empty list is a legal answer: refusal is a first-class outcome when nothing observed earns a rung"
"""Sent as request content, never as a list placeholder — a placeholder inside a list comes back as a literal element."""


def drafts_in(out: Any, key: str) -> list[dict[str, Any]]:
    """The draft-carrying objects under ``key`` of a reply; anything that is not an object is dropped."""
    items = out.get(key, []) if isinstance(out, dict) else []
    return [raw for raw in items if isinstance(raw, dict)]


def refusal(e: Exception) -> str:
    """A parse refusal that names every failing field, so a role's next draft can be corrected against it."""
    errors = getattr(e, "errors", None)
    if callable(errors):
        return "; ".join(f"{'.'.join(str(x) for x in err['loc'])}: {err['msg'].removeprefix('Value error, ')}" for err in errors())[:1000]
    return str(e).splitlines()[0]


def body_of(raw: dict[str, Any]) -> dict[str, Any]:
    """A draft's ``body`` as an object: a model that serialises it as a JSON string is read, not refused."""
    body = raw.get("body")
    if isinstance(body, str):
        body = json.loads(body)
    return body if isinstance(body, dict) else {}


REPLY_RULE = ("Every request is one JSON object whose `reply` field states the exact shape of your answer: reply with one JSON object of that "
              "shape and nothing else, every angle-bracketed placeholder replaced by a value, no field added or renamed.")


@cache
def _load(role: str) -> tuple[str | None, str]:
    text = (HERE / f"{role}.md").read_text()
    priced = None
    if text.startswith("priced_for:"):
        head, _, text = text.partition("\n")
        priced = head.split(":", 1)[1].strip() or None
    return priced, text.strip()


def prompt(role: str) -> str:
    if role not in ROLES:
        raise KeyError(f"no role prompt for {role!r}; roles are {ROLES}")
    return _load(role)[1] + "\n\n" + REPLY_RULE + "\n\n" + schemas()


def priced_for(role: str) -> str | None:
    return _load(role)[0]


@cache
def schemas() -> str:
    """The record shapes every role reads and writes, derived from the declarations — never a second copy."""
    from hgi.types import Draft, LedgerEntry, Observation

    parts = ["## Record shapes (JSON Schema, derived from hgi/types.py)"]
    for model in (Observation, Draft, LedgerEntry):
        parts.append(f"### {model.__name__}\n```json\n{_compact(model)}\n```")
    return "\n\n".join(parts)


def _compact(model) -> str:
    """The whole schema, nested definitions included: a body drafted against a schema with its definitions stripped comes back in an invented shape."""
    return json.dumps(model.model_json_schema(by_alias=True), separators=(",", ":"))
