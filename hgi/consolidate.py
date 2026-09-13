"""§ 10 — the backward pass. ``hgi consolidate`` runs every *k* passes and on any fire owed to it.

Four roles, four contexts, no shared prompt beyond the store's schemas:

- the **consolidator** reads the brief and nominates — a rung of the ladder,
  why the cheaper rungs do not suffice, and a draft with all five slots;
- the **examiner** attacks the draft refute-phrased, in a fresh context, and
  emits an attack payload whose verdict is ``pending``;
- the **adjudicator** sees the draft, the attack, the oracle's evidence and
  the bars — never the proposer's narrative — and returns one token of the
  closed verdict vocabulary;
- the **committer** runs the floor and admits, declines, defers or escalates.

The brief is derived here from the ledgers (applied ÷ considered per record,
observations grouped by the blind coder's shapes under the independence
qualifier, task-level credit for every applied record, escape clusters).
When the analyst (ARIA) drafts it instead, its report URI is recorded on the
consolidation record; either way the machine enumerates, proposes and
audits — it never authors a verdict.
"""

from __future__ import annotations

import json
from collections import defaultdict
from typing import Any

from hgi import coder as _coder
from hgi import index as _index
from hgi import latches as _latches
from hgi import lint as _lint
from hgi import model as _model
from hgi import reviews as _reviews
from hgi import roles
from hgi import tracing
from hgi.registry import route_table
from hgi.store import Store, now
from hgi.types import (
    Consolidation,
    Decision,
    Draft,
    Fire,
    LedgerEntry,
    Nomination,
    Observation,
    QueueEntry,
    RoleCall,
    Session,
    Steer,
)

BACKWARD_PASS = "the backward pass"
PRIMARY_SERIES = "task_pass_rate"
"""The suite's headline series, the one credit assignment reads."""


# --- the brief ---------------------------------------------------------------------------

def sessions_since_last(store: Store) -> tuple[list[Session], int]:
    done = store.all("consolidation")
    last = max((k.after_pass for k in done), default=0)  # type: ignore[attr-defined]
    sessions = sorted((s for s in store.all("session") if s.attached and s.closed_at is not None and s.pass_ > last), key=lambda s: s.pass_)  # type: ignore[attr-defined]
    return sessions, last


def group_observations(store: Store, record: Consolidation) -> list[dict[str, Any]]:
    """Blind coding fills each open observation's ``shape``; equal shapes group, with the independence qualifier applied later.

    An observation a draft in the pre-admission tier already rests on is
    claimed until that draft is disposed — a deferred draft is not nominated
    twice from the same instances.
    """
    claimed = {e for p in store.drafts() for e in p.evidence}
    open_obs = [o for o in store.observations("open") if o.name not in claimed and o.uid not in claimed]
    if not open_obs:
        return []
    shapes, call = _coder.code([{"name": o.name, "noticed": o.noticed} for o in open_obs], store.registry.terms("work-shape"),
                               session=record.id, records_in_context=[])
    groups: dict[tuple[str, ...], list[Observation]] = defaultdict(list)
    for o in open_obs:
        o.shape = sorted(shapes.get(o.name, ["other(uncoded)"]))
        store.write(o)
        groups[tuple(o.shape)].append(o)
    return [{"shape": list(shape), "coder_call": call,
             "observations": [{"name": o.name, "uid": o.uid, "session": o.session, "noticed": o.noticed, "anchor": o.anchor.model_dump()} for o in obs],
             "sessions": sorted({o.session for o in obs})}
            for shape, obs in sorted(groups.items())]


