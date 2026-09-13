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

The brief the consolidator reads is the analyst's (ARIA's) report when its URI
is recorded on the pass (the programmatic surface: :func:`consolidation_brief`
resolves the URI through :func:`hgi.mirror.read_report`), and otherwise it is
derived here from the ledgers (applied ÷ considered per record, observations
grouped by the blind coder's shapes under the independence qualifier,
task-level credit for every applied record, escape clusters). Either way the
report is the nominator's rows only — the machine enumerates, proposes and
audits over the store's live records; it never authors a verdict or a fact.
"""

from __future__ import annotations

import json
from collections import defaultdict
from typing import Any

from hgi import coder as _coder
from hgi import drafting as _drafting
from hgi import index as _index
from hgi import latches as _latches
from hgi import lint as _lint
from hgi import mirror as _mirror
from hgi import model as _model
from hgi import reviews as _reviews
from hgi import roles
from hgi import tracing
import suite as _suite
from hgi.registry import route_table, term_head
from hgi.store import Store, now
from suite.scorers import SERIES
from hgi.types import (
    MECHANICAL,
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

    An observation a deferred draft already rests on is claimed until that
    draft is disposed — a deferred draft is not nominated twice from the same
    instances. A pass proposal is left unclaimed: its instances still group,
    which is how a nomination comes to adopt it.
    """
    claimed = {e for p in store.drafts() if p.deferral for e in p.evidence}
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
    known = {d.id for d in store.decisions()}
    for s in sessions:
        for row in s.evaluation.rows:
            for rid in row.get("applied", []):
                if rid not in known:
                    continue  # an id the pass invented is not a record; nothing is credited or indicted under it
                applied[rid]["tasks"].append(row["task"])
                applied[rid]["after"].append(not row.get("error"))
    out = []
    for rid, a in applied.items():
        tasks = sorted(set(a["tasks"]))
        before = [not row.get("error") for s in all_sessions if s.id not in window and s.pass_ < min(x.pass_ for x in sessions)
                  for row in s.evaluation.rows if row["task"] in tasks]
        out.append({"record": rid, "scorer": PRIMARY_SERIES, "tasks": tasks, "applied_count": len(a["after"]),
                    "before": (sum(before) / len(before)) if before else None, "after": sum(a["after"]) / len(a["after"]),
                    # itemized, never net (doctrine § 13): the fractions ship the counts they are computed from
                    "before_passed": sum(before), "before_rows": len(before), "after_passed": sum(a["after"]), "after_rows": len(a["after"])})
    return out


ANALYSIS_FIELDS = ("competence", "precision", "groups", "credit", "fusion", "convergence", "structural_zero", "escapes", "recall")
"""The nominator's analytical rows — what ARIA produces over the mirrored runs, and what the local pass derives when no analyst report resolves."""


def local_analysis(store: Store, record: Consolidation, sessions: list[Session]) -> dict[str, Any]:
    """The brief's analytical rows derived from the ledgers here: the fallback when no analyst report is present.

    Grouping fills each open observation's ``shape`` as a side effect (see :func:`group_observations`); the analyst
    surface writes the same shapes from its own coding instead (see :func:`adopt_shapes`).
    """
    presented = sorted({t for s in sessions for t in s.work_shape.terms})
    return {
        "competence": _index.competence(store),
        "precision": _index.precision(store),
        "groups": group_observations(store, record),
        "credit": credit_table(store, sessions),
        "fusion": [row for row in _index.fusion(store) if row["bimodal"]],
        "convergence": [row for row in _index.convergence(store) if row["co_applied"] >= 2],
        "structural_zero": [{"record": d.id, "terms": d.consultation_terms, "latch": d.summary.latch, "presented": presented}
                            for d in store.decisions("accepted") if d.id in _index.structural_zero(store)],
        "escapes": sorted({e for s in sessions for e in s.work_shape.escapes}),
        "recall": _index.recall(store),
    }


def assemble_brief(store: Store, record: Consolidation, sessions: list[Session], analysis: dict[str, Any]) -> dict[str, Any]:
    """The whole brief around a set of analytical rows — the analyst's or the local pass's — over the store's live state.

    The score facts, the accepted record bodies, the open proposals, the steers and the fires owed are the store's:
    the analyst reads runs and drafts the nominator's rows, it never authors a record or a fact. A record a lineage
    row (``fusion`` or ``convergence``) names travels whole, so its split or fold can derive from its body; every
    other accepted record travels as its cheap cue.
    """
    fusion = analysis.get("fusion") or []
    convergence = analysis.get("convergence") or []
    named = {row["record"] for row in fusion if isinstance(row, dict) and row.get("record")} \
        | {r for row in convergence if isinstance(row, dict) for r in (row.get("records") or [])}
    return {
        "after_pass": record.after_pass,
        "sessions": [s.id for s in sessions],
        "scores": {s.id: {k: f.value for k, f in s.evaluation.scores.items()} for s in sessions if s.evaluation},
        "competence": analysis.get("competence") or [],
        "precision": analysis.get("precision") or [],
        "groups": analysis.get("groups") or [],
        "credit": analysis.get("credit") or [],
        "fusion": fusion,
        "convergence": convergence,
        "structural_zero": analysis.get("structural_zero") or [],
        "escapes": analysis.get("escapes") or [],
        "recall": analysis.get("recall") or [],
        "accepted": [{"id": d.id, "decision": d.decision, "terms": d.consultation_terms}
                     | ({"body": d.body().model_dump(by_alias=True, mode="json")} if d.id in named else {})
                     for d in store.decisions("accepted")],
        "proposals": proposals(store),
        "steers": [t.id for t in store.all("steer")],
        "fires_owed": [f for f in _index.undischarged_fires(store) if f["disposer"] == BACKWARD_PASS],
        "attacker": _index.attacker(store),
    }


