"""The scheduled reviews of the backward pass: each a mechanical nominator whose verdict is the adjudicator's.

Every threshold pairs with a scheduled reverse (§ 10.8), and every seed earns
its place or leaves (§ 13.4). The reviews here walk a projection or a
register, nominate on what they find, and hand each nomination to the
adjudicator in its own context; the committer acts on the verdict and the
ledger records the pair. None of them settles anything by count.

- :func:`retirement` — applied ÷ considered below a record's retirement
  guard over the review window nominates mootness; the adjudicator's
  killer-item check decides.
- :func:`genesis_anchors` — a genesis article carries ``warrant.evidence:
  genesis`` and no anchor; the consolidator proposes an instance from the
  loop's own ledgers, the adjudicator says whether it exemplifies the
  article, and an article still unanchored past the deadline is evicted.
- :func:`vocabulary` — the route-before-mint ladder's last rung for a term:
  the same ``other(<what>)`` escape from independent passes nominates it, the
  blind coder recodes the presentations with the candidate withheld, the
  adjudicator admits or declines, and the committer mints through the
  registry.
"""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Any

from hgi import coder as _coder
from hgi import index as _index
from hgi import model as _model
from hgi import roles
from hgi.registry import ESCAPE, is_escape
from hgi.store import Store, now
from hgi.types import Consolidation, ConstitutionArticle, Decision, LedgerEntry, Nomination, RoleCall


def _entry(store: Store, *, subject: str, claim: str, proposer: RoleCall, c: _model.Completion, verdict: str, coding: dict[str, Any],
           why: str | None, rung: str | None = None) -> LedgerEntry:
    """A currency entry as every review leaves it: the nominator as proposer, the adjudicator's call on the contradiction and the verdict."""
    entry = LedgerEntry(id=store.mint("hypothesis"), at=now(), species="currency", subject=subject, claim=claim, proposer=proposer,
                        contradiction={"source": {"role": "adjudicator", "model_id": c.model_id, "call": c.call}, "coding": coding},
                        verdict=verdict, adjudicator=RoleCall(role="adjudicator", model_id=c.model_id, call=c.call), outcome=why, rung=rung)
    store.append(entry)
    return entry


# --- retirement --------------------------------------------------------------------------------

def retirement(store: Store, record: Consolidation) -> list[Nomination]:
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
        out_ = c.json()
        v = out_.get("verdict", "still-holds")
        entry = _entry(store, subject=d.id, claim=f"{d.id} applied ÷ considered = {row['applied_over_considered']:.2f} over {row['passes_in_window']} passes",
                       proposer=RoleCall(role="consolidator", model_id=None, call=None), c=c, verdict=v, coding=row, why=out_.get("why"), rung="counterfactual-edit")
        n = Nomination(rung="counterfactual-edit", rung_why="retirement leg: the nominating ratio fell below the guard", subject=d.id,
                       evidence=[f"applied_over_considered={row['applied_over_considered']}"], ledger_entry=entry.id, outcome=v)
        if v == "moot":
            store.flip_status(d, "moot", by=record.id)
            record.flipped.append(d.id)
        out.append(n)
    return out


# --- genesis anchoring ---------------------------------------------------------------------------

def instances(store: Store) -> dict[str, list[dict[str, Any]]]:
    """The loop's own history, as the instances a genesis article may be anchored to — ids and cues, never a narrative."""
    hypotheses = []
    for e in store.all("hypothesis"):
        attack = e.contradiction.attack  # type: ignore[attr-defined]
        hypotheses.append({"id": e.id, "species": e.species, "subject": e.subject, "verdict": e.verdict, "outcome": e.outcome,  # type: ignore[attr-defined]
                           "roles": sorted({e.proposer.role, e.contradiction.source.role, *( [e.adjudicator.role] if e.adjudicator else [])}),  # type: ignore[attr-defined]
                           "attack_targets": [c.target for c in attack.claims] if attack else []})
    return {
        "observations": [{"name": o.name, "session": o.session, "state": o.disposition.state, "anchor": o.anchor.model_dump(exclude_none=True)} for o in store.observations(state=None)],
        "hypotheses": hypotheses,
        "decisions": [{"id": d.id, "status": d.status, "superseded_by": d.lineage.superseded_by, "residue": d.enforcement.residue,
                       "retirement_guard": d.lifecycle.retirement.guard.model_dump(exclude_none=True, exclude_defaults=True),
                       "admitted_by": d.admission.proposed_by, "ledger_entry": d.admission.ledger_entry} for d in store.decisions()],
        "dispositions": [{"id": u.id, "session": u.session, "record": u.record, "disposition": u.disposition} for u in store.all("disposition")][-20:],  # type: ignore[attr-defined]
        "steers": [{"id": t.id, "indicts": t.indicts.model_dump() if t.indicts else None, "matrix_cell": t.matrix_cell} for t in store.all("steer")],  # type: ignore[attr-defined]
        "fires": [{"id": f.id, "record": f.latch.record, "disposer": f.disposer, "outcome": f.disposition.outcome} for f in store.all("fire")],  # type: ignore[attr-defined]
        "unevaluable_facts": [{"session": s.id, "series": k, "unevaluable": f.unevaluable} for s in store.all("session") if s.evaluation  # type: ignore[attr-defined]
                              for k, f in s.evaluation.scores.items() if f.unevaluable],  # type: ignore[attr-defined]
        "sessions": [{"id": s.id, "pass": s.pass_, "consulted": len(s.consulted), "proposals": len(s.proposals), "observations": len(s.observations_filed)}  # type: ignore[attr-defined]
                     for s in store.all("session") if s.attached],  # type: ignore[attr-defined]
    }