def credit_table(store: Store, sessions: list[Session]) -> list[dict[str, Any]]:
    """Task-level credit for every record applied in the window: the applied tasks' pass fraction, before and after."""
    all_sessions = sorted((s for s in store.all("session") if s.attached and s.evaluation is not None), key=lambda s: s.pass_)  # type: ignore[attr-defined]
    window = {s.id for s in sessions}
    applied: dict[str, dict[str, list[bool]]] = defaultdict(lambda: {"tasks": [], "after": []})
    for s in sessions:
        for row in s.evaluation.rows:
            for rid in row.get("applied", []):
                applied[rid]["tasks"].append(row["task"])
                applied[rid]["after"].append(not row.get("error"))
    out = []
    for rid, a in applied.items():
        tasks = sorted(set(a["tasks"]))
        before = [not row.get("error") for s in all_sessions if s.id not in window and s.pass_ < min(x.pass_ for x in sessions)
                  for row in s.evaluation.rows if row["task"] in tasks]
        out.append({"record": rid, "scorer": PRIMARY_SERIES, "tasks": tasks, "applied_count": len(a["after"]),
                    "before": (sum(before) / len(before)) if before else None, "after": sum(a["after"]) / len(a["after"])})
    return out


def build_brief(store: Store, record: Consolidation, sessions: list[Session]) -> dict[str, Any]:
    """The consolidation brief: every nominator's row, and the whole body of each record a row names.

    A split's leaves and a fold's successor are derived from the bodies they
    leave, so a record named by ``fusion`` or ``convergence`` travels whole;
    every other accepted record travels as its cheap cue.
    """
    scores = {s.id: {k: f.value for k, f in s.evaluation.scores.items()} for s in sessions if s.evaluation}
    fusion = [row for row in _index.fusion(store) if row["bimodal"]]
    convergence = [row for row in _index.convergence(store) if row["co_applied"] >= 2]
    named = {row["record"] for row in fusion} | {r for row in convergence for r in row["records"]}
    presented = sorted({t for s in sessions for t in s.work_shape.terms})
    zero = [{"record": d.id, "terms": d.consultation_terms, "latch": d.summary.latch, "presented": presented}
            for d in store.decisions("accepted") if d.id in _index.structural_zero(store)]
    return {
        "after_pass": record.after_pass,
        "sessions": [s.id for s in sessions],
        "scores": scores,
        "competence": _index.competence(store),
        "groups": group_observations(store, record),
        "credit": credit_table(store, sessions),
        "fusion": fusion,
        "convergence": convergence,
        "structural_zero": zero,
        "escapes": sorted({e for s in sessions for e in s.work_shape.escapes}),
        "accepted": [{"id": d.id, "decision": d.decision, "terms": d.consultation_terms}
                     | ({"body": d.body().model_dump(by_alias=True, mode="json")} if d.id in named else {})
                     for d in store.decisions("accepted")],
        "steers": [t.id for t in store.all("steer")],
        "fires_owed": [f for f in _index.undischarged_fires(store) if f["disposer"] == BACKWARD_PASS],
    }


# --- the four roles ------------------------------------------------------------------------

def nominate(store: Store, record: Consolidation, brief: dict[str, Any]) -> list[dict[str, Any]]:
    c = _model.complete("consolidator", roles.request("nominate", brief=brief, bars=store.registry.bars, rungs=store.registry.terms("ladder-rung"),
                                                      vocabularies=store.registry.vocabulary_terms(), model_id=_model.model_id("pass"),
                                                      empty_is_legal=roles.EMPTY_IS_LEGAL), session=record.id)
    record.brief["consolidator_call"] = c.call
    return roles.drafts_in(c.json(), "nominations")


