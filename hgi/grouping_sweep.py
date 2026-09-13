"""The shape-radius sweep: choosing the Jaccard threshold that groups observations, from evidence.

Today an observation joins a recurrence by exact tuple-equality of the blind
coder's ``shape`` (:func:`hgi.consolidate.group_observations`), and a group
becomes admissible only when it draws on ``decision.independent_observations``
distinct sessions (the independence bar, :func:`hgi.lint.independence`). Two
failed model runs (``carry-forward.md`` items 32, 39) showed the cost: the
coder gives near-identical shapes to observations of the *same* lesson
(``[http-tool, versioning]`` beside ``[http-tool]``), so exact-match splits one
lesson into two sub-bar piles and neither is admitted.

Widening the join to Jaccard set-similarity ``>= tau`` merges near-shapes — but
too wide a radius merges observations of *distinct* lessons, which costs
admission precision. So ``tau`` is a precision/recall trade-off and is chosen
here empirically, not guessed.

This module is a self-contained analysis. It does **not** touch
:func:`hgi.consolidate.group_observations`; a separate change wires the chosen
threshold in. The ground truth is the curriculum family's declared lesson: an
observation's anchor names the task it was filed on
(:class:`hgi.types.Anchor`), and the curriculum task carries the lesson it
turns on (:data:`suite.lessons.LESSONS`), so the task's lesson is a *true label*
for the observation.

The sweep, per ``tau`` over the grid (:data:`GRID`, ``tau=1.0`` reproduces
today's exact-match baseline):

1. build the similarity graph over the labeled observations — an edge ``i—j``
   when ``jaccard(shape_i, shape_j) >= tau`` — and cluster by connected
   components (single-linkage, :func:`components`);
2. score the clustering against the true lesson labels
   (:func:`score_clustering`): homogeneity, completeness and V-measure
   (:func:`homogeneity_completeness_v`) and Adjusted Rand Index
   (:func:`adjusted_rand_index`); ``lessons_at_bar`` — the lessons that reach
   the independence bar inside one *pure* (single-lesson) cluster, the win the
   widening buys; and ``cross_lesson_clusters`` — the clusters spanning two or
   more lessons, the precision cost.

The recommendation (:func:`recommend`) is the *lowest* ``tau`` (widest radius)
at which ``cross_lesson_clusters == 0`` (homogeneity ``== 1.0``), maximizing
``lessons_at_bar`` — a hard constraint, not the argmax of a soft metric, because
on thin data the soft optimum is unreliable and merging two distinct lessons is
the dangerous failure. When no ``tau`` is pure — the coder's own vocabulary
already gives two lessons the same shape — the baseline ``tau=1.0`` is
recommended with that caveat, since widening cannot recover a precision the
exact-match join never had.
"""

from __future__ import annotations

import json
import math
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

# --- the grid ------------------------------------------------------------------------------------

EPS = 1e-9
"""The widest radius, ``tau ~ 0``: an edge on any shared term. ``jaccard >= EPS`` iff the shapes intersect."""

GRID: list[tuple[str, float]] = [("1.0", 1.0), ("0.67", 2 / 3), ("0.5", 0.5), ("0.33", 1 / 3), ("0.25", 0.25), ("~0", EPS)]
"""The thresholds swept, widest radius last. The labels are the round fractions the brief names; the values are the
exact rationals they stand for (``0.67`` is ``2/3``, so a two-of-three overlap connects), and ``~0`` is :data:`EPS`.
``tau=1.0`` reproduces today's exact-match grouping — set equality — and is the baseline endpoint."""

TOLERANCE = 1e-9
"""An edge is drawn when ``jaccard >= tau - TOLERANCE``, so a rational Jaccard that equals a grid rational connects
despite float noise."""


# --- the labeled observation ---------------------------------------------------------------------

@dataclass(frozen=True)
class Labeled:
    """One observation as the sweep reads it: the coder's shape and the task's lesson as its true label.

    ``session`` and ``name`` are namespaced by the arm they were read from, so distinct-session counts and
    identities stay distinct when several recorded arms are combined into one labeled set.
    """

    name: str
    session: str
    shape: frozenset[str]
    lesson: str


# --- similarity and clustering -------------------------------------------------------------------

def jaccard(a: frozenset[str], b: frozenset[str]) -> float:
    """The Jaccard similarity of two shapes: ``|a ∩ b| / |a ∪ b|``. Two empty shapes are identical (``1.0``)."""
    if not a and not b:
        return 1.0
    union = a | b
    return len(a & b) / len(union) if union else 1.0