def resolve(store: Store, anchor: str) -> dict[str, Any] | None:
    """What an anchor names, as the adjudicator reads it: the record itself, a ledger line, or the URI as given."""
    if anchor.startswith("weave:///"):
        return {"uri": anchor}
    record = store.find(anchor) or store.observation(anchor)
    if record is not None:
        return record.model_dump(mode="json", by_alias=True)
    for kind in ("hypothesis", "disposition", "steer"):
        for line in store.all(kind):
            if line.id == anchor:  # type: ignore[attr-defined]
                return line.model_dump(mode="json", by_alias=True)
    return None


def genesis_anchors(store: Store, record: Consolidation) -> list[Nomination]:
    """Genesis articles earn an anchor from the loop's own history by the deadline, or are evicted.

    The consolidator proposes one instance per unanchored article; the
    adjudicator, reading the instance itself, says whether it exemplifies the
    article; the committer appends the anchor. Past the deadline (the bars'
    ``genesis_anchor_deadline_consolidations``, counting the passes before
    this one), every article still unanchored after this attempt is evicted —
    the always-loaded tier is the only fixed-width layer, and a seed that the
    loop's history never instantiates does not keep a seat in it.
    """
    unanchored = [a for a in store.articles() if a.warrant.evidence == "genesis" and not a.warrant.anchors]
    if not unanchored:
        return []
    c = _model.complete("consolidator", roles.request("anchor", articles=[{"id": a.id, "article": a.article, "counterfactual": a.counterfactual} for a in unanchored],
                                                      instances=instances(store), empty_is_legal=roles.EMPTY_IS_LEGAL), session=record.id)
    proposals = {p["article"]: p for p in roles.drafts_in(c.json(), "anchors") if p.get("article") and p.get("anchor")}
    out = []
    for article in unanchored:
        proposal = proposals.get(article.id)
        n = Nomination(rung="article", rung_why="genesis anchoring: a seed article earns an anchor from the loop's own history or is evicted",
                       subject=article.id, evidence=[proposal["anchor"]] if proposal else [])
        if proposal is None:
            n.outcome = "no instance proposed"
        elif (instance := resolve(store, str(proposal["anchor"]))) is None:
            n.outcome = f"refused: {proposal['anchor']} names nothing in the store"
        else:
            v_call = _model.complete("adjudicator", roles.request("exemplifies", article={"id": article.id, "article": article.article, "counterfactual": article.counterfactual},
                                                                  anchor=proposal["anchor"], instance=instance), session=record.id)
            verdict = v_call.json()
            v = str(verdict.get("verdict", "moot"))
            entry = _entry(store, subject=article.id, claim=f"{article.id} is exemplified by {proposal['anchor']}",
                           proposer=RoleCall(role="consolidator", model_id=c.model_id, call=c.call), c=v_call, verdict=v,
                           coding={"anchor": proposal["anchor"], "why": proposal.get("why")}, why=verdict.get("why"), rung="article")
            n.ledger_entry = entry.id
            if v == "still-holds":
                store.anchor_article(article, str(proposal["anchor"]))
                record.anchored.append(article.id)
                n.outcome = f"anchored to {proposal['anchor']}"
            else:
                n.outcome = f"{v}: not anchored"
        out.append(n)
    deadline = store.registry.bars.get("genesis_anchor_deadline_consolidations", 3)
    if len(store.all("consolidation")) >= deadline:
        for article in unanchored:
            if article.id not in record.anchored:
                store.evict_article(store.read("constitution", article.id))  # type: ignore[arg-type]
                record.flipped.append(article.id)
                next(n for n in out if n.subject == article.id).outcome += f"; evicted past the {deadline}-consolidation deadline"
    return out


# --- vocabulary growth ----------------------------------------------------------------------------

TERM = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
"""The shape a registered term takes; an escape's ``what`` is normalised to it before it can be minted."""


