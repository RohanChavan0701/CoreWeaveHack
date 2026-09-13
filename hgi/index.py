"""Projections: regenerated read models under ``<store>/index/``, never hand-edited.

Each projection is a pure function of the store, listed in :data:`PROJECTIONS`.
``regenerate`` writes them all; ``check`` reports which committed projections
differ from regeneration (the projection-coherence gate of the lint).

Every cell obeys the settlement test (spec § 8.2): it carries what a reader
cannot comply with without opening the record — ids, hook prose, exclusions,
stakes, owed acts — and never a compliable sentence. The decision sentence
itself is evicted to the full record; :data:`FORBIDDEN_CELL_KEYS` names the
fields the lint refuses in any cell.
"""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Any, Callable

from hgi.registry import read_json, write_json
from hgi.store import Store
from hgi.types import Decision, Disposition, Fire, Session

FORBIDDEN_CELL_KEYS = frozenset({"decision", "duty", "then", "article", "context", "options"})
"""Fields whose content a reader could obey directly from a cell; the settlement test evicts them."""

_TOKEN = re.compile(r"[a-z0-9]+")


def tokens(text: str) -> set[str]:
    """Crude stems for the lexical nominator: lower-cased alphanumerics with a trailing ``s``/``ing``/``ed`` stripped."""
    out = set()
    for t in _TOKEN.findall((text or "").lower()):
        for suffix in ("ing", "ed", "es", "s"):
            if len(t) > len(suffix) + 2 and t.endswith(suffix):
                t = t[: -len(suffix)]
                break
        if len(t) > 2:
            out.add(t)
    return out


# --- projections --------------------------------------------------------------

def hooks(store: Store) -> dict[str, list[dict[str, Any]]]:
    """Hook-major: for each work-shape term, the accepted decisions whose consultation latches carry it."""
    out: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for d in store.decisions("accepted"):
        for i, latch in enumerate(d.all_latches()):
            if latch.type != "consultation" or latch.lifecycle.status != "live":
                continue
            for term in latch.guard.terms:
                out[term].append({
                    "record": d.id,
                    "latch": d.summary.latch,
                    "not_this": sorted(set(d.summary.not_this) | set(latch.guard.not_this)),
                    "stakes": d.summary.stakes,
                    "owed_act": latch.owed_act.class_,
                    "latch_index": i,
                })
    return {term: sorted(cells, key=lambda c: c["record"]) for term, cells in sorted(out.items())}


def summaries(store: Store) -> list[dict[str, Any]]:
    """The full scan of one-line summaries the decision store is recalled by."""
    return [
        {"record": d.id, "status": d.status, "latch": d.summary.latch, "stakes": d.summary.stakes,
         "not_this": d.summary.not_this, "scopes": d.scopes}
        for d in store.decisions()
    ]


def triggers(store: Store) -> list[dict[str, Any]]:
    """Live revisit latches keyed on world-state, with their predicates."""
    out = []
    for d in store.decisions("accepted"):
        for i, latch in enumerate(d.all_latches()):
            if latch.type == "revisit" and latch.lifecycle.status == "live" and latch.edge.predicate:
                out.append({"record": d.id, "latch_index": i, "predicate": latch.edge.predicate.model_dump(),
                            "disposer": latch.consumer, "owed_act": latch.owed_act.class_})
    return out


def undischarged_fires(store: Store) -> list[dict[str, Any]]:
    return [
        {"id": f.id, "record": f.latch.record, "latch_index": f.latch.index, "disposer": f.disposer,
         "owed_act": f.disposition.act, "fired_at": f.fired_at.isoformat()}
        for f in store.all("fire") if not f.disposition.discharged  # type: ignore[attr-defined]
    ]