def build_brief(store: Store, record: Consolidation, sessions: list[Session]) -> dict[str, Any]:
    """The consolidation brief derived from the ledgers here: every nominator's row, and the whole body of each record a row names.

    This is the fallback the consolidator reads when no analyst report resolves; :func:`consolidation_brief` reads
    ARIA's report as the primary input when one is recorded.
    """
    return assemble_brief(store, record, sessions, local_analysis(store, record, sessions))


def adopt_shapes(store: Store, groups: list[dict[str, Any]]) -> None:
    """Stamp the analyst's coded shape onto each open observation it grouped — the write the local grouping performs.

    So a promotion pointer and the projections agree with what the analyst nominated on, exactly as they would with
    the local coder's shapes. An observation the report names that no longer exists, or is already disposed, is left.
    """
    for g in groups if isinstance(groups, list) else []:
        if not isinstance(g, dict):
            continue
        shape = sorted(t for t in (g.get("shape") or []) if isinstance(t, str))
        for o in g.get("observations") or []:
            name = o.get("name") if isinstance(o, dict) else o
            obs = store.observation(name) if isinstance(name, str) else None
            if obs is not None and obs.disposition.state == "open":
                obs.shape = shape
                store.write(obs)


def analyst_brief(store: Store, record: Consolidation, sessions: list[Session], report: dict[str, Any]) -> dict[str, Any]:
    """The consolidation brief with the analyst's report as its primary input: ARIA's analytical rows over the store's live state.

    ARIA reads the mirrored runs and drafts the nominator's rows; the code stamps its coding onto the open
    observations where the local grouping would write it and assembles the brief around the store's current records,
    proposals and owed fires. A row the report omits is empty, not re-derived — the report is the primary input, and
    the whole-brief fallback to :func:`build_brief` is for when no report resolves at all.
    """
    adopt_shapes(store, report.get("groups") or [])
    return assemble_brief(store, record, sessions, {k: report[k] for k in ANALYSIS_FIELDS if k in report})


def consolidation_brief(store: Store, record: Consolidation, sessions: list[Session], analyst_report: str | None = None) -> dict[str, Any]:
    """The brief the consolidator reads: the analyst's report when its URI resolves to one, else the local derivation.

    The programmatic ARIA surface (§ 9.3): ``hgi mirror`` publishes the runs, the analyst drafts the brief over them,
    and ``--analyst-report <uri>`` records where. When that URI resolves to a machine-readable report the
    consolidator reads it as the brief's primary input; a URI that names only an interactive report, or none at all,
    falls back gracefully to the derivation here. Either way the machine enumerates, proposes and audits — the
    analyst nominates, never verdicts.
    """
    if analyst_report:
        report = _mirror.read_report(analyst_report)
        if report is not None:
            return analyst_brief(store, record, sessions, report)
    return build_brief(store, record, sessions)


def proposals(store: Store) -> list[dict[str, Any]]:
    """The pre-admission tier as the consolidator sees it: every open draft, the pass's own included, by uid."""
    return [{"uid": d.uid, "name": d.name, "proposed_by": d.proposed_by, "drafted_at": d.drafted_at.isoformat(), "rung": d.rung,
             "decision": d.body.decision, "terms": d.consultation_terms if hasattr(d, "consultation_terms") else d.body.consultation_terms,
             "evidence": list(d.evidence), "supersedes": list(d.supersedes)} for d in store.drafts()]


# --- the noise filter -------------------------------------------------------------------------

TRIAGE = route_table("triage", "reality-verdict", {"reducible": "route", "irreducible": "dismiss", "pending": "route", "other": "route"})
"""What the noise filter does with the adjudicator's reality verdict on a recurrence: an irreducible group is dismissed
before any slot can update on it; a reducible one — and a verdict the adjudicator could not give — goes on to nomination,
where the four-role protocol judges it again."""

IRREDUCIBLE_ROUTE = "detection"
"""Where an irreducible recurrence's lesson goes: never to authoring — the record tier — but to the detection side, which
here is the disclosure the reality entry itself carries; a scorer or a fault profile that keeps producing it is the oracle's to fix."""


def group_evidence(store: Store, group: dict[str, Any]) -> dict[str, Any]:
    """The oracle's evidence on a group: the rows its observations anchor — error, cause, tool errors — read off the sessions, never the noticing's narrative."""
    names = [o["name"] if isinstance(o, dict) else o for o in group.get("observations", [])]
    obs = [store.observation(n) for n in names]
    calls = {o.anchor.call for o in obs if o is not None and o.anchor.call}
    rows = [{"session": s.id, "task": row.get("task"), "error": row.get("error"), "tool_errors": row.get("tool_errors", []), "call": row.get("call")}
            for s in store.all("session") if s.attached and s.evaluation  # type: ignore[attr-defined]
            for row in s.evaluation.rows if row.get("call") in calls]  # type: ignore[attr-defined]
    return {"rows": rows, "anchors": sorted(calls), "observations": [{"name": o.name, "session": o.session, "noticed": o.noticed, "anchor": o.anchor.model_dump(exclude_none=True)}
                                                                    for o in obs if o is not None]}


