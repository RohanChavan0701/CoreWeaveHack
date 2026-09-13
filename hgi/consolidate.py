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
from hgi import lint as _lint
from hgi import model as _model
from hgi import roles
from hgi import tracing
from hgi.registry import term_head
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
    """Blind coding fills each open observation's ``shape``; equal shapes group, with the independence qualifier applied later."""
    open_obs = store.observations("open")
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
    scores = {s.id: {k: f.value for k, f in s.evaluation.scores.items()} for s in sessions if s.evaluation}
    return {
        "after_pass": record.after_pass,
        "sessions": [s.id for s in sessions],
        "scores": scores,
        "competence": _index.competence(store),
        "groups": group_observations(store, record),
        "credit": credit_table(store, sessions),
        "escapes": sorted({e for s in sessions for e in s.work_shape.escapes}),
        "accepted": [{"id": d.id, "decision": d.decision, "terms": d.consultation_terms} for d in store.decisions("accepted")],
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
    return {"observation_sessions": sessions, "bar_independent": store.registry.bars["decision"]["independent_observations"],
            "fault_rate": (len(faults) / rows) if rows else None, "task_ids": [row["task"] for row in []],
            "series": series, "watch_scorer": watch, "scores": brief["scores"]}


def attack(store: Store, record: Consolidation, draft: Draft, evidence: dict[str, Any]) -> tuple[dict[str, Any], _model.Completion]:
    c = _model.complete("examiner", roles.request("attack", draft=draft.model_dump(by_alias=True, mode="json"), evidence=evidence), session=record.id)
    return {"claims": c.json().get("claims", []), "verdict": "pending"}, c


def verdict(store: Store, record: Consolidation, draft: Draft, attack_payload: dict[str, Any], evidence: dict[str, Any]) -> tuple[str, str | None, _model.Completion]:
    c = _model.complete("adjudicator", roles.request("verdict", draft=draft.model_dump(by_alias=True, mode="json"), attack=attack_payload,
                                                     oracle={"series": evidence["series"], "scores": evidence["scores"]},
                                                     watch_scorer=evidence["watch_scorer"], bars=store.registry.bars), session=record.id)
    out = c.json()
    v = str(out.get("verdict", "escalate(adjudicator returned no verdict)"))
    store.registry.check("adjudicator-verdict", v)
    return v, out.get("amendment"), c


ATTACK_VERDICTS = {"admit": "survived-with-attack-named", "admit-amended": "survived-with-attack-named", "decline": "attack-landed"}


def adjudicate(store: Store, record: Consolidation, nomination: Nomination, draft: Draft, brief: dict[str, Any]) -> LedgerEntry:
    """Proposal → attack → verdict → commit, each role in its own context; the entry is appended once, with the verdict."""
    evidence = evidence_pack(store, draft, brief)
    attack_payload, examiner = attack(store, record, draft, evidence)
    v, amendment, adjudicator = verdict(store, record, draft, attack_payload, evidence)
    head = term_head(v)
    landed_premise = any(c["landed"] and c["target"].startswith("premise:") for c in attack_payload["claims"])
    entry = LedgerEntry(
        id=store.mint("hypothesis"), at=now(), species="attack", subject=draft.uid, claim=draft.body.decision,
        proposer=RoleCall(role="consolidator", model_id=_model.model_id(), call=record.brief.get("consolidator_call")),
        contradiction={"source": {"role": "examiner", "model_id": examiner.model_id, "call": examiner.call}, "attack": attack_payload},
        verdict="premise-killed" if landed_premise else ATTACK_VERDICTS.get(head, "pending"),
        adjudicator=RoleCall(role="adjudicator", model_id=adjudicator.model_id, call=adjudicator.call),
        amendment=amendment, rung=nomination.rung,
    )
    role = RoleCall(role="adjudicator", model_id=adjudicator.model_id, call=adjudicator.call)
    if head in ("admit", "admit-amended"):
        floor = [f for f in _lint.check_draft(store, draft) if f.level == "fail"]
        if floor:
            entry.outcome = "refused by the floor: " + "; ".join(f.message for f in floor)
            store.drop_draft(draft.uid)
        else:
            admission_entry = entry.model_copy(update={"verdict": v})
            decision = store.admit(draft, admission_entry, role, amendment={"decision": amendment} if head == "admit-amended" and amendment else None)
            record.flipped += list(draft.supersedes)
            record.admitted.append(decision.id)
            entry.outcome = f"admitted {decision.id}"
    elif head == "decline":
        store.drop_draft(draft.uid)
        entry.outcome = "declined; draft dropped"
    elif head == "escalate":
        store.enqueue(QueueEntry(draft=draft, ledger_entry=entry.id, why=v, queued_at=now(), oracle_evidence={"series": evidence["series"], "attack": attack_payload}))
        store.drop_draft(draft.uid)
        entry.outcome = "escalated to the human queue"
    else:
        entry.outcome = "deferred; draft kept in the pre-admission tier"
    store.append(entry)
    nomination.ledger_entry = entry.id
    nomination.outcome = entry.outcome
    return entry


def draft_from(store: Store, record: Consolidation, raw: dict[str, Any]) -> Draft:
    return store.parse_as(Draft, {"uid": store.new_uid(), "name": store.next_name("P"), "kind": "decision", "drafted_at": now().isoformat(),
                                  "proposed_by": record.id, "rung": raw["rung"], "rung_why": raw["rung_why"], "body": roles.body_of(raw),
                                  "evidence": list(raw.get("evidence", [])), "supersedes": list(raw.get("supersedes", []))})


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


def discharge_fires(store: Store, record: Consolidation) -> list[LedgerEntry]:
    """Every fire owed to the backward pass is re-adjudicated; the verdict, the fire's disposition and any flip land together."""
    entries = []
    for f in store.all("fire"):
        f: Fire
        if f.disposition.discharged or f.disposer != BACKWARD_PASS:
            continue
        d = store.find(f.latch.record)
        successor = d.lineage.superseded_by if isinstance(d, Decision) else None
        c = _model.complete("adjudicator", roles.request("currency", record=f.latch.record, fire=f.model_dump(by_alias=True, mode="json"), successor=successor),
                            session=record.id)
        out = c.json()
        v = out.get("verdict", "still-holds")
        entry = LedgerEntry(id=store.mint("hypothesis"), at=now(), species="currency", subject=f.latch.record,
                            claim=f"the warrant of {f.latch.record} still holds against {f.edge_event.scorer}={f.edge_event.observed}",
                            proposer=RoleCall(role="committer", model_id=None, call=None),
                            contradiction={"source": {"role": "adjudicator", "model_id": c.model_id, "call": c.call}, "coding": {"fire": f.id}},
                            verdict=v, adjudicator=RoleCall(role="adjudicator", model_id=c.model_id, call=c.call), outcome=out.get("why"))
        store.append(entry)
        f.disposition.outcome = v
        f.disposition.at = now()
        f.disposition.by = record.id
        store.write(f)
        record.fires_discharged.append(f.id)
        if v == "moot" and isinstance(d, Decision) and d.status == "accepted":
            store.flip_status(d, "moot", by=record.id)
            record.flipped.append(d.id)
        entries.append(entry)
    return entries


def retirement_review(store: Store, record: Consolidation) -> list[Nomination]:
    """applied ÷ considered nominates, never verdicts; the adjudicator's killer-item check decides mootness."""
    out = []
    for row in _index.competence(store):
        d: Decision = store.read("decision", row["record"])  # type: ignore[assignment]
        guard = d.lifecycle.retirement.guard
        if row["applied_over_considered"] is None or guard.applied_over_considered_below is None:
            continue
        if row["passes_in_window"] < (guard.over_passes or 0) or row["applied_over_considered"] >= guard.applied_over_considered_below:
            continue
        c = _model.complete("adjudicator", roles.request("currency", record=d.id, applied_over_considered=row["applied_over_considered"],
                                                         threshold=guard.applied_over_considered_below, moot_when=d.lifecycle.moot_when,
                                                         moot_evidence=row["considered"] > 0 and row["applied"] == 0), session=record.id)
        v = c.json().get("verdict", "still-holds")
        entry = LedgerEntry(id=store.mint("hypothesis"), at=now(), species="currency", subject=d.id,
                            claim=f"{d.id} applied ÷ considered = {row['applied_over_considered']:.2f} over {row['passes_in_window']} passes",
                            proposer=RoleCall(role="consolidator", model_id=None, call=None),
                            contradiction={"source": {"role": "adjudicator", "model_id": c.model_id, "call": c.call}, "coding": row},
                            verdict=v, adjudicator=RoleCall(role="adjudicator", model_id=c.model_id, call=c.call), rung="counterfactual-edit")
        store.append(entry)
        n = Nomination(rung="counterfactual-edit", rung_why="retirement leg: the nominating ratio fell below the guard", subject=d.id,
                       evidence=[f"applied_over_considered={row['applied_over_considered']}"], ledger_entry=entry.id, outcome=v)
        if v == "moot":
            store.flip_status(d, "moot", by=record.id)
            record.flipped.append(d.id)
        out.append(n)
    return out


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
    steers = credit(store, record, brief, sessions)
    discharge_fires(store, record)
    record.nominations += retirement_review(store, record)
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
    lines.append(f"fires discharged: {', '.join(record.fires_discharged) or 'none'}; admitted: {', '.join(record.admitted) or 'none'}; flipped: {', '.join(record.flipped) or 'none'}")
    if record.analyst_report:
        lines.append(f"analyst report: {record.analyst_report}")
    return "\n".join(lines)


# --- the human queue ------------------------------------------------------------------------

def resolve(store: Store, uid: str, v: str) -> str:
    """A human returns a verdict from the same vocabulary; the committer acts exactly as it would for the adjudicator."""
    store.registry.check("adjudicator-verdict", v)
    entry = next(q for q in store.queue() if q.draft.uid == uid)
    head = term_head(v)
    human = RoleCall(role="human", model_id=None, call=None)
    ledger = next(e for e in store.all("hypothesis") if e.id == entry.ledger_entry)  # type: ignore[attr-defined]
    outcome = "declined by the human queue"
    if head in ("admit", "admit-amended"):
        floor = [f for f in _lint.check_draft(store, entry.draft) if f.level == "fail"]
        if floor:
            outcome = "refused by the floor: " + "; ".join(f.message for f in floor)
        else:
            decision = store.admit(entry.draft, ledger.model_copy(update={"verdict": v, "adjudicator": human}), human)
            outcome = f"admitted {decision.id} on the human verdict {v}"
    store.dequeue(uid)
    store.append(LedgerEntry(id=store.mint("hypothesis"), at=now(), species="attack", subject=uid, claim=entry.draft.body.decision,
                             proposer=ledger.proposer, contradiction=ledger.contradiction, verdict=ATTACK_VERDICTS.get(head, "attack-landed"),
                             adjudicator=human, rung=entry.draft.rung, outcome=outcome))
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
           + (f", flipped {' '.join(record.flipped)}" if record.flipped else "") + (f", discharged {' '.join(record.fires_discharged)}" if record.fires_discharged else ""))
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
