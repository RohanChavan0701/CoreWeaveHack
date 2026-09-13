"""§ 6.2 — the latch fan, walked at the backward pass: edges evaluated, fires emitted, the mechanical check.

A latch is ⟨key-space · edge · guard · consumer · owed act · lifecycle⟩. The
edge makes it *considered*; the guard makes it *fire*; a fire is a record in
the fire ledger owed a disposition, never a state change in the host. Three
key-spaces move at consolidation, and each is evaluated here:

- **world-state** latches (revisit; a deferral keyed on the oracle) fire at
  evaluate time from the fact series — :mod:`hgi.evaluate` — and are
  discharged here by the backward pass;
- **competence** latches on a schedule edge (a deferral keyed on passes to
  wait) fire when the passes have elapsed;
- **neighbor** latches (wiring) fire when a record they name has departed
  from the status the guard last saw — the fire ledger carries every later
  observation, so the latch itself stays immutable.

A wiring latch's consumer is propagation and its owed act is ``check``: the
check is mechanical (the tombstone's successor resolves; a warrant's cited
records still stand) and a check that finds an anchor rotted nominates a
currency re-adjudication — a corroborating latch nominates, never settles.
:mod:`hgi.consolidate` owns every role call; this module owns no verdict.
"""

from __future__ import annotations

from typing import Any

from hgi import index as _index
from hgi.store import Store, now
from hgi.types import Decision, Draft, Envelope, Fire, Latch, WatchPredicate

PROPAGATION = "propagation"
BACKWARD_PASS = "the backward pass"
RETIRED = ("superseded", "moot", "evicted")
"""Statuses a neighbour departs *to* that rot an anchor pointing at it."""


# --- a deferral's condition as a latch --------------------------------------------------------

def deferral_latch(until: dict[str, Any] | None, *, evaluation: str, default_passes: int) -> Latch:
    """The latch a ``defer(<until>)`` verdict re-queues a draft with.

    ``until`` names a watch predicate (``scorer``, ``comparator``, ``value``,
    ``persistence``) the oracle's next runs settle, or ``passes`` to wait on
    the schedule; an adjudicator that names neither re-queues the draft at
    the next backward pass, so nothing sits in the pre-admission tier
    without a condition that can fire.
    """
    until = until or {}
    scorer = until.get("scorer")
    if scorer and until.get("comparator") in ("<", "<=", ">", ">=", "==", "!=") and until.get("value") is not None:
        predicate = WatchPredicate(evaluation=until.get("evaluation") or evaluation, scorer=scorer, comparator=until["comparator"],
                                   value=float(until["value"]), persistence=int(until.get("persistence") or 1))
        return Latch(type="revisit", slot="warrant", key_space="world-state", edge={"kind": "edge", "predicate": predicate},
                     consumer=BACKWARD_PASS, owed_act={"class": "re-adjudicate", "role": "dispositive"})
    passes = until.get("passes")
    passes = int(passes) if isinstance(passes, (int, float, str)) and str(passes).isdigit() and int(passes) > 0 else default_passes
    return Latch(type="revisit", slot="warrant", key_space="competence", edge={"kind": "schedule", "at": "consolidation"},
                 guard={"over_passes": passes}, consumer=BACKWARD_PASS, owed_act={"class": "re-adjudicate", "role": "dispositive"})


# --- emission at consolidation ------------------------------------------------------------------

def _fire(store: Store, host: str, index: int, latch: Latch, *, evaluation: str, pass_: int, scorer: str, observed, source: str) -> Fire:
    fire = Fire(id=store.mint("fire"), fired_at=now(), latch={"record": host, "index": index},
                edge_event={"evaluation": evaluation, "pass": pass_, "scorer": scorer, "observed": observed, "source": source},
                guard_result=True, disposer=latch.consumer, disposition={"act": latch.owed_act.class_})
    store.write(fire)
    return fire