def triage(store: Store, record: Consolidation, brief: dict[str, Any]) -> list[dict[str, Any]]:
    """Noise-filter before updating process (§ 10.2, I11): every recurrence at the bar is classified before it can nominate.

    The adjudicator, in its own context, reads the group's observations and the rows they anchor and says whether the
    failure was **reducible** — a duty the loop missed, which the ladder may route — or **irreducible** — nothing any
    record could have prevented: the endpoint failed the turn, the turn limit fell, a hidden test raised. An
    irreducible group is dismissed with a pointer to its reality entry and leaves the brief, so no slot updates on it;
    its recurrence tunes detection, never authoring. The verdict is the adjudicator's, never the consolidator's, and the
    entry is the reality species: the observations' passes proposed the lesson, the oracle's rows contradict or bear it.
    """
    bar = store.registry.bars["decision"]["independent_observations"]
    rows = []
    kept = []
    for group in brief.get("groups", []):
        sessions = group.get("sessions") or sorted({o.get("session") for o in group.get("observations", []) if isinstance(o, dict)})
        if len(sessions) < bar:
            kept.append(group)
            continue
        evidence = group_evidence(store, group)
        c = _model.complete("adjudicator", roles.request("triage", shape=group.get("shape"), observations=evidence["observations"], rows=evidence["rows"],
                                                         vocabulary=store.registry.terms("reality-verdict")), session=record.id)
        out = c.json() if isinstance(c.json(), dict) else {}
        v = str(out.get("verdict") or "pending")
        try:
            store.registry.check("reality-verdict", v)
        except ValueError:
            v = f"other({v[:60]})"
        act = store.registry.route("reality-verdict", v, TRIAGE)
        names = [o["name"] for o in evidence["observations"]]
        entry = LedgerEntry(id=store.mint("hypothesis"), at=now(), species="reality", subject="group/" + "+".join(group.get("shape") or ["uncoded"]),
                            claim=f"the recurrence {group.get('shape')} across {sessions} is a duty the loop missed",
                            proposer=RoleCall(role="pass", model_id=None, call=None),
                            contradiction={"source": {"role": "oracle", "model_id": None, "call": evidence["anchors"][0] if evidence["anchors"] else None},
                                           "coding": {"shape": group.get("shape"), "observations": names, "sessions": sessions, "after_pass": record.after_pass, "route": act}},
                            verdict=v, adjudicator=RoleCall(role="adjudicator", model_id=c.model_id, call=c.call),
                            outcome=(out.get("why") or "") + (f"; dismissed {', '.join(names)}: routed to {IRREDUCIBLE_ROUTE}" if act == "dismiss" else "; routed to nomination"))
        store.append(entry)
        rows.append({"shape": group.get("shape"), "observations": names, "sessions": sessions, "verdict": v, "ledger_entry": entry.id, "act": act})
        if act == "dismiss":
            for name in names:
                o = store.observation(name)
                if o is not None and o.disposition.state == "open":
                    o.disposition.state = "dismissed"
                    o.disposition.pointer = entry.id
                    o.disposition.at = now()
                    store.write(o)
            record.dismissed += names
        else:
            kept.append(group)
    brief["groups"] = kept
    return rows


# --- the four roles ------------------------------------------------------------------------

def nominate_content(store: Store, brief: dict[str, Any]) -> dict[str, Any]:
    """The nominate request's content: the brief, the bars, the ladder, the vocabularies a draft must draw on."""
    return {"brief": brief, "bars": store.registry.bars, "rungs": store.registry.terms("ladder-rung"), "vocabularies": store.registry.vocabulary_terms(), "scorers": SERIES,
            "model_id": _model.model_id("pass"), "empty_is_legal": roles.EMPTY_IS_LEGAL}


def nominate(store: Store, record: Consolidation, brief: dict[str, Any]) -> list[dict[str, Any]]:
    c = _model.complete("consolidator", roles.request("nominate", **nominate_content(store, brief)), session=record.id)
    record.brief["consolidator_call"] = c.call
    return roles.drafts_in(c.json(), "nominations")


def evidence_pack(store: Store, draft: Draft, brief: dict[str, Any]) -> dict[str, Any]:
    """What the examiner and adjudicator see: the oracle's evidence, never the proposer's narrative."""
    sessions = store.draft_sessions(draft)
    faults = [e for s in store.all("session") if s.attached and s.evaluation for row in s.evaluation.rows for e in row.get("tool_errors", []) if e.get("transient")]  # type: ignore[attr-defined]
    rows = sum(len(s.evaluation.rows) for s in store.all("session") if s.attached and s.evaluation)  # type: ignore[attr-defined]
    watch = next((l.edge.predicate.scorer for l in draft.body.latches if l.type == "revisit" and l.edge.predicate), None)
    series = {watch: [sc.get(watch) for sc in brief["scores"].values()]} if watch else {}
    evaluation = next((s.evaluation.evaluation for s in store.all("session") if s.attached and s.evaluation), "suite-v1")  # type: ignore[attr-defined]
    return {"observation_sessions": sessions, "bar_independent": store.registry.bars["decision"]["independent_observations"],
            "fault_rate": (len(faults) / rows) if rows else None, "task_ids": [t.id for t in _suite.current().tasks],
            "series": series, "watch_scorer": watch, "scores": brief["scores"], "evaluation": evaluation}


def drop_success_watch(store: Store, draft: Draft) -> tuple[Draft, dict[str, Any]]:
    """The code's reading of ``warrant:watch-direction``. A sketched watch that fires when the record works
    (:func:`hgi.drafting.fires_on_success`) is dropped from the draft — the watch is optional, the draft is not — and the
    claim lands with the predicate and the drop as its evidence. The stripped draft is written back, so the examiner and
    the adjudicator read the draft that will be admitted, unwatched."""
    body = draft.body.model_dump(by_alias=True, mode="json")
    watch = _drafting.revisit_watch(body)
    claim = {"target": "warrant:watch-direction", "reading_taken": True, "landed": False, "lens": None, "call": None,
             "refutation": "the revisit watch fires when the record succeeds; a revisit must fire on the failure or regression the stakes name"}
    if watch is None:
        return draft, {**claim, "evidence": ["no world-state watch on the draft"]}
    predicate = f"{watch['scorer']} {watch['comparator']} {watch['value']}"
    if not _drafting.fires_on_success(watch["comparator"], float(watch["value"])):
        return draft, {**claim, "evidence": [f"{predicate} fires on the failure"]}
    body["latches"] = [l for l in body["latches"] if not (l.get("type") == "revisit" and l.get("key_space") == "world-state")]
    stripped = store.parse_as(Draft, {**draft.model_dump(by_alias=True, mode="json"), "body": body})
    store.write_draft(stripped)
    return stripped, {**claim, "landed": True, "evidence": [f"{predicate} fires on success", "the watch was dropped; the draft is judged and admitted unwatched"]}