def components(shapes: list[frozenset[str]], tau: float) -> list[list[int]]:
    """Connected components (single-linkage) of the graph whose edge ``i—j`` is ``jaccard(shape_i, shape_j) >= tau``.

    Union-find over the ``O(n^2)`` pairs; returns each component as a sorted list of indices, the components ordered by
    their least index. ``tau=1.0`` yields one component per distinct shape — exact-match grouping.
    """
    n = len(shapes)
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x: int, y: int) -> None:
        parent[find(x)] = find(y)

    for i in range(n):
        for j in range(i + 1, n):
            if jaccard(shapes[i], shapes[j]) >= tau - TOLERANCE:
                union(i, j)
    groups: dict[int, list[int]] = defaultdict(list)
    for i in range(n):
        groups[find(i)].append(i)
    return sorted((sorted(members) for members in groups.values()), key=lambda m: m[0])


# --- the metric ----------------------------------------------------------------------------------

def _entropy(counts: Iterable[int], total: int) -> float:
    """The Shannon entropy (nats) of a distribution given as counts over ``total``; ``0`` for an empty or point mass."""
    h = 0.0
    for c in counts:
        if c > 0:
            p = c / total
            h -= p * math.log(p)
    return h


def homogeneity_completeness_v(labels: list[str], clusters: list[list[int]]) -> tuple[float, float, float]:
    """Homogeneity, completeness and their harmonic mean (V-measure) of a clustering against true ``labels``.

    Homogeneity is ``1 - H(C|K)/H(C)`` — a clustering is homogeneous when every cluster holds one class (lesson);
    completeness is ``1 - H(K|C)/H(K)`` — complete when every class sits in one cluster. Both are ``1.0`` at the
    degenerate limit where the conditioning entropy is defined to be zero (a single class, or a single cluster).
    """
    n = len(labels)
    if n == 0:
        return 1.0, 1.0, 1.0
    class_of = {c: i for i, c in enumerate(sorted(set(labels)))}
    class_counts = [0] * len(class_of)
    for lab in labels:
        class_counts[class_of[lab]] += 1
    cluster_counts = [len(m) for m in clusters]
    joint: dict[tuple[int, int], int] = defaultdict(int)
    for k, members in enumerate(clusters):
        for idx in members:
            joint[(class_of[labels[idx]], k)] += 1

    h_c = _entropy(class_counts, n)
    h_k = _entropy(cluster_counts, n)
    # H(C|K) = -sum p(c,k) log( p(c,k)/p(k) ) = -sum n_ck/N log(n_ck/n_k)
    h_c_given_k = 0.0
    for (_, k), n_ck in joint.items():
        h_c_given_k -= (n_ck / n) * math.log(n_ck / cluster_counts[k])
    # H(K|C) = -sum n_ck/N log(n_ck/n_c)
    h_k_given_c = 0.0
    for (c, _), n_ck in joint.items():
        h_k_given_c -= (n_ck / n) * math.log(n_ck / class_counts[c])

    homogeneity = 1.0 if h_c == 0 else 1.0 - h_c_given_k / h_c
    completeness = 1.0 if h_k == 0 else 1.0 - h_k_given_c / h_k
    v = 0.0 if homogeneity + completeness == 0 else 2 * homogeneity * completeness / (homogeneity + completeness)
    return homogeneity, completeness, v


def _comb2(n: int) -> int:
    return n * (n - 1) // 2


def adjusted_rand_index(labels: list[str], clusters: list[list[int]]) -> float:
    """The Adjusted Rand Index of a clustering against true ``labels`` — agreement over pairs, corrected for chance.

    ``1.0`` is a perfect match; ``0.0`` is chance; negative is worse than chance. ``1.0`` when every point is its own
    singleton and every point its own class, the standard degenerate convention.
    """
    n = len(labels)
    if n == 0:
        return 1.0
    class_of = {c: i for i, c in enumerate(sorted(set(labels)))}
    a = [0] * len(class_of)
    for lab in labels:
        a[class_of[lab]] += 1
    b = [len(m) for m in clusters]
    contingency: dict[tuple[int, int], int] = defaultdict(int)
    for k, members in enumerate(clusters):
        for idx in members:
            contingency[(class_of[labels[idx]], k)] += 1

    index = sum(_comb2(n_ck) for n_ck in contingency.values())
    sum_a = sum(_comb2(x) for x in a)
    sum_b = sum(_comb2(x) for x in b)
    total = _comb2(n)
    expected = (sum_a * sum_b / total) if total else 0.0
    maximum = (sum_a + sum_b) / 2
    if maximum == expected:
        return 1.0
    return (index - expected) / (maximum - expected)