def term_of(escape: str) -> str | None:
    m = ESCAPE.match(escape.strip())
    if not m:
        return None
    what = re.sub(r"[\s_]+", "-", m.group(1).strip().lower())
    return what if TERM.match(what) else None


def escape_clusters(store: Store, vocab: str = "work-shape") -> list[dict[str, Any]]:
    """Same-shaped escapes across attached passes, with the sessions that made them — the recurrence counter, never the verdict.

    An escape already adjudicated counts again only from passes after the
    consolidation that adjudicated it, so a declined term is re-nominated by
    new recurrence and not by the same two sessions forever.
    """
    adjudicated: dict[str, int] = {}
    for e in store.all("hypothesis"):
        if e.species == "coding" and e.subject.startswith(f"{vocab}/") and isinstance(e.contradiction.coding, dict):  # type: ignore[attr-defined]
            adjudicated[e.subject.split("/", 1)[1]] = max(adjudicated.get(e.subject.split("/", 1)[1], 0), int(e.contradiction.coding.get("after_pass", 0)))  # type: ignore[attr-defined]
    registered = set(store.registry.terms(vocab))
    seen: dict[str, dict[str, Any]] = defaultdict(lambda: {"sessions": [], "escapes": []})
    for s in sorted((s for s in store.all("session") if s.attached and s.closed_at is not None), key=lambda s: s.pass_):  # type: ignore[attr-defined]
        for escape in s.work_shape.escapes:  # type: ignore[attr-defined]
            what = term_of(escape)
            if what is None or what in registered or s.pass_ <= adjudicated.get(what, 0):  # type: ignore[attr-defined]
                continue
            cluster = seen[what]
            if s.id not in cluster["sessions"]:  # type: ignore[attr-defined]
                cluster["sessions"].append(s.id)  # type: ignore[attr-defined]
            cluster["escapes"].append({"session": s.id, "pass": s.pass_, "escape": escape})  # type: ignore[attr-defined]
    return [{"vocabulary": vocab, "term": what, **c} for what, c in sorted(seen.items())]


def vocabulary(store: Store, record: Consolidation, vocab: str = "work-shape") -> list[Nomination]:
    """Escape recurrence nominates a term; the blind coder contradicts; the adjudicator verdicts; the registry grows."""
    from suite.tasks import presentations

    bar = store.registry.bars.get("vocabulary", {}).get("independent_escapes", 2)
    out = []
    for cluster in escape_clusters(store, vocab):
        if len(cluster["sessions"]) < bar:
            continue
        what = cluster["term"]
        n = Nomination(rung="hook-edit", rung_why=f"escape recurrence: other({what}) from {len(cluster['sessions'])} independent passes; the route-before-mint ladder's last rung for a term",
                       subject=f"{vocab}/{what}", evidence=[e["session"] for e in cluster["escapes"]])
        text = " ".join(p["prompt"] for p in presentations())
        coded, coder_call = _coder.code([{"name": what, "noticed": text}], store.registry.terms(vocab), session=record.id, records_in_context=[])
        coder_terms = coded.get(what, [])
        covered = [t for t in coder_terms if not is_escape(t)]
        c = _model.complete("adjudicator", roles.request("vocabulary", vocabulary=vocab, term=what, escapes=cluster["escapes"], coder=coder_terms,
                                                         existing=store.registry.terms(vocab), bar=bar), session=record.id)
        out_ = c.json()
        v = str(out_.get("verdict", "decline(adjudicator returned no verdict)"))
        store.registry.check("adjudicator-verdict", v)
        admitted = v == "admit"
        entry = LedgerEntry(id=store.mint("hypothesis"), at=now(), species="coding", subject=f"{vocab}/{what}",
                            claim=f"the presentations escaping to other({what}) are one shape no {vocab} term covers",
                            proposer=RoleCall(role="consolidator", model_id=None, call=None),
                            contradiction={"source": {"role": "coder", "model_id": _model.model_id("coder"), "call": coder_call},
                                           "coding": {"coder": coder_terms, "covered_by": covered, "sessions": cluster["sessions"], "after_pass": record.after_pass}},
                            verdict="agree" if admitted else "disagree", adjudicator=RoleCall(role="adjudicator", model_id=c.model_id, call=c.call),
                            outcome=v if not admitted else f"admit: {out_.get('means', '')}", rung="hook-edit")
        store.append(entry)
        n.ledger_entry = entry.id
        if admitted:
            store.registry.add_term(vocab, what, str(out_.get("means") or f"minted from {len(cluster['sessions'])} independent escapes"), since=now().date().isoformat())
            record.minted.append(f"{vocab}/{what}")
            n.outcome = f"minted {vocab}/{what}"
        else:
            n.outcome = v + (f"; the coder read the presentations as {covered}" if covered else "")
        out.append(n)
    return out