def evidence_pack(store: Store, draft: Draft, brief: dict[str, Any]) -> dict[str, Any]:
    """What the examiner and adjudicator see: the oracle's evidence, never the proposer's narrative."""
    obs = [store.observation(e) for e in draft.evidence]
    sessions = [o.session for o in obs if o]
    faults = [e for s in store.all("session") if s.attached and s.evaluation for row in s.evaluation.rows for e in row.get("tool_errors", []) if e.get("transient")]  # type: ignore[attr-defined]
    rows = sum(len(s.evaluation.rows) for s in store.all("session") if s.attached and s.evaluation)  # type: ignore[attr-defined]
    watch = next((l.edge.predicate.scorer for l in draft.body.latches if l.type == "revisit" and l.edge.predicate), None)
    series = {watch: [sc.get(watch) for sc in brief["scores"].values()]} if watch else {}
    evaluation = next((s.evaluation.evaluation for s in store.all("session") if s.attached and s.evaluation), "suite-v1")  # type: ignore[attr-defined]
    return {"observation_sessions": sessions, "bar_independent": store.registry.bars["decision"]["independent_observations"],
            "fault_rate": (len(faults) / rows) if rows else None, "task_ids": [row["task"] for row in []],
            "series": series, "watch_scorer": watch, "scores": brief["scores"], "evaluation": evaluation}


def attack(store: Store, record: Consolidation, draft: Draft, evidence: dict[str, Any]) -> tuple[dict[str, Any], _model.Completion]:
    c = _model.complete("examiner", roles.request("attack", draft=draft.model_dump(by_alias=True, mode="json"), evidence=evidence), session=record.id)
    return {"claims": c.json().get("claims", []), "verdict": "pending"}, c


def verdict(store: Store, record: Consolidation, draft: Draft, attack_payload: dict[str, Any], evidence: dict[str, Any]) -> tuple[str, dict[str, Any], _model.Completion]:
    """The adjudicator's one token, with the amendment an admit-amended names and the condition a defer names."""
    c = _model.complete("adjudicator", roles.request("verdict", draft=draft.model_dump(by_alias=True, mode="json"), attack=attack_payload,
                                                     oracle={"series": evidence["series"], "scores": evidence["scores"], "evaluation": evidence["evaluation"]},
                                                     watch_scorer=evidence["watch_scorer"], bars=store.registry.bars,
                                                     deferred=draft.deferral.model_dump(mode="json") if draft.deferral else None), session=record.id)
    out = c.json()
    v = str(out.get("verdict", "escalate(adjudicator returned no verdict)"))
    store.registry.check("adjudicator-verdict", v)
    return v, out, c


ADJUDICATION = route_table("adjudication", "adjudicator-verdict",
                           {"admit": "admit", "admit-amended": "admit", "decline": "drop", "escalate": "escalate", "defer": "defer", "other": "defer"})
"""What the committer does with the adjudicator's token on a draft. An escape verdict re-queues the draft rather than leaving it without a condition."""
ATTACK_VERDICTS = route_table("attack-ledger", "adjudicator-verdict",
                              {"admit": "survived-with-attack-named", "admit-amended": "survived-with-attack-named", "decline": "attack-landed",
                               "defer": "pending", "escalate": "pending", "other": "pending"})
"""The attack entry's verdict as the adjudicator's token settles it; a draft still pending leaves the attack pending."""
HUMAN = route_table("human-queue", "adjudicator-verdict",
                    {"admit": "admit", "admit-amended": "admit", "decline": "drop", "defer": "defer", "escalate": "keep", "other": "defer"})
"""The queue is the human's seat: an escalation from it has nowhere further to go and keeps the entry where it is."""
CURRENCY = route_table("currency", "currency-verdict", {"still-holds": "stand", "reversed": "dispute", "moot": "retire", "pending": "stand", "other": "stand"})
"""A warrant re-checked: ``retire`` flips the record moot, ``dispute`` flips the premise the reading reversed (every premise when none is named), ``stand`` leaves it."""