@dataclass
class Score:
    """One row of the sweep: the clustering at ``tau`` scored against the true lesson labels."""

    tau_label: str
    tau: float
    clusters: int
    homogeneity: float
    completeness: float
    v_measure: float
    ari: float
    lessons_at_bar: int
    cross_lesson_clusters: int
    lessons_at_bar_names: list[str] = field(default_factory=list)

    def row(self) -> dict[str, Any]:
        return {"tau": self.tau_label, "tau_value": round(self.tau, 6), "clusters": self.clusters,
                "homogeneity": round(self.homogeneity, 4), "completeness": round(self.completeness, 4),
                "v_measure": round(self.v_measure, 4), "ari": round(self.ari, 4),
                "lessons_at_bar": self.lessons_at_bar, "cross_lesson_clusters": self.cross_lesson_clusters,
                "lessons_at_bar_names": sorted(self.lessons_at_bar_names)}


def score_clustering(obs: list[Labeled], clusters: list[list[int]], bar: int, tau_label: str, tau: float) -> Score:
    """Score one clustering: the entropy metrics, plus the two that decide the trade-off.

    ``lessons_at_bar`` is the count of distinct lessons that reach ``bar`` distinct sessions inside one *pure*
    (single-lesson) cluster — the admissions the widening is meant to buy. ``cross_lesson_clusters`` is the count of
    clusters holding two or more distinct lessons — the precision cost; it is zero exactly when homogeneity is ``1.0``.
    """
    labels = [o.lesson for o in obs]
    homogeneity, completeness, v = homogeneity_completeness_v(labels, clusters)
    ari = adjusted_rand_index(labels, clusters)
    cross = 0
    at_bar: set[str] = set()
    for members in clusters:
        lessons = {obs[i].lesson for i in members}
        if len(lessons) >= 2:
            cross += 1
            continue
        (lesson,) = tuple(lessons)
        if len({obs[i].session for i in members}) >= bar:
            at_bar.add(lesson)
    return Score(tau_label=tau_label, tau=tau, clusters=len(clusters), homogeneity=homogeneity, completeness=completeness,
                 v_measure=v, ari=ari, lessons_at_bar=len(at_bar), cross_lesson_clusters=cross, lessons_at_bar_names=sorted(at_bar))


def sweep(obs: list[Labeled], bar: int, grid: list[tuple[str, float]] = GRID) -> list[Score]:
    """The τ-curve: cluster and score at each grid threshold, widest radius last."""
    shapes = [o.shape for o in obs]
    return [score_clustering(obs, components(shapes, tau), bar, label, tau) for label, tau in grid]


def recommend(curve: list[Score]) -> tuple[Score | None, str]:
    """τ*: the lowest τ (widest radius) with ``cross_lesson_clusters == 0``, maximizing ``lessons_at_bar``.

    The hard constraint first, the recall gain as the tie-break. Returns the chosen row and the justification. When no
    τ is pure — even exact match conflates two lessons under one shape — the baseline ``tau=1.0`` is named with that
    caveat: widening cannot recover a precision the exact-match join never had.
    """
    pure = [s for s in curve if s.cross_lesson_clusters == 0]
    if not pure:
        baseline = next((s for s in curve if s.tau == 1.0), curve[0] if curve else None)
        why = ("no τ keeps every cluster within one lesson — the blind coder's shape vocabulary already gives two "
               "lessons the same shape, so exact match itself conflates them; τ=1.0 is named as the baseline, and "
               "widening the radius cannot recover a precision the join never had. Fix the coding, not the radius.")
        return baseline, why
    # lowest τ (widest radius); tie-break on the most lessons brought to the bar
    best = min(pure, key=lambda s: (s.tau, -s.lessons_at_bar))
    why = (f"τ*={best.tau_label}: the widest radius that keeps every cluster within a single lesson "
           f"(cross_lesson_clusters=0, homogeneity=1.0), bringing {best.lessons_at_bar} lesson(s) to the "
           f"independence bar" + (f" — {', '.join(best.lessons_at_bar_names)}" if best.lessons_at_bar_names else "") + ".")
    return best, why


# --- reading the labeled set -----------------------------------------------------------------------

CURRICULUM_FAMILIES = ("curriculum", "curriculum-strict")
"""The families whose tasks declare a lesson; their union is the id → lesson label source for the sweep."""


def id_to_lesson(families: Iterable[str] = CURRICULUM_FAMILIES) -> dict[str, str]:
    """Task id → its declared lesson, over the curriculum families — the true labels an observation's anchor resolves to."""
    from suite.families import FAMILIES

    out: dict[str, str] = {}
    for name in families:
        for task in FAMILIES[name].tasks():
            if task.lesson is not None:
                out[task.id] = task.lesson
    return out


