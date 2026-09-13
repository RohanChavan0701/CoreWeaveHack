"""The shape-radius scorer, trusted on a synthetic fixture where the right τ is known.

The recorded runs are thin and their curve is noisy; the scorer itself is checked here on hand-built labeled
observations whose Jaccard geometry is exact, so the metric — connected components, homogeneity/completeness,
``lessons_at_bar``, ``cross_lesson_clusters`` and the τ* rule — is known to be right before it reads real data.
"""

from __future__ import annotations

import math

from hgi import grouping_sweep as gs
from hgi.grouping_sweep import Labeled


def _obs(name: str, session: str, shape: set[str], lesson: str) -> Labeled:
    return Labeled(name=name, session=session, shape=frozenset(shape), lesson=lesson)


# --- similarity and components -----------------------------------------------------------------

def test_jaccard():
    assert gs.jaccard(frozenset("ab"), frozenset("ab")) == 1.0
    assert gs.jaccard(frozenset("ab"), frozenset("abc")) == 2 / 3
    assert gs.jaccard(frozenset("ab"), frozenset("cd")) == 0.0
    assert gs.jaccard(frozenset(), frozenset()) == 1.0


def test_components_at_tau_one_is_exact_match_grouping():
    """τ=1.0 reproduces today's tuple-equality grouping: one component per distinct shape, order by least index."""
    shapes = [frozenset("xy"), frozenset("xyz"), frozenset("xy"), frozenset("p")]
    comps = gs.components(shapes, 1.0)
    assert comps == [[0, 2], [1], [3]]  # the two identical {x,y} shapes group; {x,y,z} and {p} stand alone


def test_components_single_linkage_transitive_merge():
    """Single-linkage is transitive: a chain of 0.5-similar shapes joins into one component though the ends share little."""
    shapes = [frozenset("abc"), frozenset("bcd"), frozenset("cde")]
    assert gs.jaccard(shapes[0], shapes[1]) == 0.5 and gs.jaccard(shapes[1], shapes[2]) == 0.5
    assert gs.jaccard(shapes[0], shapes[2]) == 0.2  # the ends are below the threshold
    assert gs.components(shapes, 0.5) == [[0, 1, 2]]  # but the chain links them


# --- the entropy metrics -----------------------------------------------------------------------

def test_perfect_clustering_scores_one():
    obs = [_obs("o1", "s1", {"a"}, "A"), _obs("o2", "s2", {"a"}, "A"),
           _obs("o3", "s3", {"b"}, "B"), _obs("o4", "s4", {"b"}, "B")]
    clusters = [[0, 1], [2, 3]]
    h, c, v = gs.homogeneity_completeness_v([o.lesson for o in obs], clusters)
    assert h == 1.0 and c == 1.0 and v == 1.0
    assert gs.adjusted_rand_index([o.lesson for o in obs], clusters) == 1.0


def test_one_cluster_of_two_classes_is_complete_not_homogeneous():
    labels = ["A", "A", "B", "B"]
    clusters = [[0, 1, 2, 3]]  # everything in one cluster
    h, c, v = gs.homogeneity_completeness_v(labels, clusters)
    assert c == 1.0            # each class sits in one cluster
    assert h == 0.0            # the cluster holds both classes
    assert v == 0.0


def test_singletons_are_homogeneous_not_complete():
    labels = ["A", "A"]
    clusters = [[0], [1]]      # each point its own cluster
    h, c, _ = gs.homogeneity_completeness_v(labels, clusters)
    assert h == 1.0            # every cluster holds one class
    assert c < 1.0             # the class is split across two clusters


# --- the τ* rule on a fixture whose answer is known --------------------------------------------

def _fixture() -> list[Labeled]:
    """Two lessons, each split across a near-shape at τ=1.0, with a single shared term that only bridges the
    lessons at the widest radius (~0). The exact geometry, with the independence bar at 2:

      A: {x,y}@s1 and {x,y,z}@s2      jaccard 2/3 → merge at τ<=0.67
      B: {p,q}@s3 and {p,q,w}@s4      jaccard 2/3 → merge at τ<=0.67
      cross: {x,y,z} vs {p,q,w} share nothing; {x,y,z,w}... — the bridge is w on A's a2 and B's b2

    We put w on a2 as well so a2={x,y,z,w}: then jaccard(a1={x,y}, a2)=2/4=0.5 (A merges at τ<=0.5), and
    jaccard(a2, b2={p,q,w}) = 1/6 (< 0.25), so A and B bridge only at ~0 (any shared term).
    """
    return [_obs("a1", "s1", {"x", "y"}, "A"), _obs("a2", "s2", {"x", "y", "z", "w"}, "A"),
            _obs("b1", "s3", {"p", "q"}, "B"), _obs("b2", "s4", {"p", "q", "w"}, "B")]


def test_curve_and_recommendation_on_known_fixture():
    obs = _fixture()
    bar = 2
    curve = {s.tau_label: s for s in gs.sweep(obs, bar)}

    # τ=1.0 — exact match: four singletons, neither lesson reaches the two-session bar, no cross-lesson cluster.
    assert curve["1.0"].clusters == 4
    assert curve["1.0"].lessons_at_bar == 0
    assert curve["1.0"].cross_lesson_clusters == 0
    assert curve["1.0"].homogeneity == 1.0

    # τ=0.67 — B's 2/3 near-shape merges (B at the bar); A's 0.5 pair does not yet.
    assert curve["0.67"].lessons_at_bar == 1
    assert curve["0.67"].cross_lesson_clusters == 0

    # τ=0.5 — A's pair merges too: both lessons reach the bar inside one pure cluster. The win.
    assert curve["0.5"].lessons_at_bar == 2
    assert curve["0.5"].cross_lesson_clusters == 0
    assert curve["0.5"].homogeneity == 1.0

    # τ=0.25 — still pure and both at the bar: the shared w gives jaccard 1/6, below 0.25.
    assert curve["0.25"].lessons_at_bar == 2
    assert curve["0.25"].cross_lesson_clusters == 0

    # τ=~0 — any shared term bridges A and B through w: one impure cluster, the precision cost appears.
    assert curve["~0"].cross_lesson_clusters == 1
    assert curve["~0"].homogeneity < 1.0
    assert curve["~0"].lessons_at_bar == 0

    # τ* is the lowest τ (widest radius) that stays pure while maximizing lessons_at_bar: 0.25, not ~0.
    recommended, why = gs.recommend(gs.sweep(obs, bar))
    assert recommended is not None
    assert recommended.tau_label == "0.25"
    assert recommended.lessons_at_bar == 2
    assert "τ*=0.25" in why


def test_recommend_falls_back_to_baseline_when_no_tau_is_pure():
    """When one shape covers two lessons, even exact match conflates them; recommend names τ=1.0 with the caveat."""
    obs = [_obs("o1", "s1", {"http-tool"}, "moved-v2"), _obs("o2", "s2", {"http-tool"}, "token-route")]
    curve = gs.sweep(obs, bar=2)
    assert curve[0].tau_label == "1.0"
    assert curve[0].cross_lesson_clusters == 1  # the identical shape already spans two lessons
    recommended, why = gs.recommend(curve)
    assert recommended is not None and recommended.tau == 1.0
    assert "cannot recover" in why


def test_v_measure_is_harmonic_mean():
    labels = ["A", "A", "B", "B", "B"]
    clusters = [[0, 1, 2], [3, 4]]
    h, c, v = gs.homogeneity_completeness_v(labels, clusters)
    assert math.isclose(v, 2 * h * c / (h + c))
