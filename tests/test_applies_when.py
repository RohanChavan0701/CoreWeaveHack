"""Carry-forward item 57 part 4 — cross-shape applicability is set at consolidation, and ``anchor_terms`` is a floor.

Reach is the consolidator's judgment (:func:`hgi.consolidate.applies_when`): the shapes the lesson fires on, biased
broad, with the origin tasks (:func:`hgi.consolidate.anchor_terms`) as the lower bound and the ``not_this`` the lens
draws for precision. The origin floor stays inside the hook whatever the lens answers, and a broadening onto a
pool-universal term is refused (the item-56 false-ripeness trap). The demotion recovers transfer the origin-seeded hook
defeated by construction.
"""

from __future__ import annotations

from hgi import consolidate as _consolidate
from hgi import stub
from hgi.drafting import sketch_of
from hgi.store import now
from hgi.types import Observation, Session


def _anchored_obs(store) -> Observation:
    """An observation whose anchor call resolves to a genesis/sum_numbers row — a task declaring shapes (http-tool, error-wrapping)."""
    row = {"task": "genesis/sum_numbers", "error": {"message": "GET /numbers failed", "cause": None}, "applied": [], "tool_errors": [], "call": "weave:///c/1"}
    facts = {"task_pass_rate": {"series": "suite-v1/task_pass_rate", "value": 0.5, "as_of": now().isoformat()}}
    s = store.parse_as(Session, {"id": store.mint("session"), "pass": 1, "started_at": now().isoformat(), "closed_at": now().isoformat(),
                                 "attached": True, "evaluation": {"evaluation": "suite-v1", "scores": facts, "rows": [row]}})
    store.write(s)
    o = Observation(uid=store.new_uid(), name=store.next_name("O"), noticed_at=now(), session=s.id,
                    happened="task genesis/sum_numbers failed and named no cause", anchor={"call": "weave:///c/1"})
    store.write(o)
    return o


def _sketch(store, terms):
    return sketch_of(stub.sketch("cause", list(terms), ["O-0001"]), store.registry)


def test_the_default_lens_keeps_reach_at_the_sketch_terms_and_the_floor(store):
    o = _anchored_obs(store)
    sk = _sketch(store, ["error-wrapping"])
    terms, not_this = _consolidate.applies_when(store, sk, [o.name])
    # the conservative stub does not broaden; the hook is the sketch's own term plus the origin floor
    assert set(terms) == {"error-wrapping", "http-tool"} and not_this == list(sk.not_this)


def test_the_lens_widens_the_reach_beyond_the_origin(store, monkeypatch):
    o = _anchored_obs(store)
    sk = _sketch(store, ["error-wrapping"])
    monkeypatch.setitem(stub.HANDLERS, "applies_when", lambda req: {"fires_on": ["error-wrapping", "shell-tool"], "not_this": ["a reasoning-loop retry"]})
    terms, not_this = _consolidate.applies_when(store, sk, [o.name])
    assert "shell-tool" in terms, "the lens sets reach beyond where the lesson was learned"
    assert {"error-wrapping", "http-tool"} <= set(terms), "the origin floor is kept under the widened reach"
    assert "a reasoning-loop retry" in not_this, "the lens draws the not_this that recovers precision"


def test_the_origin_floor_is_kept_even_when_the_lens_omits_it(store, monkeypatch):
    o = _anchored_obs(store)
    sk = _sketch(store, ["error-wrapping"])
    monkeypatch.setitem(stub.HANDLERS, "applies_when", lambda req: {"fires_on": ["shell-tool"], "not_this": []})
    terms, _ = _consolidate.applies_when(store, sk, [o.name])
    assert {"error-wrapping", "http-tool", "shell-tool"} <= set(terms), "the floor is the lower bound the lens cannot drop below"


def test_a_broadening_onto_a_pool_universal_term_is_refused(store, monkeypatch):
    o = _anchored_obs(store)
    sk = _sketch(store, ["error-wrapping"])
    monkeypatch.setattr(_consolidate, "pool_universal_terms", lambda *a, **k: {"output-schema"})
    monkeypatch.setitem(stub.HANDLERS, "applies_when", lambda req: {"fires_on": ["error-wrapping", "shell-tool", "output-schema"], "not_this": []})
    terms, _ = _consolidate.applies_when(store, sk, [o.name])
    assert "shell-tool" in terms and "output-schema" not in terms, "a term (essentially) every task carries keys no hook and is refused"


def test_sketch_body_carries_the_widened_reach_and_not_this(store, monkeypatch):
    raw = {"rung": "new-decision", "evidence": [], "sketch": stub.sketch("cause", ["error-wrapping"], [])}
    monkeypatch.setitem(stub.HANDLERS, "applies_when", lambda req: {"fires_on": ["error-wrapping", "shell-tool"], "not_this": ["a reasoning-loop retry"]})
    body = _consolidate.sketch_body(store, raw)
    hook = next(l["guard"] for l in body["latches"] if l["type"] == "consultation")
    assert {"error-wrapping", "shell-tool"} <= set(hook["terms"])
    assert "a reasoning-loop retry" in hook["not_this"] and "a reasoning-loop retry" in body["summary"]["not_this"]