def read_store(store_dir: Path, arm_label: str, labels: dict[str, str]) -> tuple[list[Labeled], dict[str, int]]:
    """The labeled observations of one recorded arm's store, joined observation → shape → task → lesson.

    Every session's rows give ``call → task``; each observation's ``anchor.call`` resolves to a task and the task to its
    lesson (``labels``). An observation is kept when it carries a non-empty coder shape and its anchor resolves to a
    labeled task; the returned counts say how many were dropped for want of each. Names and sessions are namespaced by
    ``arm_label`` so a combined set keeps them distinct.
    """
    from hgi import registry as _registry
    from hgi.store import Store

    reg = _registry.load(store_dir)
    token = _registry.use(reg)
    try:
        store = Store(store_dir, registry=reg)
        call_to_task: dict[str, str] = {}
        for s in store.all("session"):
            if s.attached and s.evaluation is not None:
                for row in s.evaluation.rows:
                    if row.get("call") and row.get("task"):
                        call_to_task[row["call"]] = row["task"]
        out: list[Labeled] = []
        counts = {"observations": 0, "no_shape": 0, "no_label": 0, "kept": 0}
        for o in store.observations(state=None):
            counts["observations"] += 1
            if not o.shape:
                counts["no_shape"] += 1
                continue
            lesson = labels.get(call_to_task.get(o.anchor.call or "", ""))
            if lesson is None:
                counts["no_label"] += 1
                continue
            out.append(Labeled(name=f"{arm_label}:{o.name}", session=f"{arm_label}:{o.session}",
                               shape=frozenset(o.shape), lesson=lesson))
            counts["kept"] += 1
    finally:
        _registry.reset(token)
    return out, counts


def _arm_dirs(run_root: Path, arms: list[str] | None) -> list[Path]:
    """The arm directories under ``run_root`` that hold a store, in name order; filtered to ``arms`` when given."""
    dirs = []
    for child in sorted(run_root.iterdir()):
        if (child / "store" / "registry").exists() and (arms is None or child.name in arms):
            dirs.append(child)
    return dirs


def read_dataset(run_root: Path, arms: list[str] | None = None) -> tuple[list[Labeled], dict[str, Any]]:
    """The combined labeled set over the recorded arms under ``run_root``, with the provenance the results record.

    An arm contributes only the labeled observations of its attached sessions; a detached arm keeps no store and
    contributes nothing. The provenance names the run root, the arms read, their per-arm counts, and the total N.
    """
    labels = id_to_lesson()
    obs: list[Labeled] = []
    per_arm: dict[str, dict[str, int]] = {}
    for arm_dir in _arm_dirs(run_root, arms):
        arm_obs, counts = read_store(arm_dir / "store", arm_dir.name, labels)
        if counts["kept"] == 0:
            continue
        obs += arm_obs
        per_arm[arm_dir.name] = counts
    provenance = {"run_root": str(run_root), "arms": sorted(per_arm), "per_arm": per_arm,
                  "n_labeled": len(obs), "n_lessons": len({o.lesson for o in obs}),
                  "n_sessions": len({o.session for o in obs}), "generated": False}
    return obs, provenance


# --- rendering and writing -------------------------------------------------------------------------

