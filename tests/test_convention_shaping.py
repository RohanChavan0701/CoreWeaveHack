"""The convention-shaping demonstration: the same labeled set, coded two ways, swept — the fix decision 77 named.

The shape-radius sweep (:mod:`hgi.grouping_sweep`) found no τ could buy precision because the coder shaped on the tool.
This pins the source fix: coding the same noticings on the convention makes the τ=1.0 grouping — the shipped radius —
pure, where coding them on the tool leaves it conflated. The synthetic set is coded through the real stub coder, so
the test exercises the shipped shaping rule; a live re-score on the endpoint is the pending confirmation.
"""

from __future__ import annotations

from hgi import grouping_sweep as gs


def _compare(store):
    return gs.compare_shapings(gs.SYNTHETIC_NOTICINGS, store.registry.terms("work-shape"), bar=2)


def test_tool_major_shaping_leaves_exact_match_impure(store):
    tool = _compare(store)["tool"]["at_tau_1.0"]
    assert tool["homogeneity"] < 1.0 and tool["cross_lesson_clusters"] >= 1
    # the tool cue collapses the shell lessons under one shape and the http lessons under a couple, far short of seven
    assert tool["clusters"] < len(gs.SYNTHETIC_NOTICINGS)


def test_convention_major_shaping_makes_exact_match_pure_and_brings_lessons_to_the_bar(store):
    cmp = _compare(store)
    conv = cmp["convention"]["at_tau_1.0"]
    lessons = {l for _, l, _ in gs.SYNTHETIC_NOTICINGS}
    assert conv["homogeneity"] == 1.0 and conv["cross_lesson_clusters"] == 0
    # every lesson with two independent sessions reaches the bar inside its own pure cluster
    assert conv["lessons_at_bar"] == len(lessons) > 0
    assert set(conv["lessons_at_bar_names"]) == lessons


def test_the_shift_is_the_coding_not_the_radius(store):
    """The convention shaping improves the τ=1.0 row itself — the radius the sweep left at 1.0 — not a wider one."""
    cmp = _compare(store)
    tool, conv = cmp["tool"]["at_tau_1.0"], cmp["convention"]["at_tau_1.0"]
    assert conv["homogeneity"] > tool["homogeneity"]
    assert conv["cross_lesson_clusters"] < tool["cross_lesson_clusters"]
    assert conv["lessons_at_bar"] > tool["lessons_at_bar"]
    # the shipped shaping resolves each lesson to its own distinct convention shape
    assert len(cmp["convention"]["distinct_shapes"]) == len({l for _, l, _ in gs.SYNTHETIC_NOTICINGS})
