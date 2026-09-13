"""The observation-eliciting brief names the world, not the check.

The economy run filed observations that named their own scores — "the
`method_transfer` check was missed", "no check record fired to verify the
total" — because the series names reached the brief the close uses to elicit
them. Grouping starved: no finding named the actual convention (a footer row,
a trailing newline, a quoted comma) in words a later pass could group on. The
fix keeps the score/series names out of that brief (the L-0004 subject) and
asks the pass for the fact of the task's world its first attempt turned on.
"""

from __future__ import annotations

import json

from hgi import boot as _boot
from hgi import close as _close
from hgi import evaluate as _evaluate
from hgi import index as _index
from hgi import roles
from suite.scorers import SERIES


def _l0004(store):
    return next(l for l in store.registry.lenses("close") if l.id == "L-0004")


def _passed_session(store):
    s = _boot.boot(store, None, 1)
    _evaluate.evaluate_session(store, s.id, None, detached=False)
    _index.regenerate(store)
    return store.read("session", s.id)


def test_observation_brief_carries_no_series_or_score_names(store):
    session = _passed_session(store)
    subjects = _close.lens_subjects(store, session, _l0004(store))
    assert isinstance(subjects, list) and subjects, "the generative lens is walked once per failed row"

    # what the model actually receives: the eliciting brief, built exactly as walk_lenses builds it
    lens = _l0004(store)
    briefs = [roles.request("lens", lens={"id": lens.id, "angle": lens.angle, "counterfactual": lens.counterfactual, "product": lens.product},
                            subject=subject, empty_is_legal=roles.EMPTY_LENS_IS_LEGAL) for subject in subjects]
    blob = " ".join(briefs)
    for series in SERIES:
        assert series not in blob, f"the eliciting brief must not carry the series name {series!r}"

    # the row still carries the world facts the finding names — the output, the tool errors — just not the scores
    for subject in subjects:
        assert "scores" not in subject["row"], "the score dict, keyed by series name, is stripped from the brief"
        assert subject["row"].get("tool_errors") or subject["row"].get("error"), "the world facts survive"


def test_pass_prompt_asks_for_the_world_fact_not_the_check(store):
    prompt = roles.prompt("pass")
    assert "convention" in prompt, "the lens instruction asks for the convention the attempt turned on"
    assert "their scores" not in prompt, "the pass is no longer told to read the scores off the item"