def competence(store: Store) -> list[dict[str, Any]]:
    """applied ÷ considered per record over the review window — the demotion nominator, never a verdict."""
    sessions, window = _window(store)
    recent = {s.id for s in sessions}
    tally: dict[str, dict[str, int]] = defaultdict(lambda: {"considered": 0, "applied": 0, "guard_failed": 0, "off_map": 0})
    for u in store.all("disposition"):
        u: Disposition
        if u.session not in recent:
            continue
        t = tally[u.record]
        if u.considered:
            t["considered"] += 1
        if u.disposition == "applied":
            t["applied"] += 1
        elif u.disposition == "guard-failed":
            t["guard_failed"] += 1
        elif u.disposition == "fired-off-map":
            t["off_map"] += 1
    rows = []
    for d in store.decisions("accepted"):
        t = tally[d.id]
        ratio = (t["applied"] / t["considered"]) if t["considered"] else None
        rows.append({"record": d.id, **t, "applied_over_considered": ratio, "window_passes": window,
                     "passes_in_window": len(recent)})
    return rows


def _window(store: Store) -> tuple[list[Session], int]:
    """The closed attached sessions of the review window, oldest first, and the window's length."""
    window = store.registry.bars["retirement"]["window_passes"]
    sessions: list[Session] = sorted((s for s in store.all("session") if s.attached and s.closed_at is not None), key=lambda s: s.pass_)  # type: ignore[misc]
    return sessions[-window:], window


def _applied_by_session(store: Store, sessions: list[Session]) -> dict[str, dict[str, bool]]:
    """record → {session id → applied?} over the window, from the disposition ledger."""
    recent = {s.id for s in sessions}
    out: dict[str, dict[str, bool]] = defaultdict(dict)
    for u in store.all("disposition"):
        u: Disposition
        if u.session in recent and u.guard_passed:
            out[u.record][u.session] = u.disposition == "applied"
    return out


def fusion(store: Store) -> list[dict[str, Any]]:
    """Dispositions by matched sub-shape per accepted record — the split nominator of § 10.6.

    A record applied cleanly whenever one work-shape term matched it and never
    when only another did is a fused record; ``bimodal`` marks the rows where
    both sub-shapes were seen at least twice and their applied ratios sit at
    the two ends. The row nominates; the consolidator drafts the leaves and
    the adjudicator ratifies them against the raw anchors, never the labels.
    """
    sessions, _ = _window(store)
    applied = _applied_by_session(store, sessions)
    matched = {s.id: {c.record: c.terms_matched for c in s.considered if c.via == "index"} for s in sessions}
    rows = []
    for d in store.decisions("accepted"):
        by_term: dict[str, dict[str, int]] = defaultdict(lambda: {"considered": 0, "applied": 0})
        for sid, was_applied in applied.get(d.id, {}).items():
            for term in matched.get(sid, {}).get(d.id, []):
                by_term[term]["considered"] += 1
                by_term[term]["applied"] += int(was_applied)
        if len(by_term) < 2:
            continue
        seen_twice = {t: c for t, c in by_term.items() if c["considered"] >= 2}
        always = sorted(t for t, c in seen_twice.items() if c["applied"] == c["considered"])
        never = sorted(t for t, c in seen_twice.items() if c["applied"] == 0)
        rows.append({"record": d.id, "by_term": dict(sorted(by_term.items())), "applied_on": always, "never_on": never,
                     "bimodal": bool(always and never)})
    return rows


def convergence(store: Store) -> list[dict[str, Any]]:
    """Accepted pairs whose activation overlaps and whose applications coincide — the fold nominator of § 10.6.

    Two records applied in the same passes on the same hook have put their
    differentiation under stress; whether their payloads entail one another is
    the consolidator's reading and the adjudicator's verdict, never this row's.
    """
    sessions, _ = _window(store)
    applied = _applied_by_session(store, sessions)
    accepted = store.decisions("accepted")
    rows = []
    for i, a in enumerate(accepted):
        for b in accepted[i + 1:]:
            shared = sorted(set(a.consultation_terms) & set(b.consultation_terms))
            if not shared:
                continue
            on_a = {s for s, x in applied.get(a.id, {}).items() if x}
            on_b = {s for s, x in applied.get(b.id, {}).items() if x}
            rows.append({"records": [a.id, b.id], "shared_terms": shared, "identical_hooks": set(a.consultation_terms) == set(b.consultation_terms),
                         "co_applied": len(on_a & on_b), "applied_apart": len(on_a ^ on_b)})
    return rows