def independence_claim(store: Store, draft: Draft, evidence: dict[str, Any]) -> dict[str, Any]:
    """The code's reading of ``warrant:independence``: the distinct sessions of the draft's evidence against the bar — the
    same count the floor refuses on (:func:`hgi.lint.independence`), so a landing here is a refusal at admission."""
    unmet = _lint.independence(store, draft)
    return {"target": "warrant:independence", "reading_taken": True, "landed": unmet is not None, "lens": None, "call": None,
            "refutation": "the anchored observations come from fewer distinct passes than the bar; one context counted twice is one datum",
            "evidence": [unmet.message if unmet else f"sessions {sorted(set(evidence['observation_sessions']))} meet the bar {evidence['bar_independent']}"]}


def settle(attack_payload: dict[str, Any], mechanical: list[dict[str, Any]]) -> dict[str, Any]:
    """The mechanical claims join the examiner's, first. An examiner claim on a mechanical class that contradicts the
    computed reading is discarded: the count is the code's, and a register still walking such a lens is advisory."""
    decided = {c["target"]: c["landed"] for c in mechanical}
    kept = [c for c in attack_payload["claims"] if c.get("target") not in decided or bool(c.get("landed")) == decided[c["target"]]]
    return {**attack_payload, "claims": [*mechanical, *kept]}


def attack(store: Store, record: Consolidation, draft: Draft, evidence: dict[str, Any], lenses: list[Any] | None = None) -> tuple[dict[str, Any], _model.Completion]:
    """The examiner attacks the verbatim draft, one angle per context: each examiner-hosted lens is walked in a fresh call
    and contributes the claims of its own class; the fan's product is their union, each claim naming the angle and the
    call that produced it. A fan walked in one context is a longer prompt, not an ensemble (the fan law), and the
    examiner is where tree-facing lenses live because its independence from the draft is structural (the host law).
    A register with no examiner lens falls back to the single-context attack, which is the same product with no angles.
    ``lenses`` names the angles to walk when the caller is not the backward pass — the lens battery's examiner control
    walks one angle at a time; the pass walks the register's.
    """
    lenses = store.registry.lenses("examiner") if lenses is None else lenses
    payload = dict(draft=draft.model_dump(by_alias=True, mode="json"), evidence=evidence)
    if not lenses:
        c = _model.complete("examiner", roles.request("attack", **payload), session=record.id)
        out = c.json()
        claims = [x for x in (out.get("claims", []) if isinstance(out, dict) else []) if isinstance(x, dict)]
        return {"claims": claims, "verdict": "pending"}, c
    claims, first = [], None
    for lens in lenses:
        c = _model.complete("examiner", roles.request("attack", lens={"id": lens.id, "angle": lens.angle, "counterfactual": lens.counterfactual,
                                                                       "claims": lens.claims, "product": lens.product}, **payload), session=record.id)
        first = first or c
        out = c.json()
        for x in (out.get("claims", []) if isinstance(out, dict) else []):
            if isinstance(x, dict) and any(str(x.get("target", "")).startswith(prefix) for prefix in lens.claims):
                claims.append({**x, "lens": lens.id, "call": c.call})
    return {"claims": claims, "verdict": "pending"}, first  # type: ignore[return-value]


def verdict(store: Store, record: Consolidation, draft: Draft, attack_payload: dict[str, Any], evidence: dict[str, Any]) -> tuple[str, dict[str, Any], _model.Completion]:
    """The adjudicator's token and its full reply — the amendment an admit-amended names, the condition a defer names, the
    rationale weighing the attack. A token outside the vocabulary is an escalation, never a guess."""
    c = _model.complete("adjudicator", roles.request("verdict", draft=draft.model_dump(by_alias=True, mode="json"), attack=attack_payload,
                                                     oracle={"series": evidence["series"], "scores": evidence["scores"], "evaluation": evidence["evaluation"]},
                                                     watch_scorer=evidence["watch_scorer"], task_ids=evidence["task_ids"], bars=store.registry.bars,
                                                     deferred=draft.deferral.model_dump(mode="json") if draft.deferral else None), session=record.id)
    out = c.json() if isinstance(c.json(), dict) else {}
    v = str(out.get("verdict") or "escalate(adjudicator returned no verdict)")
    try:
        store.registry.check("adjudicator-verdict", v)
    except ValueError:
        v = f"escalate(adjudicator returned a token outside the vocabulary: {v[:80]})"
    return v, out, c


def promote(store: Store, record: Consolidation, draft: Draft, evidence: dict[str, Any], landed: list[dict[str, Any]]) -> tuple[Draft, dict[str, Any]] | None:
    """A landed ``payload:abstraction`` is amend-only: the consolidator is re-asked once, with the refutation, to restate the
    payload at the transferable shape and keep the instances as anchors. The revised draft replaces the one on disk and
    is what the attack's abstraction angle re-walks and the adjudicator judges; ``None`` when the reply carries no new
    payload, in which case the adjudicator amends the payload itself."""
    instances = [o.noticed for e in draft.evidence if (o := store.observation(e)) is not None]
    c = _model.complete("consolidator", roles.request("promote", decision=draft.body.decision, refutations=[{"refutation": x.get("refutation"), "evidence": x.get("evidence", [])} for x in landed],
                                                      task_ids=evidence["task_ids"], instances=instances,
                                                      instruction="promote the payload to the transferable shape; keep the instances as anchors"), session=record.id)
    out = c.json() if isinstance(c.json(), dict) else {}
    text = out.get("decision")
    if not isinstance(text, str) or not text.strip() or text.strip() == draft.body.decision:
        return None
    body = draft.body.model_dump(by_alias=True, mode="json") | {"decision": text.strip()}
    revised = store.parse_as(Draft, {**draft.model_dump(by_alias=True, mode="json"), "body": body})
    store.write_draft(revised)
    return revised, {"decision": draft.body.decision, "claims": landed, "consolidator_call": c.call}


