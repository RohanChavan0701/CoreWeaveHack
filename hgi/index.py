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

from hgi.registry import is_escape, read_json, write_json
from hgi.store import Store
from hgi.types import Decision, Disposition, Draft, Fire, Session

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
    """Hook-major: for each registered work-shape term, the accepted decisions whose consultation latches carry it.

    An ``other(<what>)`` escape in a guard is legal to write and reaches
    nothing here: no boot classifies into an escape, so a record keyed only
    on escapes is a structural zero until the term is minted and the hook
    re-keyed. A latch is worth exactly as much as the governance of its
    key-space.
    """
    out: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for d in store.decisions("accepted"):
        for i, latch in enumerate(d.all_latches()):
            if latch.type != "consultation" or latch.lifecycle.status != "live":
                continue
            for term in latch.guard.terms:
                if is_escape(term):
                    continue
                out[term].append({
                    "record": d.id,
                    "latch": d.summary.latch,
                    "not_this": sorted(set(d.summary.not_this) | set(latch.guard.not_this)),
                    "stakes": d.summary.stakes,
                    "owed_act": latch.owed_act.class_,
                    "latch_index": i,
                })
    return {term: sorted(cells, key=lambda c: c["record"]) for term, cells in sorted(out.items())}


UNWATCHED = "unwatched"
"""What a record's watch cell reads when no live world-state latch can send it back for re-adjudication: the world has no
way to contradict its warrant, and the cell says so loudly rather than defaulting — a join over nothing is displayed, never
tiebroken (doctrine § 16.17)."""


def watch_of(record: Decision) -> str:
    """The record's derived falsification grammar, as a cell: its live dispositive world-state watches, or ``unwatched``."""
    watches = [l.edge.predicate for l in record.all_latches()
               if l.type == "revisit" and l.lifecycle.status == "live" and l.owed_act.role == "dispositive" and l.edge.predicate]
    if not watches:
        return UNWATCHED
    return "; ".join(f"{p.scorer} {p.comparator} {p.value} over {p.persistence}" for p in watches)


def summaries(store: Store) -> list[dict[str, Any]]:
    """The full scan of one-line summaries the decision store is recalled by; ``watch`` is the record's derived grammar or ``unwatched``."""
    return [
        {"record": d.id, "status": d.status, "latch": d.summary.latch, "stakes": d.summary.stakes,
         "not_this": d.summary.not_this, "scopes": d.scopes, "watch": watch_of(d)}
        for d in store.decisions()
    ]


def watch_hosts(store: Store) -> list[tuple[str, list]]:
    """Every record the oracle's next run can move: accepted decisions and deferred drafts, with their latch fans.

    A draft's own fan is not yet live — nothing a draft proposes is yet true —
    so only its deferral latch is exposed, at the index a fire's ``latch.index``
    reads; the body's positions are held by ``None``.
    """
    hosts: list[tuple[str, list]] = [(d.id, d.all_latches()) for d in store.decisions("accepted")]
    hosts += [(p.uid, [None] * len(p.body.all_latches()) + [p.deferral.until]) for p in store.drafts() if p.deferral]
    return hosts


def triggers(store: Store) -> list[dict[str, Any]]:
    """Live revisit latches keyed on world-state, with their predicates — on decisions and on deferred drafts alike."""
    out = []
    for host, latches in watch_hosts(store):
        for i, latch in enumerate(latches):
            if latch is not None and latch.type == "revisit" and latch.lifecycle.status == "live" and latch.edge.predicate:
                out.append({"record": host, "latch_index": i, "predicate": latch.edge.predicate.model_dump(),
                            "disposer": latch.consumer, "owed_act": latch.owed_act.class_})
    return out


def deferred(store: Store) -> list[dict[str, Any]]:
    """Drafts re-queued on a ``defer(<until>)`` verdict, with the condition each waits on."""
    out = []
    for p in store.drafts():
        if not p.deferral:
            continue
        until = p.deferral.until
        out.append({"draft": p.uid, "name": p.name, "ledger_entry": p.deferral.ledger_entry, "after_pass": p.deferral.after_pass,
                    "key_space": until.key_space, "predicate": until.edge.predicate.model_dump() if until.edge.predicate else None,
                    "over_passes": until.guard.over_passes, "disposer": until.consumer})
    return out