def structural_zero(store: Store) -> list[str]:
    """Accepted decisions no live consultation hook reaches."""
    reached = {cell["record"] for cells in hooks(store).values() for cell in cells}
    return [d.id for d in store.decisions("accepted") if d.id not in reached]


def lineage(store: Store) -> dict[str, Any]:
    """The lineage DAG: successor, split and fold edges, plus the observation → decision promotion edges."""
    edges = []
    for d in store.decisions():
        for p in d.lineage.supersedes:
            edges.append({"from": p, "to": d.id, "kind": "supersedes"})
        if d.lineage.split_from:
            edges.append({"from": d.lineage.split_from, "to": d.id, "kind": "split"})
        for p in d.lineage.folded_from:
            edges.append({"from": p, "to": d.id, "kind": "fold"})
        if d.admission.ledger_entry:
            edges.append({"from": d.admission.ledger_entry, "to": d.id, "kind": "admission"})
    for o in store.observations(state=None):
        if o.disposition.state == "promoted" and o.disposition.pointer:
            edges.append({"from": o.name, "to": o.disposition.pointer, "kind": "promotion"})
    nodes = sorted({e["from"] for e in edges} | {e["to"] for e in edges} | {d.id for d in store.decisions()})
    return {"nodes": nodes, "edges": edges}


def matrix(store: Store) -> dict[str, Any]:
    """The detection matrix of § 10.1: steers × fires × applied dispositions. Every count is a floor."""
    cells: dict[str, list[str]] = defaultdict(list)
    for t in store.all("steer"):
        cells[t.matrix_cell].append(t.id)  # type: ignore[attr-defined]
    indicted = {t.indicts.record for t in store.all("steer") if t.indicts}  # type: ignore[attr-defined]
    for f in store.all("fire"):
        f: Fire
        cells["system-catches/oracle-catches" if f.latch.record in indicted else "system-catches/none-catches"].append(f.id)
    for u in store.all("disposition"):
        u: Disposition
        if u.disposition == "applied" and u.record not in indicted:
            cells["system-catches/none-catches"].append(u.id)
    cells.setdefault("system-misses/none-catches", [])
    return {cell: sorted(ids) for cell, ids in sorted(cells.items())} | {"note": "system-misses/none-catches is detection-limited; its count is a floor of zero"}


PROJECTIONS: dict[str, Callable[[Store], Any]] = {
    "hooks": hooks,
    "summaries": summaries,
    "triggers": triggers,
    "fires": undischarged_fires,
    "competence": competence,
    "fusion": fusion,
    "convergence": convergence,
    "structural_zero": structural_zero,
    "lineage": lineage,
    "matrix": matrix,
}


def regenerate(store: Store) -> dict[str, Any]:
    out = {}
    for name, fn in PROJECTIONS.items():
        payload = fn(store)
        write_json(store.index_dir / f"{name}.json", payload)
        out[name] = payload
    return out


def check(store: Store) -> list[str]:
    """Names of projections whose committed file differs from regeneration."""
    stale = []
    for name, fn in PROJECTIONS.items():
        path = store.index_dir / f"{name}.json"
        committed = read_json(path) if path.exists() else None
        if committed != fn(store):
            stale.append(name)
    return stale


def read(store: Store, name: str) -> Any:
    path = store.index_dir / f"{name}.json"
    return read_json(path) if path.exists() else PROJECTIONS[name](store)


# --- the path query -------------------------------------------------------------

def paths_to(store: Store, id: str) -> list[list[str]]:
    """Every path through the lineage DAG that ends at ``id`` — the history of being wrong, read backwards."""
    graph = lineage(store)
    preds: dict[str, list[str]] = defaultdict(list)
    for e in graph["edges"]:
        preds[e["to"]].append(e["from"])

    def walk(node: str, seen: tuple[str, ...]) -> list[list[str]]:
        if node in seen or not preds.get(node):
            return [[node]]
        return [[*p, node] for pre in preds[node] for p in walk(pre, (*seen, node))]

    return walk(id, ())