def adjudicate(store: Store, record: Consolidation, nomination: Nomination, draft: Draft, brief: dict[str, Any]) -> LedgerEntry:
    """Proposal → attack → verdict → commit, each role in its own context; the entry is appended once, with the verdict."""
    evidence = evidence_pack(store, draft, brief)
    attack_payload, examiner = attack(store, record, draft, evidence)
    v, out, adjudicator = verdict(store, record, draft, attack_payload, evidence)
    amendment = out.get("amendment")
    landed_premise = any(c["landed"] and c["target"].startswith("premise:") for c in attack_payload["claims"])
    act = store.registry.route("adjudicator-verdict", v, ADJUDICATION)
    entry = LedgerEntry(
        id=store.mint("hypothesis"), at=now(), species="attack", subject=draft.uid, claim=draft.body.decision,
        proposer=RoleCall(role="consolidator", model_id=_model.model_id(), call=record.brief.get("consolidator_call")),
        contradiction={"source": {"role": "examiner", "model_id": examiner.model_id, "call": examiner.call}, "attack": attack_payload},
        verdict="premise-killed" if landed_premise else store.registry.route("adjudicator-verdict", v, ATTACK_VERDICTS),
        adjudicator=RoleCall(role="adjudicator", model_id=adjudicator.model_id, call=adjudicator.call),
        amendment=amendment, rung=nomination.rung,
    )
    role = RoleCall(role="adjudicator", model_id=adjudicator.model_id, call=adjudicator.call)
    if act == "admit":
        floor = [f for f in _lint.check_draft(store, draft) if f.level == "fail"]
        if floor:
            entry.outcome = "refused by the floor: " + "; ".join(f.message for f in floor)
            store.drop_draft(draft.uid)
        else:
            admission_entry = entry.model_copy(update={"verdict": v})
            decision = store.admit(draft, admission_entry, role, amendment={"decision": amendment} if v.startswith("admit-amended") and amendment else None)
            record.flipped += [r for r in draft.retires if r not in record.flipped]
            record.admitted.append(decision.id)
            entry.outcome = f"admitted {decision.id}"
    elif act == "drop":
        store.drop_draft(draft.uid)
        entry.outcome = "declined; draft dropped"
    elif act == "escalate":
        store.enqueue(QueueEntry(draft=draft, ledger_entry=entry.id, why=v, queued_at=now(), oracle_evidence={"series": evidence["series"], "attack": attack_payload}))
        store.drop_draft(draft.uid)
        entry.outcome = "escalated to the human queue"
    else:  # defer: re-queued with the condition as a latch, never left without one
        entry.outcome = defer(store, record, draft, entry, out.get("until"), evaluation=evidence["evaluation"])
    store.append(entry)
    nomination.ledger_entry = entry.id
    nomination.outcome = entry.outcome
    return entry


EDIT_RUNGS = {"counterfactual-edit": ("counterfactual", "not_this"), "hook-edit": ("terms", "not_this")}
"""The slot-local rungs of the ladder (§ 10.3, rungs 1 and 4): each names the fields of ``edit`` it may change."""


def edited_body(store: Store, raw: dict[str, Any]) -> dict[str, Any]:
    """A successor's body for an edit rung: the one superseded record's body with the rung's fields replaced — a refinement is a successor record, never a rewrite."""
    rung, edit = raw.get("rung"), raw.get("edit") or {}
    if rung not in EDIT_RUNGS:
        return roles.body_of(raw)
    if len(raw.get("supersedes") or []) != 1:
        raise ValueError(f"a {rung} supersedes exactly one record; got {raw.get('supersedes')}")
    body = store.read("decision", raw["supersedes"][0]).body().model_dump(by_alias=True, mode="json")  # type: ignore[attr-defined]
    allowed = {k: v for k, v in edit.items() if k in EDIT_RUNGS[rung] and v}
    if not allowed:
        raise ValueError(f"a {rung} names at least one of {EDIT_RUNGS[rung]} in its edit")
    if "counterfactual" in allowed:
        body["counterfactual"] = allowed["counterfactual"]
    for latch in body["latches"]:
        if latch["type"] == "consultation":
            if "terms" in allowed:
                latch["guard"]["terms"] = list(allowed["terms"])
            if "not_this" in allowed:
                latch["guard"]["not_this"] = list(allowed["not_this"])
    if "not_this" in allowed:
        body["summary"]["not_this"] = list(allowed["not_this"])
    return body