def as_markdown(curve: list[Score], recommended: Score | None, why: str, provenance: dict[str, Any], bar: int) -> str:
    """The readable τ-curve: a table of τ → the metrics, the recommendation and its justification, the dataset and N."""
    lines = ["# Shape radius — the Jaccard grouping threshold, from evidence", "",
             "The blind coder's shape groups observations into recurrences; a group at the independence bar "
             f"({bar} distinct sessions) can be admitted. Exact match (τ=1.0) splits one lesson across near-shapes; a "
             "wider Jaccard radius merges them, at the risk of merging distinct lessons. This is the τ-curve over the "
             "recorded runs, scored against the curriculum's declared lesson as the true label.", ""]
    if recommended is not None:
        lines += [f"**Recommended τ\\* = {recommended.tau_label}.** {why}", ""]
    else:
        lines += [f"**No τ recommended.** {why}", ""]
    lines += ["## Dataset", "",
              f"- Source: recorded runs under `{provenance['run_root']}` (attached arms; not freshly generated).",
              f"- Arms: {', '.join(provenance['arms']) or 'none'}.",
              f"- N = {provenance['n_labeled']} labeled observations over {provenance['n_sessions']} distinct sessions "
              f"and {provenance['n_lessons']} lessons.",
              "- Per arm (kept / observations; dropped for no-shape, no-label):"]
    for arm, c in sorted(provenance["per_arm"].items()):
        lines.append(f"  - `{arm}`: {c['kept']}/{c['observations']} (no-shape {c['no_shape']}, no-label {c['no_label']}).")
    lines += ["", "## The curve", "",
              "`lessons_at_bar` is the lessons that reach the bar inside one pure (single-lesson) cluster — the win. "
              "`cross_lesson_clusters` is the clusters spanning two or more lessons — the precision cost. "
              "Homogeneity is 1.0 exactly when there is no cross-lesson cluster.", "",
              "| τ | homogeneity | completeness | V-measure | ARI | clusters | lessons_at_bar | cross_lesson_clusters |",
              "|---|---|---|---|---|---|---|---|"]
    for s in curve:
        mark = " ✓" if recommended is not None and s.tau == recommended.tau else ""
        lines.append(f"| {s.tau_label}{mark} | {s.homogeneity:.3f} | {s.completeness:.3f} | {s.v_measure:.3f} | "
                     f"{s.ari:.3f} | {s.clusters} | {s.lessons_at_bar} | {s.cross_lesson_clusters} |")
    lines += ["", "## Reading", "",
              "τ=1.0 reproduces today's exact-match grouping. The recommendation is the *lowest* τ (widest radius) at "
              "which `cross_lesson_clusters == 0`, maximizing `lessons_at_bar` — a hard constraint rather than the "
              "argmax of a soft metric, because on thin data the soft optimum is unreliable and merging two distinct "
              "lessons is the dangerous failure. The counts are a floor from the recorded runs; a wider labeled set "
              "would sharpen the curve.", ""]
    return "\n".join(lines) + "\n"


def as_json(curve: list[Score], recommended: Score | None, why: str, provenance: dict[str, Any], bar: int) -> dict[str, Any]:
    return {"bar": bar, "grid": [label for label, _ in GRID], "dataset": provenance,
            "recommended_tau": recommended.tau_label if recommended is not None else None,
            "recommended_tau_value": round(recommended.tau, 6) if recommended is not None else None,
            "justification": why, "curve": [s.row() for s in curve]}


def write_results(out_dir: Path, curve: list[Score], recommended: Score | None, why: str,
                  provenance: dict[str, Any], bar: int) -> tuple[Path, Path]:
    """Write ``radius.json`` and ``radius.md`` under ``out_dir``; return their paths."""
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "radius.json"
    md_path = out_dir / "radius.md"
    json_path.write_text(json.dumps(as_json(curve, recommended, why, provenance, bar), indent=2, sort_keys=True) + "\n")
    md_path.write_text(as_markdown(curve, recommended, why, provenance, bar))
    return json_path, md_path


# --- the command -----------------------------------------------------------------------------------

DEFAULT_RUN_ROOT = "runs/stream"
DEFAULT_OUT = "experiments/results/grouping-radius"


def register(add, store_of, finish) -> None:
    p = add("grouping-radius", "sweep the Jaccard shape-radius τ over recorded runs and recommend τ*")
    p.add_argument("--run", default=DEFAULT_RUN_ROOT, help=f"the run root holding the arms (default: {DEFAULT_RUN_ROOT})")
    p.add_argument("--arm", action="append", help="read only this arm (repeatable); default every attached arm under the run root")
    p.add_argument("--out", default=DEFAULT_OUT, help=f"where to write radius.json and radius.md (default: {DEFAULT_OUT})")
    p.add_argument("--bar", type=int, default=None, help="the independence bar (default: the seed's decision.independent_observations)")
    p.set_defaults(fn=_cmd)


def _default_bar() -> int:
    from hgi.genesis import BARS

    return int(BARS["decision"]["independent_observations"])


def _cmd(args) -> int:
    run_root = Path(args.run)
    if not run_root.exists():
        raise SystemExit(f"no run root at {run_root}; pass --run <path to a directory of arms with store/>")
    bar = args.bar if args.bar is not None else _default_bar()
    obs, provenance = read_dataset(run_root, args.arm)
    provenance["bar"] = bar
    if not obs:
        raise SystemExit(f"no labeled observations found under {run_root}; every arm read was empty or unlabeled")
    curve = sweep(obs, bar)
    recommended, why = recommend(curve)
    json_path, md_path = write_results(Path(args.out), curve, recommended, why, provenance, bar)
    print(as_markdown(curve, recommended, why, provenance, bar))
    print(f"wrote {json_path} and {md_path}")
    return 0
