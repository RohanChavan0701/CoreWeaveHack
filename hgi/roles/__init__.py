"""The role prompts, one file each, each priced.

A prompt file is Markdown with a leading ``priced_for:`` line naming the
model it was authored against. ``prompt(role)`` returns the body; the four
contexts of the backward pass share no prompt text beyond the store's
schemas, which every role receives through :func:`schemas`.
"""

from __future__ import annotations

from functools import cache
from pathlib import Path

HERE = Path(__file__).parent

ROLES = ("pass", "consolidator", "examiner", "adjudicator", "coder")


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
    return _load(role)[1] + "\n\n" + schemas()


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
    import json

    schema = model.model_json_schema(by_alias=True)
    schema.pop("$defs", None)
    return json.dumps(schema, separators=(",", ":"))[:4000]