def inherited_evidence(store: Store, retires: list[str]) -> list[str]:
    """The observation anchors of the records a draft retires: a successor, a leaf or a fold rests on the instances its predecessors rested on."""
    out: list[str] = []
    for rid in retires:
        if store.exists("decision", rid):
            out += [a for a in store.read("decision", rid).warrant.anchors if store.observation(a) is not None]  # type: ignore[attr-defined]
    return list(dict.fromkeys(out))


def defer(store: Store, record: Consolidation, draft: Draft, entry: LedgerEntry, until: Any, *, evaluation: str) -> str:
    """The committer's act on ``defer(<until>)``: the condition becomes a latch on the draft; the outcome names what it waits on."""
    latch = _latches.deferral_latch(until if isinstance(until, dict) else None, evaluation=evaluation,
                                    default_passes=store.registry.bars["consolidation_every_passes"])
    _latches.settle(store, draft, by=entry.id)
    store.defer(draft, entry, latch, after_pass=record.after_pass)
    record.deferred.append(draft.uid)
    return "deferred; re-queued with its condition as a latch: " + (
        f"{latch.edge.predicate.scorer} {latch.edge.predicate.comparator} {latch.edge.predicate.value} over {latch.edge.predicate.persistence} run(s)"
        if latch.edge.predicate else f"{latch.guard.over_passes} pass(es)")


def draft_from(store: Store, record: Consolidation, raw: dict[str, Any]) -> Draft:
    retires = [*(raw.get("supersedes") or []), *(raw.get("folded_from") or []), *([raw["split_from"]] if raw.get("split_from") else [])]
    return store.parse_as(Draft, {"uid": store.new_uid(), "name": store.next_name("P"), "kind": "decision", "drafted_at": now().isoformat(),
                                  "proposed_by": record.id, "rung": raw["rung"], "rung_why": raw["rung_why"], "body": edited_body(store, raw),
                                  "evidence": list(raw.get("evidence") or []) or inherited_evidence(store, retires),
                                  "supersedes": list(raw.get("supersedes") or []),
                                  "split_from": raw.get("split_from") or None, "folded_from": list(raw.get("folded_from") or [])})


# --- credit, fires, retirement --------------------------------------------------------------

def credit(store: Store, record: Consolidation, brief: dict[str, Any], sessions: list[Session]) -> list[Steer]:
    """Oracle-attributed steers: the adjudicator performs credit assignment on a regression, never the pass that produced it."""
    if not brief["credit"]:
        return []
    c = _model.complete("adjudicator", roles.request("credit", applied=brief["credit"]), session=record.id)
    fired_on = {f.latch.record for f in store.all("fire") if any(f.edge_event.pass_ == s.pass_ for s in sessions)}  # type: ignore[attr-defined]
    out = []
    for s in c.json().get("steers", []):
        steer = Steer(id=store.mint("steer"), at=now(), source={"kind": "oracle", "anchor": c.call}, correction=s["correction"],
                      indicts={"record": s["record"], "slot": s["slot"], "signature": s["signature"]}, why_not_caught=s.get("why_not_caught"),
                      matrix_cell="system-catches/oracle-catches" if s["record"] in fired_on else "system-misses/oracle-catches")
        store.append(steer)
        out.append(steer)
    return out


def discharge_fires(store: Store, record: Consolidation, brief: dict[str, Any]) -> list[LedgerEntry]:
    """Every fire owed to the backward pass is discharged by what it is on: a decision's revisit latch re-adjudicates the warrant
    (currency); a deferred draft's latch re-adjudicates the draft. The verdict, the fire's disposition and any flip land together."""
    entries = []
    _latches.emit_scheduled(store, record.after_pass, by=record.id)
    for f in store.all("fire"):
        f: Fire
        if f.disposition.discharged or f.disposer != BACKWARD_PASS:
            continue
        host = store.host(f.latch.record)
        if isinstance(host, Draft):
            entries.append(readjudicate(store, record, host, f, brief))
        elif isinstance(host, Decision):
            entries.append(currency(store, record, host, f))
        else:
            _latches.discharge(store, f, f"no host carries the latch {f.latch.record}[{f.latch.index}]; the fire is void", by=record.id)
        record.fires_discharged.append(f.id)
    return entries