def emit_scheduled(store: Store, after_pass: int, by: str) -> list[Fire]:
    """Every deferred draft whose schedule latch has waited its passes fires, owed to the backward pass."""
    pending = {(f["record"], f["latch_index"]) for f in _index.undischarged_fires(store)}
    fires = []
    for draft in store.drafts():
        if not draft.deferral:
            continue
        latches = draft.all_latches()
        i, latch = len(latches) - 1, latches[-1]
        if latch.edge.kind != "schedule" or latch.lifecycle.status != "live" or (draft.uid, i) in pending:
            continue
        elapsed = after_pass - draft.deferral.after_pass
        if elapsed >= (latch.guard.over_passes or 1):
            fires.append(_fire(store, draft.uid, i, latch, evaluation="competence", pass_=after_pass, scorer="passes_since_deferral", observed=elapsed, source=by))
    return fires


def emit_neighbour(store: Store, after_pass: int, by: str) -> list[Fire]:
    """Every live wiring latch whose neighbour has departed from the status last seen fires, owed to propagation.

    The status last seen is the latest fire on the same latch for that
    neighbour, else the status the guard recorded at the write; a record
    written before guards remembered statuses is read as having seen its
    successor ``accepted``, which is what a supersedure writes.
    """
    all_fires = store.all("fire")
    pending = {(f.latch.record, f.latch.index) for f in all_fires if not f.disposition.discharged}  # type: ignore[attr-defined]
    fires = []
    for d in store.decisions():
        for i, latch in enumerate(d.all_latches()):
            if latch.type != "wiring" or latch.lifecycle.status != "live" or (d.id, i) in pending:
                continue
            for rid in latch.guard.records:
                neighbour = store.find(rid)
                if not isinstance(neighbour, Envelope):
                    continue
                seen = [f.edge_event.observed for f in all_fires if f.latch.record == d.id and f.latch.index == i and f.edge_event.scorer == f"{rid}.status"]  # type: ignore[attr-defined]
                baseline = seen[-1] if seen else latch.guard.statuses.get(rid, "accepted")
                if neighbour.status != baseline:
                    fires.append(_fire(store, d.id, i, latch, evaluation="neighbor", pass_=after_pass, scorer=f"{rid}.status", observed=neighbour.status, source=by))
                    break  # one fire per latch per pass; the next neighbour's departure is the next consolidation's edge
    return fires


# --- the mechanical check -------------------------------------------------------------------------

def check(store: Store, host: Decision, fire: Fire) -> dict[str, Any]:
    """Propagation's ``check`` on a wiring fire: what the neighbour's move means for the host, and which anchors it rotted.

    A tombstone (``superseded`` | ``moot``) whose successor moved on keeps
    its pointer — the lineage path stands, and the path query reads through
    it. A standing record whose cited anchor retired has a rotted warrant;
    the check names the anchors and the backward pass asks the adjudicator
    whether the record still holds — the check itself settles nothing.
    """
    rid = fire.edge_event.scorer.removesuffix(".status")
    status = str(fire.edge_event.observed)
    neighbour = store.find(rid)
    successors = list(neighbour.lineage.superseded_by) if isinstance(neighbour, Decision) else []
    if host.status in ("superseded", "moot"):
        where = f"{rid} is now {status}" + (f", superseded by {', '.join(successors)}" if successors else "")
        return {"outcome": f"check: {where}; the tombstone {host.id} keeps its pointer and the lineage path stands", "rotted": []}
    rotted = [rid] if status in RETIRED and rid in host.warrant.anchors else []
    if rotted:
        return {"outcome": f"check: anchor {rid} is {status}" + (f" (successor {', '.join(successors)})" if successors else "") + f"; the warrant of {host.id} cites a retired record",
                "rotted": rotted, "successors": successors}
    return {"outcome": f"check: {rid} is now {status}; nothing {host.id} derives from it changed", "rotted": []}


def discharge(store: Store, fire: Fire, outcome: str, by: str) -> Fire:
    """Same-commit settlement: the fire's disposition and the change that settles it land together."""
    fire.disposition.outcome = outcome
    fire.disposition.at = now()
    fire.disposition.by = by
    store.write(fire)
    return fire


def settle(store: Store, draft: Draft, by: str) -> None:
    """A deferral latch settles when its draft is adjudicated again, whatever the verdict."""
    if draft.deferral and draft.deferral.until.lifecycle.status == "live":
        draft.deferral.until.lifecycle.status = "settled"
        draft.deferral.until.lifecycle.settled_at = now()
        draft.deferral.until.lifecycle.settled_by = by
        if store.draft(draft.uid) is not None:
            store.write_draft(draft)
