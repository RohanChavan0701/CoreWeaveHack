"""§ 8.6 — close. ``hgi close --session S-nnnn`` produces the backward pass's inputs:

1. reflect, streams first — the close lenses walk against the session's
   typed event streams (fires, the evaluation rows) before free recall;
2. dispositions — every consulted record receives a use-time disposition,
   or the close is refused;
3. observations file with anchors; caught contradictions file to the ledger
   with the verdict ``pending``;
4. steer capture — feedback on the session's calls lands as steer records;
5. proposals — candidate records drafted into the pre-admission tier;
6. the session record closes with its ``carry_forward``.

Boot consumes what the backward pass produced; close produces what it will
consume. That closure is the system.
"""

from __future__ import annotations

import json
from typing import Any

from hgi import boot as _boot
from hgi import index as _index
from hgi import model as _model
from hgi import roles
from hgi import steers as _steers
from hgi import tracing
from hgi.store import Store, now
from hgi.types import Decision, Disposition, Draft, LedgerEntry, Observation, RoleCall, Session

NO_HOOK = "none"
"""The record a fired-off-map disposition names when the work matched no hook at all."""


def _decision_view(store: Store, record: str) -> dict[str, Any]:
    d: Decision = store.read("decision", record)  # type: ignore[assignment]
    return {"record": d.id, "decision": d.decision, "terms": d.consultation_terms, "not_this": d.consultation_not_this,
            "premises": [p.model_dump() for p in d.warrant.premises]}


def dispose(store: Store, session: Session) -> list[Disposition]:
    """Step 2. One disposition per consulted record; guard-failed considerations are telemetry, written too."""
    rows = session.evaluation.rows if session.evaluation else []
    consulted = [_decision_view(store, c.record) for c in session.consulted]
    verdicts: dict[str, dict[str, Any]] = {}
    if consulted:
        c = _model.complete("pass", roles.request("dispose", consulted=consulted, rows=rows, vocabulary=store.registry.terms("use-time-disposition")),
                            session=session.id, pass_=session.pass_, records_in_context=[x["record"] for x in consulted])
        verdicts = {v["record"]: v for v in c.json().get("dispositions", [])}
    out = []
    for c in session.consulted:
        v = verdicts.get(c.record)
        if v is None:
            continue  # left undisposed on purpose: the completeness check below refuses the close
        u = Disposition(id=store.mint("disposition"), session=session.id, record=c.record, considered=True, guard_passed=True,
                        disposition=v["disposition"], note=v.get("note"))
        store.append(u)
        c.disposition = u.id
        out.append(u)
    for k in session.considered:
        if k.via != "constitution" and not k.guard_passed:
            u = Disposition(id=store.mint("disposition"), session=session.id, record=k.record, considered=True, guard_passed=False,
                            disposition="guard-failed", note=f"nominated via {k.via}: {', '.join(k.terms_matched)}")
            store.append(u)
            out.append(u)
    if not session.consulted and any(r.get("error") for r in rows):
        u = Disposition(id=store.mint("disposition"), session=session.id, record=NO_HOOK, considered=False, guard_passed=False,
                        disposition="fired-off-map", note="work failed and matched no hook")
        store.append(u)
        out.append(u)
    return out


def file_observations(store: Store, session: Session) -> list[Observation]:
    """Step 3a. Each L-0004 finding with an anchor becomes an observation; a finding with no anchor is not filed."""
    out = []
    for answer in session.lens_answers:
        if answer.lens != "L-0004":
            continue
        for f in answer.findings:
            anchor = dict(f.get("anchor") or {})
            if not any(anchor.values()):
                continue
            o = Observation(uid=store.new_uid(), name=store.next_name("O"), noticed_at=now(), session=session.id,
                            noticed=f["noticed"], anchor=anchor, recheck_when=f.get("recheck_when"))
            store.write(o)
            session.observations_filed.append(o.name)
            out.append(o)
    return out


def file_contradictions(store: Store, session: Session) -> list[LedgerEntry]:
    """Step 3b. Each L-0003 finding naming a record and a slot files as a currency entry, verdict pending."""
    out = []
    for answer in session.lens_answers:
        if answer.lens != "L-0003":
            continue
        for f in answer.findings:
            if not f.get("record") or not store.find(f["record"]):
                continue
            entry = LedgerEntry(id=store.mint("hypothesis"), at=now(), species="currency", subject=f["record"],
                                claim=f"{f.get('slot', 'warrant')}: {f.get('what_changed', '')}",
                                proposer=RoleCall(role="pass", model_id=session.model_id, call=answer.call),
                                contradiction={"source": {"role": "pass", "model_id": session.model_id, "call": answer.call}, "coding": f})
            store.append(entry)
            session.ledger_entries.append(entry.id)
            out.append(entry)
    return out