def settle_currency(store: Store, record: Consolidation, d: Decision, out: dict[str, Any], entry: LedgerEntry) -> str:
    """Act on a currency verdict through :data:`CURRENCY`: retire, dispute the warrant, or let the record stand. Returns what was done."""
    act = store.registry.route("currency-verdict", entry.verdict, CURRENCY)
    if act == "retire" and d.status == "accepted":
        store.flip_status(d, "moot", by=entry.id)
        record.flipped.append(d.id)
        return f"{entry.verdict}: {d.id} flipped moot"
    if act == "dispute" and d.status == "accepted":
        premise = out.get("premise") if any(p.id == out.get("premise") for p in d.warrant.premises) else None
        store.flip_premises(d, "reversed" if premise else "disputed", premise, by=entry.id)
        record.flipped.append(d.id)
        return f"{entry.verdict}: " + (f"premise {premise} of {d.id} reversed" if premise else f"every premise of {d.id} disputed")
    return f"{entry.verdict}: {d.id} stands"


def ask_currency(store: Store, record: Consolidation, d: Decision, f: Fire, claim: str, coding: dict[str, Any], **content: Any) -> tuple[LedgerEntry, dict[str, Any]]:
    """The adjudicator re-checks a warrant; the currency entry is appended with its verdict."""
    c = _model.complete("adjudicator", roles.request("currency", record=d.id, fire=f.model_dump(by_alias=True, mode="json"), **content), session=record.id)
    out = c.json()
    v = str(out.get("verdict", "pending"))
    entry = LedgerEntry(id=store.mint("hypothesis"), at=now(), species="currency", subject=d.id, claim=claim,
                        proposer=RoleCall(role="committer", model_id=None, call=None),
                        contradiction={"source": {"role": "adjudicator", "model_id": c.model_id, "call": c.call}, "coding": coding},
                        verdict=v, adjudicator=RoleCall(role="adjudicator", model_id=c.model_id, call=c.call), outcome=out.get("why"))
    store.append(entry)
    return entry, out


def currency(store: Store, record: Consolidation, d: Decision, f: Fire) -> LedgerEntry:
    """A revisit fire on a decision: the adjudicator re-checks the warrant's currency and the verdict is routed."""
    successor = ", ".join(d.lineage.superseded_by) if d.lineage.superseded_by else None
    entry, out = ask_currency(store, record, d, f, claim=f"the warrant of {d.id} still holds against {f.edge_event.scorer}={f.edge_event.observed}",
                              coding={"fire": f.id}, successor=successor)
    _latches.discharge(store, f, settle_currency(store, record, d, out, entry), by=record.id)
    return entry


def readjudicate(store: Store, record: Consolidation, draft: Draft, f: Fire, brief: dict[str, Any]) -> LedgerEntry:
    """A deferred draft whose condition fired goes through attack and verdict again, in fresh contexts."""
    nomination = Nomination(rung=draft.rung, rung_why=draft.rung_why, subject=draft.name, evidence=list(draft.evidence), draft=draft.uid)
    _latches.settle(store, draft, by=f.id)
    entry = adjudicate(store, record, nomination, draft, brief)
    _latches.discharge(store, f, entry.outcome or entry.verdict, by=record.id)
    record.nominations.append(nomination)
    return entry