def rewalk(store: Store, record: Consolidation, draft: Draft, evidence: dict[str, Any], attack_payload: dict[str, Any], lens_ids: set[str | None]) -> dict[str, Any]:
    """The angles whose claims a promotion answered are walked again over the revised draft, and their claims replace
    the stale ones; the code's claims and the other angles' stand. A single-context attack (no lens) is re-run whole."""
    lenses = [l for l in store.registry.lenses("examiner") if l.id in lens_ids] or None
    fresh, _ = attack(store, record, draft, evidence, lenses=lenses)
    kept = [c for c in attack_payload["claims"] if c.get("target") in MECHANICAL or c.get("lens") not in lens_ids]
    return {**attack_payload, "claims": [*kept, *fresh["claims"]]}


ADJUDICATION = route_table("adjudication", "adjudicator-verdict",
                           {"admit": "admit", "admit-amended": "admit", "decline": "drop", "escalate": "escalate", "defer": "defer", "other": "defer"})
"""What the committer does with the adjudicator's token on a draft. An escape verdict re-queues the draft rather than leaving it without a condition."""
ATTACK_VERDICTS = route_table("attack-ledger", "adjudicator-verdict",
                              {"admit": "survived-with-attack-named", "admit-amended": "survived-with-attack-named", "decline": "attack-landed",
                               "defer": "pending", "escalate": "pending", "other": "pending"})
"""The attack entry's verdict as the adjudicator's token settles it; a draft still pending leaves the attack pending. The
backward pass's own decline is always a premise kill (:func:`adjudicate` overrides any other), so ``attack-landed`` is
reached only from the human queue."""
HUMAN = route_table("human-queue", "adjudicator-verdict",
                    {"admit": "admit", "admit-amended": "admit", "decline": "drop", "defer": "defer", "escalate": "keep", "other": "defer"})
"""The queue is the human's seat: an escalation from it has nowhere further to go and keeps the entry where it is."""
CURRENCY = route_table("currency", "currency-verdict", {"still-holds": "stand", "reversed": "dispute", "moot": "retire", "pending": "stand", "other": "stand"})
"""A warrant re-checked: ``retire`` flips the record moot, ``dispute`` flips the premise the reading reversed (every premise when none is named), ``stand`` leaves it."""


def adjudicate(store: Store, record: Consolidation, nomination: Nomination, draft: Draft, brief: dict[str, Any]) -> LedgerEntry:
    """Proposal → attack → verdict → commit, each role in its own context; the entry is appended once, with the verdict.

    The two mechanical classes (:data:`hgi.types.MECHANICAL`) are read by the code before any context opens: a watch that
    fires on success is dropped from the draft, and the independence count is the floor's. A landed abstraction claim
    with no premise kill beside it and the bar met sends the draft back to the consolidator once (:func:`promote`). A
    ``decline`` stands only on an upheld premise kill — a landed ``premise:`` claim the adjudicator declined on; a decline
    with none is overridden to an admit (amended where an amendment was offered), the attack named on the entry and the
    override on its outcome. Defer and escalate are the adjudicator's as returned."""
    claim = draft.body.decision
    draft, watch = drop_success_watch(store, draft)
    evidence = evidence_pack(store, draft, brief)
    mechanical = [independence_claim(store, draft, evidence), watch]
    attack_payload, examiner = attack(store, record, draft, evidence)
    attack_payload = settle(attack_payload, mechanical)
    landed = [c for c in attack_payload["claims"] if isinstance(c, dict) and c.get("landed")]
    abstraction = [c for c in landed if str(c.get("target", "")).startswith("payload:")]
    promotion = None
    if abstraction and all(c in abstraction or c["target"] == "warrant:watch-direction" for c in landed):
        if (revised := promote(store, record, draft, evidence, abstraction)) is not None:
            draft, promotion = revised
            attack_payload = rewalk(store, record, draft, evidence, attack_payload, {c.get("lens") for c in abstraction})
    v, out, adjudicator = verdict(store, record, draft, attack_payload, evidence)
    amendment = out.get("amendment") if isinstance(out.get("amendment"), str) else None
    rationale = out.get("rationale") if isinstance(out.get("rationale"), str) else None
    landed_premise = any(str(c.get("target", "")).startswith("premise:") for c in landed)
    overridden = None
    if term_head(v) == "decline" and not landed_premise:
        overridden, v = v, (f"admit-amended({amendment})" if amendment else "admit")
    note = f"; the adjudicator's {overridden} was overridden: a decline stands only on an upheld premise kill" if overridden else ""
    act = store.registry.route("adjudicator-verdict", v, ADJUDICATION)
    entry = LedgerEntry(
        id=store.mint("hypothesis"), at=now(), species="attack", subject=draft.uid, claim=claim,
        proposer=RoleCall(role="consolidator", model_id=_model.model_id("consolidator"), call=record.brief.get("consolidator_call")),
        contradiction={"source": {"role": "examiner", "model_id": examiner.model_id, "call": examiner.call}, "attack": attack_payload,
                       "coding": {"promotion": promotion} if promotion else None},
        verdict="premise-killed" if term_head(v) == "decline" else store.registry.route("adjudicator-verdict", v, ATTACK_VERDICTS),
        adjudicator=RoleCall(role="adjudicator", model_id=adjudicator.model_id, call=adjudicator.call),
        amendment=amendment or (draft.body.decision if promotion else None), rationale=rationale, rung=nomination.rung,
    )
    role = RoleCall(role="adjudicator", model_id=adjudicator.model_id, call=adjudicator.call)
    if act == "admit":
        floor = [f for f in _lint.check_draft(store, draft) if f.level == "fail"]
        if floor:
            entry.outcome = "refused by the floor: " + "; ".join(f.message for f in floor) + note
            store.drop_draft(draft.uid)
        else:
            admission_entry = entry.model_copy(update={"verdict": v})
            decision = store.admit(draft, admission_entry, role, amendment={"decision": amendment} if v.startswith("admit-amended") and amendment else None)
            record.flipped += [r for r in draft.retires if r not in record.flipped]
            record.admitted.append(decision.id)
            entry.outcome = f"admitted {decision.id}" + ("; the payload was promoted on the examiner's abstraction claim" if promotion else "") + note
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