def propose(store: Store, session: Session) -> list[Draft]:
    """Step 5. The pass proposes; nothing it proposes is yet true. A draft that fails to parse is not filed."""
    rows = session.evaluation.rows if session.evaluation else []
    c = _model.complete("pass", roles.request("propose", observations=session.observations_filed, rows=rows, bars=store.registry.bars,
                                              rungs=store.registry.terms("ladder-rung"), vocabularies=store.registry.vocabulary_terms(), model_id=_model.model_id("pass"), empty_is_legal=roles.EMPTY_IS_LEGAL),
                        session=session.id, pass_=session.pass_)
    out = []
    for raw in roles.drafts_in(c.json(), "drafts"):
        try:
            draft = store.parse_as(Draft, {**raw, "body": roles.body_of(raw), "uid": store.new_uid(), "name": store.next_name("P"),
                                           "drafted_at": now().isoformat(), "proposed_by": session.id})
        except ValueError as e:
            print(f"draft refused: {roles.refusal(e)}")
            continue
        store.write_draft(draft)
        session.proposals.append(draft.uid)
        out.append(draft)
    return out


def carry_forward(store: Store, session: Session, dispositions: list[Disposition]) -> str:
    scores = {k: ("unevaluable" if f.value is None else round(f.value, 2)) for k, f in (session.evaluation.scores if session.evaluation else {}).items()}
    open_fires = [f["id"] for f in _index.undischarged_fires(store)]
    consulted = ", ".join(f"{u.record} {u.disposition}" for u in dispositions if u.guard_passed) or "nothing"
    return (f"pass {session.pass_} scored {scores}; consulted {consulted}; filed {len(session.observations_filed)} observations "
            f"({', '.join(session.observations_filed) or 'none'}); open fires: {', '.join(open_fires) or 'none'}")


def close(store: Store, session_id: str) -> Session:
    tracing.init()
    session: Session = store.read("session", session_id)  # type: ignore[assignment]
    if session.closed_at is not None:
        raise SystemExit(f"{session.id} is already closed")
    if session.evaluation is None:
        raise SystemExit(f"{session.id} has not been evaluated; run hgi evaluate first")

    rows = session.evaluation.rows
    session.lens_answers += _boot.walk_lenses(store, session, "close", lambda lens: {
        "consulted": [_decision_view(store, c.record) for c in session.consulted],
        "rows": rows, "fires": session.fires_seen,
        "scores": {k: f.value for k, f in session.evaluation.scores.items()},
    })
    dispositions = dispose(store, session)
    missing = [c.record for c in session.consulted if c.disposition is None]
    if missing:
        raise SystemExit(f"close refused [disposition-completeness]: consulted records without a disposition: {', '.join(missing)}")
    file_observations(store, session)
    file_contradictions(store, session)
    _steers.capture(store, session)
    propose(store, session)
    session.carry_forward = carry_forward(store, session, dispositions)
    session.closed_at = now()
    store.write(session)
    print(report(session, dispositions))
    return session


def report(session: Session, dispositions: list[Disposition]) -> str:
    consulted = [u for u in dispositions if u.guard_passed]
    return "\n".join([
        f"== {session.id} closed ==",
        f"consulted {len(consulted)}: " + (", ".join(f"{u.record} {u.disposition}" for u in consulted) or "none"),
        f"observations filed: {', '.join(session.observations_filed) or 'none'}",
        f"ledger entries: {', '.join(session.ledger_entries) or 'none'}; steers: {', '.join(session.steers_filed) or 'none'}; proposals: {len(session.proposals)}",
        f"carry-forward: {session.carry_forward}",
    ])


def register(add, store_of, finish) -> None:
    p = add("close", "dispositions, observations, steers, proposals, the session record")
    p.add_argument("--session", required=True)
    p.set_defaults(fn=lambda args: _cmd(args, store_of, finish))


def _cmd(args, store_of, finish) -> int:
    store = store_of(args)
    session = close(store, args.session)
    filed = " ".join(session.observations_filed + session.ledger_entries + session.steers_filed)
    finish(store, args, f"Close {session.id} pass {session.pass_}" + (f": filed {filed}" if filed else ""))
    return 0