def propagate(store: Store, record: Consolidation) -> list[Fire]:
    """Wiring latches whose neighbour moved fire and are checked in the same commit; a rotted anchor goes to the adjudicator."""
    fires = _latches.emit_neighbour(store, record.after_pass, by=record.id)
    for f in fires:
        host: Decision = store.read("decision", f.latch.record)  # type: ignore[assignment]
        result = _latches.check(store, host, f)
        outcome = result["outcome"]
        if result["rotted"]:
            entry, out = ask_currency(store, record, host, f, claim=f"the warrant of {host.id} still holds with {', '.join(result['rotted'])} {f.edge_event.observed}",
                                      coding={"fire": f.id, "rotted": result["rotted"]}, rotted=result["rotted"], successor=", ".join(result.get("successors", [])) or None)
            outcome += f"; {entry.id}: {settle_currency(store, record, host, out, entry)}"
        _latches.discharge(store, f, outcome, by=record.id)
        record.fires_discharged.append(f.id)
    return fires


# --- the pass -------------------------------------------------------------------------------

def consolidate(store: Store, analyst_report: str | None = None, force: bool = False) -> Consolidation:
    tracing.init()
    sessions, last = sessions_since_last(store)
    every = store.registry.bars["consolidation_every_passes"]
    owed = [f for f in _index.undischarged_fires(store) if f["disposer"] == BACKWARD_PASS]
    if not force and len(sessions) < every and not owed:
        raise SystemExit(f"consolidation runs every {every} passes or on a fire owed to it; {len(sessions)} pass(es) since pass {last}, {len(owed)} fires owed")
    record = Consolidation(id=store.mint("consolidation"), started_at=now(), after_pass=max((s.pass_ for s in sessions), default=last),
                           sessions_read=[s.id for s in sessions], analyst_report=analyst_report)
    brief = build_brief(store, record, sessions)
    record.brief = {k: v for k, v in brief.items() if k != "groups"} | {"groups": [{k: v for k, v in g.items() if k != "observations"} | {"observations": [o["name"] for o in g["observations"]]} for g in brief["groups"]]}

    with tracing.attributes(session=record.id, role="consolidator"):
        for raw in nominate(store, record, brief):
            nomination = Nomination(rung=raw["rung"], rung_why=raw["rung_why"], subject=raw["subject"], evidence=list(raw.get("evidence", [])))
            try:
                draft = draft_from(store, record, raw)
            except ValueError as e:
                nomination.outcome = f"draft refused at parse: {roles.refusal(e)}"
                record.nominations.append(nomination)
                continue
            store.write_draft(draft)
            nomination.draft = draft.uid
            adjudicate(store, record, nomination, draft, brief)
            record.nominations.append(nomination)
    discharge_fires(store, record, brief)
    steers = credit(store, record, brief, sessions)
    record.nominations += _reviews.retirement(store, record)
    record.nominations += _reviews.genesis_anchors(store, record)
    record.nominations += _reviews.vocabulary(store, record)
    propagate(store, record)
    record.closed_at = now()
    store.write(record)
    print(report(record, steers))
    return record


def report(record: Consolidation, steers: list[Steer]) -> str:
    lines = [f"== {record.id} after pass {record.after_pass} — read {', '.join(record.sessions_read) or 'nothing'} ==",
             "groups: " + ("; ".join(f"{g['shape']} ← {', '.join(g['observations'])}" for g in record.brief.get("groups", [])) or "none")]
    for n in record.nominations:
        lines.append(f"nominated {n.rung} on {n.subject} ({', '.join(n.evidence)}) → {n.ledger_entry}: {n.outcome}")
    lines.append(f"steers: {', '.join(f'{t.id} {t.indicts.record if t.indicts else ''} [{t.matrix_cell}]' for t in steers) or 'none'}")
    lines.append(f"fires discharged: {', '.join(record.fires_discharged) or 'none'}; admitted: {', '.join(record.admitted) or 'none'}; "
                 f"flipped: {', '.join(record.flipped) or 'none'}; deferred: {', '.join(record.deferred) or 'none'}; anchored: {', '.join(record.anchored) or 'none'}; "
                 f"minted: {', '.join(record.minted) or 'none'}")
    if record.analyst_report:
        lines.append(f"analyst report: {record.analyst_report}")
    return "\n".join(lines)