OPERATED_RUNGS = frozenset({*EDIT_RUNGS, "new-decision"})
"""The rungs this roster has an operator for. The case leg drafts decisions and their successors; ``adoption-row`` and
``rule-enrollment`` need the rule tier, ``floor`` a lint check authored by hand, ``article`` an eviction under the cap."""

DISPLACED_TO = "new-decision"
"""Where a nomination at a rung with no operator lands: the decision is the cheapest *available* home in this roster, so a
lesson a rule, a floor or an article would carry is carried as a decision rather than lost — the ladder's cheapest
sufficient home, read over the homes that exist. The rung it meant travels with it (``displaced_from``) and is stamped on
the admitted record, so a later tier can find what stands in for it and re-home it; a mis-placed record that fires beats a
well-placed record that was never written. A nomination with no sketch to carry as a decision is still refused."""


def displacement(rung: str) -> str | None:
    """The rung a nomination at ``rung`` is displaced from in this roster, or ``None`` when the rung has an operator."""
    return None if rung in OPERATED_RUNGS else rung


def orphaned_edit(store: Store, rung: str, raw: dict[str, Any]) -> bool:
    """Whether an edit-rung nomination names no record and the store holds none to edit.

    An edit rung supersedes exactly one existing record; when it comes back with an empty ``supersedes`` and the store
    holds no decision at all, there is nothing to refine, so the nomination is a new decision wearing an edit's rung.
    It is displaced to ``new-decision`` (:data:`DISPLACED_TO`) rather than refused at parse — the lesson is carried
    where it can fire. When decisions do exist and none is named, the edit is refused as before (see :func:`edited_body`)."""
    return rung in EDIT_RUNGS and not (raw.get("supersedes") or []) and not store.decisions()


def anchor_terms(store: Store, evidence: list[str]) -> list[str]:
    """The task-declared work-shape terms of the tasks the evidence observations were noticed on.

    A record's hook is the drafter's reading of the group's coded shape — the blind coder's coding of how the work
    presented (``test-failure-triage``), which need not name what the task is about (``http-tool``). The boot index
    matches a record to a task only where their work-shape terms intersect, so a record learned from an http-tool task
    but hooked on the coder's shape never fires on the next http-tool task. The task's own terms are its declared
    ``shapes`` (``suite.Task.shapes``); an observation's anchor call resolves to the evaluation row it was noticed on,
    and that row names the task. Seed the hook with those shapes so a record is retrievable for the tasks it was
    learned from (economy-run item 39). Only registered work-shape terms are returned, so the derived body still parses."""
    calls = {o.anchor.call for e in evidence if (o := store.observation(e)) is not None and o.anchor.call}
    if not calls:
        return []
    tasks = {row.get("task") for s in store.all("session") if s.attached and s.evaluation  # type: ignore[attr-defined]
             for row in s.evaluation.rows if row.get("call") in calls and row.get("task")}  # type: ignore[attr-defined]
    registered = set(store.registry.terms("work-shape"))
    by_id = {t.id: t for t in _suite.current().tasks}
    return sorted({sh for tid in tasks for sh in getattr(by_id.get(tid), "shapes", ()) if sh in registered})


def sketch_body(store: Store, raw: dict[str, Any]) -> dict[str, Any]:
    """A draft's body derived from the consolidator's sketch under the store's bars.

    A lineage move (split or fold) instead carries a body derived mechanically from the records it
    leaves — that derived body is used as given; it is the code's, not a role writing mechanism by hand.
    A nomination with neither a sketch nor a derived body is a failing field, never a placeholder.

    The consultation hook is seeded with the tasks' own declared work-shape terms (:func:`anchor_terms`), on top of the
    terms the drafter chose, so the record is retrievable for the tasks it was learned from.
    """
    from hgi.drafting import body as _body_from_sketch
    from hgi.drafting import sketch_of

    if raw.get("sketch") is not None:
        sketch = sketch_of(raw.get("sketch"), store.registry)
        evidence = [e for e in raw.get("evidence", []) if isinstance(e, str)]
        seeded = list(dict.fromkeys([*sketch.terms, *anchor_terms(store, evidence)]))
        if seeded != list(sketch.terms):
            sketch = sketch.model_copy(update={"terms": seeded})
        return _body_from_sketch(sketch, evidence, store.registry.bars, _model.model_id("pass"))
    if raw.get("split_from") or raw.get("folded_from"):  # a lineage move derives its body from the records it leaves, not from a sketch
        derived = raw.get("body")
        if isinstance(derived, str):
            derived = json.loads(derived)
        if isinstance(derived, dict):
            return derived
    raise ValueError("sketch: a drafting reply carries a `sketch` object")


