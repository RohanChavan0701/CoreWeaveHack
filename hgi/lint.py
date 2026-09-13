"""The floor. This docstring is the home of the check list.

Each check names its seam, what it fails or warns on, and its residue — what
it does not check. The floor binds mechanically where bindable and directs
attention to the rest by disclosure.

Check                        Seam           Fails / warns                                                              Residue
---------------------------  -------------  -------------------------------------------------------------------------  --------------------------------------------------
schema                       write          fails a record that does not parse against its declared type              truth of any field
closed-vocabulary            write          fails an enum value outside the registry without an other(<what>) escape  whether the escape should have been a term
complement-law               write          fails a decision without falsifiers or a counterfactual, a consultation   whether the pair is non-vacuous
                                            latch without not_this; warns on a counterfactual with no anchor
settlement-test              write          fails a projection cell carrying a compliable sentence                    compliance by omission
verdict-authority            write          fails a proposal or attack payload carrying a verdict; fails a ledger     whether the adjudicator's verdict is right
                                            verdict with no adjudicator call
role-separation              write          fails a ledger entry whose proposer, contradictor and adjudicator are      whether two contexts of one model share a prior
                                            not three distinct roles, or whose two role calls are one call
fire-disposer                write          fails a fire naming no disposer                                           whether the disposer discharged it well
settlement-authority         write          fails a settled latch whose settlement cites no adjudicated ledger entry,  whether the settlement was right
                                            dispositive fire or admitted successor
ports                        write          fails a latch off its port declaration without a warrant; fails a         whether the declaration is right
                                            required latch type that is absent
constitution-cap             write          fails a store exceeding max_articles or max_bytes                         the ranking
disposition-completeness     close          fails a closed session with a consulted record lacking a disposition      whether the disposition was honest
fire-completeness            close          fails a closed session that saw a fire owed to the working pass and left   whether the discharge was honest
                                            it undischarged
projection-coherence         commit         fails when index/ differs from regeneration                               nothing — total
consumer-edge-acyclicity     commit         fails a cycle over wiring edges                                           undeclared edges
model-pricing                boot           warns on a conditioning record (lens, article, decision) priced for a     the size of the re-pricing
                                            model other than the session's, or restamped for it without re-authoring
role-pricing                 boot           warns on a role prompt not priced for the model the role runs on          reading a role's replies on an unread model
oracle-honesty               runtime        fails a fact carrying both a zero value and an unevaluable reason         a scorer measuring the wrong quantity
genesis-anchor               consolidation  warns on a genesis article or lens past its anchor deadline with no        whether the anchor exemplifies the article; whether
                                            anchor                                                                     the lens's product was worth consuming

Two seams lie beyond the lint: the review seam (the examiner over a committed
draft) and the consumption seam (read the record, never only its projection).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from pydantic import ValidationError

from hgi import index as _index
from hgi.registry import read_json
from hgi.store import LAYOUTS, Store
from hgi.types import (
    RECORD_MODELS,
    ConstitutionArticle,
    Decision,
    DecisionBody,
    Draft,
    LedgerEntry,
    QueueEntry,
    Session,
    anchors_in,
)


@dataclass
class Finding:
    check: str
    level: str  # "fail" | "warn"
    record: str | None
    message: str

    def __str__(self) -> str:
        where = f" {self.record}" if self.record else ""
        return f"{self.level.upper():4} [{self.check}]{where}: {self.message}"


@dataclass
class Check:
    name: str
    seam: str
    residue: str
    fn: Callable[..., list[Finding]]


CHECKS: dict[str, Check] = {}


def check(name: str, seam: str, residue: str):
    def deco(fn):
        CHECKS[name] = Check(name, seam, residue, fn)
        return fn
    return deco


def fail(check: str, record: str | None, message: str) -> Finding:
    return Finding(check, "fail", record, message)


def warn(check: str, record: str | None, message: str) -> Finding:
    return Finding(check, "warn", record, message)


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)

    @property
    def failures(self) -> list[Finding]:
        return [f for f in self.findings if f.level == "fail"]

    @property
    def green(self) -> bool:
        return not self.failures

    def __str__(self) -> str:
        lines = [str(f) for f in self.findings]
        lines.append(f"lint: {'green' if self.green else 'RED'} — {len(self.failures)} failures, {len(self.findings) - len(self.failures)} warnings")
        return "\n".join(lines)


# --- raw parsing: schema, closed-vocabulary, verdict-authority, fire-disposer ---

def _classify_parse_error(kind: str, data: Any, err: Exception) -> str:
    """Route a refused parse to the check whose invariant it broke; ``schema`` is the residual."""
    msg = str(err)
    if "closed vocabulary" in msg:
        return "closed-vocabulary"
    if kind == "fire" and (not isinstance(data, dict) or not data.get("disposer")):
        return "fire-disposer"
    if kind in ("draft", "attack") and _carries_verdict(data):
        return "verdict-authority"
    return "schema"


def _carries_verdict(data: Any) -> bool:
    """Whether a proposal or attack payload carries a verdict other than pending, anywhere in its tree."""
    if isinstance(data, dict):
        v = data.get("verdict")
        if v is not None and v != "pending":
            return True
        return any(_carries_verdict(x) for x in data.values())
    if isinstance(data, list):
        return any(_carries_verdict(x) for x in data)
    return False


def _raw_records(store: Store):
    """Every (kind, path, line, raw) in the store, including drafts, the queue and the lens register."""
    for kind, (directory, layout) in LAYOUTS.items():
        base = store.root / directory
        if layout == "file":
            for p in sorted(base.glob("*.json")):
                yield kind, p, None, read_json(p)
        else:
            p = base / f"{directory}.jsonl"
            if p.exists():
                for n, line in enumerate(p.read_text().splitlines(), start=1):
                    if line.strip():
                        yield kind, p, n, json.loads(line)
    for p in sorted(store.proposals_dir.glob("*.json")):
        yield "draft", p, None, read_json(p)
    for p in sorted(store.queue_dir.glob("*.json")):
        yield "queue", p, None, read_json(p)
    lens_path = store.registry.path("lenses")
    if lens_path.exists():
        for n, item in enumerate(read_json(lens_path)):
            yield "lens", lens_path, n, item


_MODELS = {**RECORD_MODELS, "draft": Draft, "queue": QueueEntry}


@check("schema", "write", "truth of any field")
def check_schema(store: Store) -> list[Finding]:
    out = []
    for kind, path, line, raw in _raw_records(store):
        where = f"{path.name}" + (f":{line}" if line is not None else "")
        try:
            store.parse_as(_MODELS[kind], raw)
        except (ValidationError, ValueError) as e:
            out.append(fail(_classify_parse_error(kind, raw, e), where, _first_line(e)))
        if kind in ("draft",) and _carries_verdict(raw):
            out.append(fail("verdict-authority", where, "a proposal carries a verdict; only the adjudicator's context writes one"))
        if kind == "hypothesis" and isinstance(raw, dict):
            attack = (raw.get("contradiction") or {}).get("attack") or {}
            if attack.get("verdict", "pending") != "pending":
                out.append(fail("verdict-authority", where, "an attack payload carries a verdict other than pending"))
            if raw.get("verdict", "pending") != "pending" and not raw.get("adjudicator"):
                out.append(fail("verdict-authority", where, "a ledger verdict with no adjudicator call"))
    return out


def _first_line(e: Exception) -> str:
    return str(e).strip().splitlines()[0] if str(e).strip() else type(e).__name__


# --- role separation ------------------------------------------------------------------

@check("role-separation", "write", "whether two contexts of one model share a prior")
def check_role_separation(store: Store) -> list[Finding]:
    """Proposer, contradictor and adjudicator are distinct parties on every ledger entry (§ 3.3): each collapse of two is a
    named failure, and a contradictor recorded as the adjudicator grades its own attack. Roles must differ; where two
    parties both carry a call URI, the calls must differ too — one context wearing two role names is one context."""
    out = []
    for e in store.all("hypothesis"):
        e: LedgerEntry
        parties = [("proposer", e.proposer), ("contradictor", e.contradiction.source)] + ([("adjudicator", e.adjudicator)] if e.adjudicator else [])
        for i, (a_name, a) in enumerate(parties):
            for b_name, b in parties[i + 1:]:
                if a.role == b.role:
                    out.append(fail("role-separation", e.id, f"{a_name} and {b_name} are both {a.role!r}; {a_name} = {b_name} is a named collapse of the separation of powers"))
                elif a.call and b.call and a.call == b.call:
                    out.append(fail("role-separation", e.id, f"{a_name} ({a.role}) and {b_name} ({b.role}) cite one call {a.call}; two role names on one context is one context"))
    return out


# --- complement law ---------------------------------------------------------------

def body_findings(id: str, body: DecisionBody) -> list[Finding]:
    """The complement-law findings for a decision body; shared by drafts (the committer's floor) and admitted decisions."""
    out = []
    if not body.warrant.premises or any(not p.falsifier.strip() for p in body.warrant.premises):
        out.append(fail("complement-law", id, "a decision carries premises written as what would refute them"))
    if not body.counterfactual.strip():
        out.append(fail("complement-law", id, "a decision carries a counterfactual — the directive's named overshoot"))
    elif not anchors_in(body.counterfactual):
        out.append(warn("complement-law", id, "the counterfactual cites no anchor; a pair with no anchored instance is priming"))
    for i, latch in enumerate(body.latches):
        if latch.type == "consultation" and not (latch.guard.not_this or body.summary.not_this):
            out.append(fail("complement-law", id, f"consultation latch {i} declares no not-this exclusions"))
    return out


@check("complement-law", "write", "whether the pair is non-vacuous")
def check_complement_law(store: Store) -> list[Finding]:
    out = []
    for d in store.decisions():
        out += body_findings(d.id, d)
    for draft in store.drafts():
        out += body_findings(draft.name, draft.body)
    for a in store.articles():
        if not a.counterfactual.strip():
            out.append(fail("complement-law", a.id, "an article carries a counterfactual"))
    return out


# --- settlement authority ----------------------------------------------------------

@check("settlement-authority", "write", "whether the settlement was right")
def check_settlement_authority(store: Store) -> list[Finding]:
    """A corroborating fire nominates and never settles; every settled latch names what licensed it and the licence holds."""
    out = []
    hosts = [(d.id, d.all_latches()) for d in store.decisions()] + [(p.name, p.all_latches()) for p in store.drafts()]
    for host, latches in hosts:
        for i, latch in enumerate(latches):
            if latch.lifecycle.status != "settled":
                continue
            if not latch.lifecycle.settled_by:
                out.append(fail("settlement-authority", host, f"latch {i} is settled by nothing"))
                continue
            try:
                store.license(latch.lifecycle.settled_by)
            except PermissionError as e:
                out.append(fail("settlement-authority", host, f"latch {i}: {e}"))
    return out


# --- ports ----------------------------------------------------------------------

@check("ports", "write", "whether the declaration is right")
def check_ports(store: Store) -> list[Finding]:
    out = []
    for d in store.decisions():
        live = [l for l in d.all_latches() if l.lifecycle.status == "live"]
        present = {l.type for l in live}
        declared = store.registry.ports.get("decision", {}).get(d.status, {})
        for latch_type, mark in declared.items():
            if mark == "required" and latch_type not in present:
                out.append(fail("ports", d.id, f"a {d.status} decision requires a live {latch_type} latch"))
        for l in live:
            if store.registry.port("decision", d.status, l.type) == "forbidden" and not l.warrant:
                out.append(fail("ports", d.id, f"a live {l.type} latch is forbidden on a {d.status} decision without a warrant on the latch"))
    return out


# --- settlement test ------------------------------------------------------------

def _cells(payload: Any):
    if isinstance(payload, dict):
        yield payload
        for v in payload.values():
            yield from _cells(v)
    elif isinstance(payload, list):
        for v in payload:
            yield from _cells(v)


@check("settlement-test", "write", "compliance by omission")
def check_settlement(store: Store) -> list[Finding]:
    out = []
    for name, fn in _index.PROJECTIONS.items():
        for cell in _cells(fn(store)):
            leaked = sorted(set(cell) & _index.FORBIDDEN_CELL_KEYS)
            if leaked:
                out.append(fail("settlement-test", f"index/{name}", f"a cell carries compliable fields {leaked}; evict them to the record"))
    return out


# --- constitution cap -----------------------------------------------------------

@check("constitution-cap", "write", "the ranking")
def check_cap(store: Store) -> list[Finding]:
    cap = store.registry.constitution_cap
    live = store.articles()
    out = []
    if len(live) > cap["max_articles"]:
        out.append(fail("constitution-cap", None, f"{len(live)} live articles exceed max_articles={cap['max_articles']}; adding an article means evicting one"))
    size = sum(a.size for a in live)
    if size > cap["max_bytes"]:
        out.append(fail("constitution-cap", None, f"{size} bytes of live articles exceed max_bytes={cap['max_bytes']}"))
    return out


def check_article_admissible(store: Store, article: ConstitutionArticle) -> list[Finding]:
    """The cap check for one more article, before it is written."""
    cap = store.registry.constitution_cap
    live = [a for a in store.articles() if a.id != article.id]
    out = []
    if len(live) + 1 > cap["max_articles"]:
        out.append(fail("constitution-cap", article.id, f"an {_ordinal(len(live) + 1)} article exceeds max_articles={cap['max_articles']} without an eviction"))
    if sum(a.size for a in live) + article.size > cap["max_bytes"]:
        out.append(fail("constitution-cap", article.id, f"the article would exceed max_bytes={cap['max_bytes']}"))
    return out


def _ordinal(n: int) -> str:
    return f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


# --- disposition completeness --------------------------------------------------

@check("disposition-completeness", "close", "whether the disposition was honest")
def check_dispositions(store: Store) -> list[Finding]:
    out = []
    have = {u.id for u in store.all("disposition")}
    for s in store.all("session"):
        s: Session
        if s.closed_at is None or not s.attached:
            continue
        for c in s.consulted:
            if c.disposition is None or c.disposition not in have:
                out.append(fail("disposition-completeness", s.id, f"consulted record {c.record} has no use-time disposition"))
    return out


@check("fire-completeness", "close", "whether the discharge was honest")
def check_fires_discharged(store: Store) -> list[Finding]:
    """A fire owed to the working pass is discharged by the pass that saw it, or that pass's close was not a close."""
    from hgi.boot import WORKING_PASS

    out = []
    for s in store.all("session"):
        s: Session
        if s.closed_at is None or not s.attached:
            continue
        for fid in s.fires_seen:
            if not store.exists("fire", fid):
                continue
            f = store.read("fire", fid)
            if f.disposer == WORKING_PASS and not f.disposition.discharged:  # type: ignore[attr-defined]
                out.append(fail("fire-completeness", s.id, f"fire {fid} owed to the working pass was seen at boot and left undischarged at close"))
    return out


# --- projection coherence --------------------------------------------------------

@check("projection-coherence", "commit", "nothing — total")
def check_projections(store: Store) -> list[Finding]:
    return [fail("projection-coherence", f"index/{name}", "committed projection differs from regeneration; run hgi index") for name in _index.check(store)]


# --- acyclicity -----------------------------------------------------------------

@check("consumer-edge-acyclicity", "commit", "undeclared edges")
def check_acyclic(store: Store) -> list[Finding]:
    edges: dict[str, set[str]] = {}
    for d in store.decisions():
        for l in d.all_latches():
            if l.type == "wiring":
                edges.setdefault(d.id, set()).update(l.guard.records)
    out = []
    seen_cycles = set()
    for start in edges:
        stack = [(start, (start,))]
        while stack:
            node, path = stack.pop()
            for nxt in edges.get(node, ()):
                if nxt == start:
                    cyc = tuple(sorted(path))
                    if cyc not in seen_cycles:
                        seen_cycles.add(cyc)
                        out.append(fail("consumer-edge-acyclicity", start, f"wiring cycle {' -> '.join(path)} -> {start}"))
                elif nxt not in path:
                    stack.append((nxt, (*path, nxt)))
    return out


# --- model pricing ------------------------------------------------------------------

@check("model-pricing", "boot", "the size of the re-pricing")
def check_pricing(store: Store, model_id: str | None = None) -> list[Finding]:
    """Warn on a conditioning record the session's model did not condition — priced for another
    model, or restamped for this one without its text being re-authored (:mod:`hgi.price`)."""
    out = []
    if model_id is None:
        return out
    for _, record in store.conditioning():
        priced = record.priced_for
        if priced.model_id != model_id:
            out.append(warn("model-pricing", record.id, f"priced for {priced.model_id!r}, the session runs {model_id!r}"))
        elif priced.authored_for:
            out.append(warn("model-pricing", record.id,
                            f"stamped for {model_id!r} by a re-price; the text is authored for {priced.authored_for!r}"))
    return out


@check("role-pricing", "boot", "reading a role's replies on an unread model")
def check_role_pricing(store: Store, model_id: str | None = None) -> list[Finding]:
    """Warn when a role runs on a model its prompt is not priced for — its replies have not been read back there yet."""
    from hgi import model as _model
    from hgi import roles

    out = []
    for role in roles.ROLES:
        runs = _model.model_id(role) if role != "pass" else model_id
        if not roles.is_priced_for(role, runs):
            out.append(warn("role-pricing", f"roles/{role}.md", f"priced for {roles.priced_for(role)!r}, the role runs {runs!r}"))
    return out


# --- oracle honesty -------------------------------------------------------------------

@check("oracle-honesty", "runtime", "a scorer measuring the wrong quantity")
def check_oracle_honesty(store: Store) -> list[Finding]:
    out = []
    for p in sorted(store.dir("session").glob("*.json")):
        raw = read_json(p)
        for series, fact in ((raw.get("evaluation") or {}).get("scores") or {}).items():
            if fact.get("value") in (0, 0.0) and fact.get("unevaluable"):
                out.append(fail("oracle-honesty", p.stem, f"{series}: a missing value written as zero"))
    return out


# --- genesis anchors ----------------------------------------------------------------

@check("genesis-anchor", "consolidation", "whether the anchor exemplifies the article")
def check_genesis(store: Store) -> list[Finding]:
    deadline = store.registry.bars.get("genesis_anchor_deadline_consolidations", 3)
    done = len(store.all("consolidation"))
    if done < deadline:
        return []
    return ([warn("genesis-anchor", a.id, f"genesis article past {deadline} consolidation passes with no anchor; evict or anchor")
             for a in store.articles() if a.warrant.evidence == "genesis" and not a.warrant.anchors]
            + [warn("genesis-anchor", l.id, f"genesis lens past {deadline} consolidation passes with no anchor: nothing it produced reached a consumer; retire or anchor")
               for l in store.registry.lenses() if l.warrant.evidence == "genesis" and not l.warrant.anchors])


# --- running ------------------------------------------------------------------------

def run(store: Store, seams: tuple[str, ...] | None = None, model_id: str | None = None) -> Report:
    report = Report()
    for c in CHECKS.values():
        if seams and c.seam not in seams:
            continue
        try:
            report.findings += c.fn(store, model_id) if c.name in ("model-pricing", "role-pricing") else c.fn(store)
        except (ValidationError, ValueError) as e:
            # the schema check has already named the refused record; a later check cannot read past it
            report.findings.append(warn(c.name, None, f"skipped: a record was refused at parse ({_first_line(e)})"))
    return report


def check_draft(store: Store, draft: Draft) -> list[Finding]:
    """The committer's floor over one draft: shape, complement law, ports for the status it will take."""
    findings = body_findings(draft.name, draft.body)
    declared = store.registry.ports.get("decision", {}).get("accepted", {})
    present = {l.type for l in draft.body.all_latches()}
    for latch_type, mark in declared.items():
        if mark == "required" and latch_type not in present:
            findings.append(fail("ports", draft.name, f"an accepted decision requires a {latch_type} latch"))
    return findings


def write_seam(store: Store) -> Report:
    return run(store, seams=("write",))