# --- the human queue ------------------------------------------------------------------------

def resolve(store: Store, uid: str, v: str) -> str:
    """A human returns a verdict from the same vocabulary; the committer acts exactly as it would for the adjudicator."""
    act = store.registry.route("adjudicator-verdict", v, HUMAN)
    entry = next(q for q in store.queue() if q.draft.uid == uid)
    human = RoleCall(role="human", model_id=None, call=None)
    ledger = next(e for e in store.all("hypothesis") if e.id == entry.ledger_entry)  # type: ignore[attr-defined]
    verdict_entry = LedgerEntry(id=store.mint("hypothesis"), at=now(), species="attack", subject=uid, claim=entry.draft.body.decision,
                                proposer=ledger.proposer, contradiction=ledger.contradiction, verdict=store.registry.route("adjudicator-verdict", v, ATTACK_VERDICTS),
                                adjudicator=human, rung=entry.draft.rung)
    outcome = "declined by the human queue"
    if act == "admit":
        floor = [f for f in _lint.check_draft(store, entry.draft) if f.level == "fail"]
        if floor:
            outcome = "refused by the floor: " + "; ".join(f.message for f in floor)
        else:
            decision = store.admit(entry.draft, ledger.model_copy(update={"verdict": v, "adjudicator": human}), human)
            outcome = f"admitted {decision.id} on the human verdict {v}"
    elif act == "defer":
        last = max((k.after_pass for k in store.all("consolidation")), default=0)  # type: ignore[attr-defined]
        stand_in = Consolidation(id="K-0000", started_at=now(), after_pass=last, sessions_read=[])
        evaluation = next((s.evaluation.evaluation for s in store.all("session") if s.attached and s.evaluation), "suite-v1")  # type: ignore[attr-defined]
        outcome = defer(store, stand_in, entry.draft, verdict_entry, None, evaluation=evaluation) + " (from the human queue)"
    elif act == "keep":
        outcome = f"kept on the queue: {v} names no seat beyond the human's"
    if act != "keep":
        store.dequeue(uid)
    verdict_entry.outcome = outcome
    store.append(verdict_entry)
    return outcome


def register(add, store_of, finish) -> None:
    p = add("consolidate", "the backward pass over the ledgers")
    p.add_argument("--analyst-report", help="the ARIA report URI the brief was drafted from")
    p.add_argument("--force", action="store_true", help="run regardless of the k-pass schedule")
    p.set_defaults(fn=lambda args: _cmd(args, store_of, finish))
    q = add("queue", "the escalation queue: list it, or resolve one entry with a human verdict")
    q.add_argument("--resolve", metavar="UID")
    q.add_argument("--verdict", help="admit | admit-amended(<amendment>) | decline(<why>) | defer(<until>)")
    q.set_defaults(fn=lambda args: _queue(args, store_of, finish))


def _cmd(args, store_of, finish) -> int:
    store = store_of(args)
    record = consolidate(store, analyst_report=args.analyst_report, force=args.force)
    finish(store, args, f"Consolidate {record.id} after pass {record.after_pass}: admitted {' '.join(record.admitted) or 'nothing'}"
           + (f", flipped {' '.join(record.flipped)}" if record.flipped else "") + (f", discharged {' '.join(record.fires_discharged)}" if record.fires_discharged else "")
           + (f", deferred {len(record.deferred)}" if record.deferred else "") + (f", minted {' '.join(record.minted)}" if record.minted else ""))
    return 0


def _queue(args, store_of, finish) -> int:
    store = store_of(args)
    if not args.resolve:
        for q in store.queue():
            print(f"{q.draft.uid}  {q.draft.name}  {q.why}\n    {q.draft.body.decision}")
        return 0
    outcome = resolve(store, args.resolve, args.verdict)
    print(outcome)
    finish(store, args, f"Queue: {outcome}")
    return 0