def wiring(store: Store) -> list[dict[str, Any]]:
    """Live neighbour-keyed latches: which record watches which, and the status each neighbour was last seen in."""
    out = []
    for d in store.decisions():
        for i, latch in enumerate(d.all_latches()):
            if latch.type == "wiring" and latch.lifecycle.status == "live":
                out.append({"record": d.id, "status": d.status, "latch_index": i, "neighbours": latch.guard.records,
                            "seen": latch.guard.statuses, "owed_act": latch.owed_act.class_, "disposer": latch.consumer})
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
    """Accepted decisions no live consultation hook on a registered term reaches — stored, unreachable, never recalled."""
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


def row_passed(row: dict[str, Any]) -> bool:
    """Whether the oracle passed a task row: its ``task_pass_rate`` score, read off the row; an unscored row reads as passed only when it carries no error."""
    score = (row.get("scores") or {}).get("task_pass_rate") or {}
    return score.get("value") == 1.0 if "value" in score else not row.get("error")


def observed_from(store: Store, session: Session, row: dict[str, Any]) -> bool:
    """Whether the session filed an observation from this row: one anchored on the row's call, or naming its task when the row carries no call."""
    for o in store.observations(state=None):
        if o.session != session.id:
            continue
        if row.get("call") and o.anchor.call == row["call"]:
            return True
        if not row.get("call") and str(row.get("task")) in o.noticed:
            return True
    return False


def true_misses(store: Store) -> list[str]:
    """The rows nothing caught (§ 10.1, the bottom-right cell): a task failed in a closed attached session that consulted no
    record, and the pass filed no observation from the row — no latch fired, no floor refused, no noticing. Each is
    ``<session>/<task>``. A floor: the store cannot see a miss the world has not yet voted on."""
    out = []
    for s in store.all("session"):
        s: Session
        if not s.attached or s.closed_at is None or s.evaluation is None or s.consulted:
            continue
        for row in s.evaluation.rows:
            if not row_passed(row) and not observed_from(store, s, row):
                out.append(f"{s.id}/{row.get('task')}")
    return out


def matrix(store: Store) -> dict[str, Any]:
    """The detection matrix of § 10.1: steers × fires × applied dispositions × the rows nothing caught. Every count is a floor."""
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
    cells["system-misses/none-catches"] = true_misses(store)
    return {cell: sorted(ids) for cell, ids in sorted(cells.items())} | {
        "note": "system-misses/none-catches is detection-limited: it counts the failed rows of sessions that consulted nothing and filed "
                "no observation from the row, and its count is a floor — the store cannot see a miss the world has not yet voted on"}


def recall(store: Store) -> list[dict[str, Any]]:
    """Should-have-fired (§ 10.5, activation — recall): the boot recall lens's probes and the steers' archaeology, per record.

    L-0002 asks each pass which record the store holds that this work needed and no hook reached; a finding naming an
    accepted record the pass did not consult is a recall probe against that record's hook. Joined with the steers that
    indict a record's activation slot, the rows are the should-have-fired stream — a floor, never complete, and a
    nominator for re-keying (``hook-edit``), never a verdict. ``presented`` is what the probing passes classified their
    work as: the terms a re-key may add.
    """
    sessions, _ = _window(store)
    probes: dict[str, list[dict[str, Any]]] = defaultdict(list)
    presented: dict[str, set[str]] = defaultdict(set)
    accepted = {d.id: d for d in store.decisions("accepted")}
    for s in sessions:
        consulted = {c.record for c in s.consulted}
        for answer in s.lens_answers:
            if answer.lens != "L-0002":
                continue
            for f in answer.findings:
                rid = f.get("record")
                if rid in accepted and rid not in consulted:
                    probes[rid].append({"session": s.id, "why": str(f.get("why", "")), "call": answer.call})
                    presented[rid].update(s.work_shape.terms)
    steers = defaultdict(list)
    for t in store.all("steer"):
        if t.indicts and t.indicts.slot == "activation":  # type: ignore[attr-defined]
            steers[t.indicts.record].append(t.id)  # type: ignore[attr-defined]
    rows = []
    for rid in sorted(set(probes) | set(steers)):
        if rid not in accepted:
            continue
        hook = accepted[rid].consultation_terms
        rows.append({"record": rid, "hook": hook, "probes": probes.get(rid, []), "sessions": sorted({p["session"] for p in probes.get(rid, [])}),
                     "presented": sorted(presented.get(rid, set())), "missing": sorted(presented.get(rid, set()) - set(hook)), "steers": steers.get(rid, [])})
    return rows