def edited_body(store: Store, raw: dict[str, Any]) -> dict[str, Any]:
    """A successor's body for an edit rung: the one superseded record's body with the rung's fields replaced — a refinement is a successor record, never a rewrite.

    A non-edit rung's body is derived from the sketch instead; the record's mechanism is the code's to derive, never the role's to write.
    """
    rung, edit = raw.get("rung"), raw.get("edit") or {}
    if rung not in EDIT_RUNGS:
        return sketch_body(store, raw)
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
    """A draft from a nomination: the body derived from the sketch (or the superseded record for an edit rung), the lineage
    move recorded in ``split_from``/``folded_from``, and the anchors inherited from what it retires when it names none of its own."""
    retires = [*(raw.get("supersedes") or []), *(raw.get("folded_from") or []), *([raw["split_from"]] if raw.get("split_from") else [])]
    return store.parse_as(Draft, {"uid": store.new_uid(), "name": store.next_name("P"), "kind": "decision", "drafted_at": now().isoformat(),
                                  "proposed_by": record.id, "rung": raw.get("rung"), "rung_why": raw.get("rung_why") or "", "displaced_from": raw.get("displaced_from"),
                                  "body": edited_body(store, raw),
                                  "evidence": list(raw.get("evidence") or []) or inherited_evidence(store, retires),
                                  "supersedes": list(raw.get("supersedes") or []),
                                  "split_from": raw.get("split_from") or None, "folded_from": list(raw.get("folded_from") or [])})


def adoptable(store: Store, raw: dict[str, Any]) -> Draft | None:
    """The open draft a nomination adopts, when it names one that exists; a name that matches nothing is not an adoption."""
    uid = raw.get("adopts")
    if not isinstance(uid, str) or not uid:
        return None
    return next((d for d in store.drafts() if d.uid == uid), None)


def expire_proposals(store: Store, record: Consolidation) -> list[str]:
    """A pass proposal no consolidation adopted is dropped once ``proposal_ttl_consolidations`` consolidations have run since it was drafted."""
    ttl = store.registry.bars.get("proposal_ttl_consolidations")
    if ttl is None:
        return []
    started = [k.started_at for k in store.all("consolidation")] + [record.started_at]  # type: ignore[attr-defined]
    expired = []
    for d in store.drafts():
        if not d.proposed_by.startswith("S-"):
            continue  # a deferred draft of the backward pass is kept by its own condition
        if sum(1 for at in started if at > d.drafted_at) >= ttl:
            store.drop_draft(d.uid)
            expired.append(d.uid)
    return expired


def nomination_from(store: Store, raw: dict[str, Any]) -> Nomination:
    """The nomination as the consolidator stated it; a rung outside the ladder is kept as an escape so the refusal is recorded, not lost."""
    rung = str(raw.get("rung") or "")
    try:
        store.registry.check("ladder-rung", rung)
    except ValueError:
        rung = f"other({rung or 'no rung'})"
    return Nomination(rung=rung, rung_why=str(raw.get("rung_why") or ""), subject=str(raw.get("subject") or "(unnamed)"),
                      evidence=[e for e in raw.get("evidence", []) if isinstance(e, str)])


# --- credit, fires, retirement --------------------------------------------------------------