def attacker(store: Store) -> dict[str, Any]:
    """The instruments are instrumented (I16): attacker precision as a tracked floor, and the attacker's misses as a stream.

    Over the attack species: how many drafts the examiner was dispatched against, how many claims it landed, how many of
    its landings the adjudicator upheld (``attack-landed`` | ``premise-killed``) against how many it overruled, per angle
    where the claims name their lens. A persistently zero landing count interrogates the dispatch bar before any target is
    declared clean, and a precision of one over zero overrulings is a ceiling artifact where the adjudicator absorbs the
    attack — both read as notes here, never as verdicts. The misses are the should-have-been-caught-by stream: a record
    that survived its attack and was later indicted by a steer, had a premise reversed, or went moot on its own warrant.
    """
    entries = [e for e in store.all("hypothesis") if e.species == "attack" and e.contradiction.attack]  # type: ignore[attr-defined]
    claims = [c for e in entries for c in e.contradiction.attack.claims]  # type: ignore[attr-defined]
    landed = [c for c in claims if c.landed]
    with_landing = [e for e in entries if any(c.landed for c in e.contradiction.attack.claims)]  # type: ignore[attr-defined]
    upheld = [e for e in with_landing if e.verdict in ("attack-landed", "premise-killed")]  # type: ignore[attr-defined]
    per_angle: dict[str, dict[str, int]] = defaultdict(lambda: {"claims": 0, "landed": 0})
    for c in claims:
        per_angle[c.lens or "single-context"]["claims"] += 1
        per_angle[c.lens or "single-context"]["landed"] += int(c.landed)
    indicted = defaultdict(list)
    for t in store.all("steer"):
        if t.indicts:  # type: ignore[attr-defined]
            indicted[t.indicts.record].append(t.id)  # type: ignore[attr-defined]
    misses = []
    for d in store.decisions():
        survived = [e.id for e in entries if (e.outcome or "").startswith(f"admitted {d.id}")]  # type: ignore[attr-defined]
        if not survived:
            continue
        caught_by = list(indicted.get(d.id, []))
        caught_by += [f"premise {p.id} {p.status}" for p in d.warrant.premises if p.status in ("reversed", "disputed")]
        if d.status == "moot":
            caught_by.append("moot on its own warrant")
        if caught_by:
            misses.append({"record": d.id, "survived": survived, "caught_by": caught_by})
    notes = []
    if entries and not landed:
        notes.append(f"zero landings over {len(entries)} dispatches: interrogate the dispatch bar before declaring any target clean")
    if with_landing and len(upheld) == len(with_landing):
        notes.append("every landing upheld: a precision of one over zero overrulings is a ceiling artifact where the adjudicator absorbs the attack, not a clean bill")
    return {"dispatched": len(entries), "claims": len(claims), "landed": len(landed), "entries_with_landing": len(with_landing),
            "upheld": len(upheld), "overruled": len(with_landing) - len(upheld),
            "precision": (len(upheld) / len(with_landing)) if with_landing else None,
            "per_angle": dict(sorted(per_angle.items())), "misses": misses, "notes": notes,
            "floor": "every count is a floor: an attack the synthesis absorbed before the ledger saw it is not here"}


PROJECTIONS: dict[str, Callable[[Store], Any]] = {
    "hooks": hooks,
    "summaries": summaries,
    "triggers": triggers,
    "deferred": deferred,
    "wiring": wiring,
    "fires": undischarged_fires,
    "competence": competence,
    "fusion": fusion,
    "convergence": convergence,
    "structural_zero": structural_zero,
    "lineage": lineage,
    "matrix": matrix,
    "attacker": attacker,
    "recall": recall,
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