def credit(store: Store, record: Consolidation, brief: dict[str, Any], sessions: list[Session]) -> list[Steer]:
    """Oracle-attributed steers: the adjudicator performs credit assignment on a regression, never the pass that produced it.

    The regression is mechanical — a record applied in the window whose
    applied tasks passed no more often than before — and only those rows
    reach the adjudicator, which names the slot; a record whose tasks
    improved is not a candidate and earns no steer.
    """
    regressions = [a for a in brief["credit"] if a["applied_count"] > 0 and a["before"] is not None and a["after"] <= a["before"]]
    if not regressions:
        return []
    c = _model.complete("adjudicator", roles.request("credit", applied=regressions, empty_is_legal=roles.EMPTY_STEER_IS_LEGAL), session=record.id)
    fired_on = {f.latch.record for f in store.all("fire") if any(f.edge_event.pass_ == s.pass_ for s in sessions)}  # type: ignore[attr-defined]
    out = []
    candidates = {a["record"] for a in regressions}
    out_json = c.json()
    for s in (out_json.get("steers", []) if isinstance(out_json, dict) else []):
        if not isinstance(s, dict) or s.get("record") not in candidates or not s.get("correction"):
            continue  # a steer names a regressed record and says what it got wrong; anything else is not a steer
        steer = Steer(id=store.mint("steer"), at=now(), source={"kind": "oracle", "anchor": c.call}, correction=str(s["correction"]),
                      indicts={"record": s["record"], "slot": s.get("slot") or "payload", "signature": s.get("signature") or "recalled-applied-still-corrected"},
                      why_not_caught=s.get("why_not_caught"),
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
    """The adjudicator re-checks a warrant; the currency entry is appended with its verdict.

    The fire is the contradictor — the world moved and said so — the committer that owes the fire its disposition is
    the proposer of the standing claim, and the adjudicator alone verdicts: three parties, no collapse.
    """
    c = _model.complete("adjudicator", roles.request("currency", record=d.id, fire=f.model_dump(by_alias=True, mode="json"), **content), session=record.id)
    out = c.json()
    v = str(out.get("verdict", "pending"))
    entry = LedgerEntry(id=store.mint("hypothesis"), at=now(), species="currency", subject=d.id, claim=claim,
                        proposer=RoleCall(role="committer", model_id=None, call=None),
                        contradiction={"source": {"role": "oracle", "model_id": None, "call": f.id}, "coding": coding},
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


def pending_contradictions(store: Store) -> list[LedgerEntry]:
    """The close-time contradictions nobody has adjudicated: pending currency entries on accepted decisions that no later entry cites."""
    entries = store.all("hypothesis")
    consumed = {e.contradiction.coding.get("pending") for e in entries if isinstance(e.contradiction.coding, dict)}  # type: ignore[attr-defined]
    return [e for e in entries if e.species == "currency" and e.verdict == "pending" and e.adjudicator is None  # type: ignore[attr-defined]
            and e.id not in consumed and store.exists("decision", e.subject) and store.read("decision", e.subject).status == "accepted"]  # type: ignore[attr-defined]


def readjudicate_pending(store: Store, record: Consolidation) -> list[LedgerEntry]:
    """Every pending contradiction the passes filed at close (L-0003) reaches the adjudicator: a ledger with no consumer is a graveyard.

    The pass contradicted a standing record from its own streams — self-noticed signal, the lowest-trust class — so the
    pending entry never settles anything by itself: the adjudicator re-checks the warrant against the finding and the
    verdict lands on a new entry that cites the pending one, the pending line staying as the history of the claim.
    """
    out = []
    for pending in pending_contradictions(store):
        d: Decision = store.read("decision", pending.subject)  # type: ignore[assignment]
        finding = pending.contradiction.coding if isinstance(pending.contradiction.coding, dict) else {"what_changed": pending.claim}
        c = _model.complete("adjudicator", roles.request("currency", record=d.id, claim=pending.claim, finding=finding,
                                                         premises=[p.model_dump() for p in d.warrant.premises]), session=record.id)
        out_ = c.json()
        v = str(out_.get("verdict", "pending"))
        entry = LedgerEntry(id=store.mint("hypothesis"), at=now(), species="currency", subject=d.id, claim=pending.claim,
                            proposer=pending.proposer, contradiction={"source": pending.contradiction.source.model_dump(), "coding": {"pending": pending.id, "finding": finding}},
                            verdict=v, adjudicator=RoleCall(role="adjudicator", model_id=c.model_id, call=c.call), outcome=out_.get("why"))
        store.append(entry)
        entry.outcome = f"{entry.outcome or ''}; {settle_currency(store, record, d, out_, entry)}".strip("; ")
        record.nominations.append(Nomination(rung="counterfactual-edit", rung_why="a pass contradicted the warrant at close; the adjudicator re-checks it",
                                             subject=d.id, evidence=[pending.id], ledger_entry=entry.id, outcome=entry.outcome))
        out.append(entry)
    return out


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
    brief = consolidation_brief(store, record, sessions, analyst_report)
    brief["triage"] = triage(store, record, brief)
    record.brief = {k: v for k, v in brief.items() if k != "groups"} | {"groups": [{k: v for k, v in g.items() if k != "observations"} | {"observations": [o["name"] if isinstance(o, dict) else o for o in g.get("observations", [])]} for g in brief["groups"]]}

    with tracing.attributes(session=record.id, role="consolidator"):
        for raw in nominate(store, record, brief):
            nomination = nomination_from(store, raw)
            adopted = adoptable(store, raw)
            displaced = displacement(nomination.rung)
            orphan = displaced is None and orphaned_edit(store, nomination.rung, raw)
            if adopted is None and (displaced := displaced or (nomination.rung if orphan else None)) is not None:
                why = ("no operator for it in this roster" if not orphan
                       else "an edit rung named no record and the store holds none to edit")
                nomination.displaced_from, nomination.rung = displaced, DISPLACED_TO
                nomination.rung_why = f"displaced from {displaced}: {why}, so the lesson is carried as a decision; " + nomination.rung_why
                raw = {**raw, "rung": DISPLACED_TO, "rung_why": nomination.rung_why, "displaced_from": displaced}
            if adopted is not None:
                nomination.adopts = adopted.uid
                draft = adopted
            else:
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
    readjudicate_pending(store, record)
    record.expired = expire_proposals(store, record)
    steers = credit(store, record, brief, sessions)
    record.nominations += _reviews.retirement(store, record)
    record.nominations += _reviews.genesis_anchors(store, record)
    record.nominations += _reviews.lenses(store, record)
    record.nominations += _reviews.vocabulary(store, record)
    record.nominations += _reviews.ports(store, record)
    propagate(store, record)
    record.closed_at = now()
    store.write(record)
    print(report(record, steers))
    return record


def report(record: Consolidation, steers: list[Steer]) -> str:
    lines = [f"== {record.id} after pass {record.after_pass} — read {', '.join(record.sessions_read) or 'nothing'} ==",
             "triage: " + ("; ".join(f"{t['shape']} {t['verdict']} → {t['ledger_entry']}" for t in record.brief.get("triage", [])) or "no group at the bar"),
             "groups: " + ("; ".join(f"{g['shape']} ← {', '.join(g['observations'])}" for g in record.brief.get("groups", [])) or "none")]
    for n in record.nominations:
        lines.append(f"nominated {n.rung} on {n.subject} ({', '.join(n.evidence)})" + (f" adopting {n.adopts}" if n.adopts else "") + f" → {n.ledger_entry}: {n.outcome}")
    lines.append(f"steers: {', '.join(f'{t.id} {t.indicts.record if t.indicts else ''} [{t.matrix_cell}]' for t in steers) or 'none'}")
    lines.append(f"fires discharged: {', '.join(record.fires_discharged) or 'none'}; admitted: {', '.join(record.admitted) or 'none'}; "
                 f"flipped: {', '.join(record.flipped) or 'none'}; deferred: {', '.join(record.deferred) or 'none'}; anchored: {', '.join(record.anchored) or 'none'}; "
                 f"minted: {', '.join(record.minted) or 'none'}"
                 + (f"; proposals expired: {', '.join(record.expired)}" if record.expired else "")
                 + (f"; dismissed as irreducible: {', '.join(record.dismissed)}" if record.dismissed else "")
                 + (f"; lenses retired: {', '.join(record.retired)}" if record.retired else ""))
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
