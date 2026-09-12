"""Every record kind of the store, declared once.

JSON admission, the lint and the projections derive from these declarations;
there is no hand-maintained parallel field list. The models parse, they do
not validate after the fact: a malformed record is refused before the first
byte lands.

Closed-vocabulary fields are typed with :func:`Term`, which checks the value
against the registry in scope (``registry`` in the validation context, else
:func:`hgi.registry.current`). Every such field admits ``other(<what>)``.

Identity: ids are reserve-once, immutable, gap-tolerant, and encode no tier,
status or revisable slot. The prefix table is :data:`PREFIXES`.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    ValidationInfo,
    model_validator,
)

from hgi import registry as _registry

# --- vocabulary-typed strings --------------------------------------------------

def _registry_for(info: ValidationInfo) -> _registry.Registry:
    ctx = info.context or {}
    return ctx.get("registry") or _registry.current()


def Term(vocab: str):  # noqa: N802 — a type constructor
    """A string constrained to the closed vocabulary ``vocab`` or an ``other(<what>)`` escape."""

    def _check(value: str, info: ValidationInfo) -> str:
        return _registry_for(info).check(vocab, value)

    return Annotated[str, AfterValidator(_check)]


ID_PATTERN = re.compile(r"^([A-Z])-(\d{4,})$")
PREFIXES: dict[str, str] = {
    "constitution": "C",
    "decision": "D",
    "observation": "O",
    "lens": "L",
    "session": "S",
    "fire": "F",
    "hypothesis": "H",
    "steer": "T",
    "disposition": "U",
    "consolidation": "K",
}
"""Record kind → id prefix. ``O-`` is the observation's momentary *name*; its eternal identity is its ``uid``."""

ANCHOR_PATTERN = re.compile(r"(weave:///\S+|\b[A-Z]-\d{4,}\b|\bcommit:[0-9a-f]{7,}\b|\b[\w./-]+\.py:\d+\b)")
"""What counts as an anchor when cited inline in prose: a Weave URI, a record id, a commit, or a path:line."""


def anchors_in(text: str) -> list[str]:
    return ANCHOR_PATTERN.findall(text or "")


class Strict(BaseModel):
    """Every record model forbids unknown fields: a stray field is a parse failure, not a warning."""

    model_config = ConfigDict(extra="forbid")


# --- the envelope -------------------------------------------------------------

class Lineage(Strict):
    supersedes: list[str] = Field(default_factory=list)
    superseded_by: str | None = None
    split_from: str | None = None
    folded_from: list[str] = Field(default_factory=list)


class RoleCall(Strict):
    """A traced call by one of the four roles, joinable to the trace store."""

    role: Term("role")
    model_id: str | None = None
    call: str | None = None
    """The Weave call URI; ``None`` when the run was untraced."""


class Admission(Strict):
    """Stamped by the committer, never by the proposer.

    The admitting commit is not stored on the record because a commit cannot
    contain its own hash; it is derived from git history by ``hgi lineage``
    (the commit message names every id it admitted).
    """

    proposed_by: str
    """A session id, a consolidation id, or ``genesis``."""
    ledger_entry: str | None = None
    verdict: Term("adjudicator-verdict")
    adjudicator: RoleCall | None = None
    committed_at: datetime


class Envelope(Strict):
    id: str
    kind: str
    status: str
    created_at: datetime
    lineage: Lineage = Field(default_factory=Lineage)
    admission: Admission

    @model_validator(mode="after")
    def _id_matches_kind(self):
        m = ID_PATTERN.match(self.id)
        if not m or m.group(1) != PREFIXES.get(self.kind):
            raise ValueError(f"id {self.id!r} does not carry the prefix for kind {self.kind!r}")
        return self


# --- the latch ---------------------------------------------------------------

class WatchPredicate(Strict):
    """A world-state key: a Weave evaluation, a scorer, and a comparator over the last ``persistence`` runs."""

    evaluation: str
    scorer: str
    comparator: Literal["<", "<=", ">", ">=", "==", "!="]
    value: float
    persistence: int = 1


class Edge(Strict):
    kind: Term("edge-kind")
    at: str | None = None
    """For ``level`` and ``schedule`` edges: ``boot`` | ``consolidation`` | ``commit``."""
    predicate: WatchPredicate | None = None
    """For ``edge`` edges keyed on world-state."""


class Guard(Strict):
    terms: list[Term("work-shape")] = Field(default_factory=list)
    not_this: list[str] = Field(default_factory=list)
    applied_over_considered_below: float | None = None
    over_passes: int | None = None


class OwedAct(Strict):
    class_: Term("act-class") = Field(alias="class")
    role: Term("owed-act-role")

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class LatchLifecycle(Strict):
    status: Term("latch-lifecycle") = "live"
    settled_at: datetime | None = None
    settled_by: str | None = None


class Latch(Strict):
    """⟨key-space · edge · guard · consumer · owed act · lifecycle⟩ attached to one slot."""

    type: Term("latch-type")
    slot: Term("slot")
    key_space: Term("key-space")
    edge: Edge
    guard: Guard = Field(default_factory=Guard)
    consumer: str
    owed_act: OwedAct
    lifecycle: LatchLifecycle = Field(default_factory=LatchLifecycle)
    warrant: str | None = None
    """Required only for a latch off its port declaration."""

    @model_validator(mode="after")
    def _key_space_matches_edge(self):
        if self.key_space == "world-state" and self.edge.predicate is None:
            raise ValueError("a world-state latch names a watch predicate")
        if self.key_space == "work-shape" and not self.guard.terms:
            raise ValueError("a work-shape latch names at least one registered term")
        return self


# --- shared slots -------------------------------------------------------------

class Priced(Strict):
    model_id: str | None = None
    """The frozen model the conditioning text was authored against; ``None`` reads as unpriced."""


class Enforcement(Strict):
    floor: list[str] = Field(default_factory=list)
    """Lint checks by name, from :mod:`hgi.lint`'s check list."""
    residue: list[str] = Field(default_factory=list)


# --- constitution -------------------------------------------------------------

class GenesisWarrant(Strict):
    evidence: str
    """``genesis`` for a seed article; otherwise the anchors that earned it."""
    anchors: list[str] = Field(default_factory=list)


class ConstitutionArticle(Envelope):
    kind: Literal["constitution"] = "constitution"
    status: Term("constitution-status")
    article: str
    counterfactual: str
    warrant: GenesisWarrant
    priced_for: Priced = Field(default_factory=Priced)

    @property
    def size(self) -> int:
        return len(self.article.encode()) + len(self.counterfactual.encode())


# --- decision -----------------------------------------------------------------

class Summary(Strict):
    """The cheap cue: what the reader sees before opening the record. Passes the settlement test by construction."""

    latch: str
    not_this: list[str] = Field(default_factory=list)
    stakes: str


class Option(Strict):
    name: str
    judged: Literal["chosen", "rejected"]
    why: str


class Premise(Strict):
    id: str
    statement: str
    falsifier: str
    status: Term("premise-status") = "unevaluated"


class Adjudication(Strict):
    ledger_entry: str | None = None
    species: Term("species") = "attack"
    verdict: str = "pending"


class DecisionWarrant(Strict):
    anchors: list[str] = Field(default_factory=list)
    premises: list[Premise] = Field(default_factory=list)
    adjudication: Adjudication = Field(default_factory=Adjudication)


class DecisionLifecycle(Strict):
    consumer: str
    moot_when: str
    retirement: Latch


class DecisionBody(Strict):
    """The content of a decision — everything but the envelope. A draft carries a body; an admitted decision carries a body inside an envelope."""

    scopes: list[str] = Field(default_factory=list)
    summary: Summary
    context: str
    options: list[Option]
    decision: str
    counterfactual: str
    warrant: DecisionWarrant
    latches: list[Latch]
    enforcement: Enforcement
    lifecycle: DecisionLifecycle
    priced_for: Priced = Field(default_factory=Priced)

    def all_latches(self) -> list[Latch]:
        return [*self.latches, self.lifecycle.retirement]

    @property
    def consultation_terms(self) -> list[str]:
        return [t for l in self.latches if l.type == "consultation" for t in l.guard.terms]

    @property
    def consultation_not_this(self) -> list[str]:
        return [n for l in self.latches if l.type == "consultation" for n in l.guard.not_this]


class Decision(Envelope, DecisionBody):
    kind: Literal["decision"] = "decision"
    status: Term("decision-status")


# --- observation (pre-admission stratum) -------------------------------------

class Anchor(Strict):
    call: str | None = None
    path: str | None = None
    record: str | None = None
    commit: str | None = None

    @model_validator(mode="after")
    def _non_empty(self):
        if not any([self.call, self.path, self.record, self.commit]):
            raise ValueError("an anchor names at least one of call, path, record, commit")
        return self


class ObservationDisposition(Strict):
    state: Term("observation-state") = "open"
    pointer: str | None = None
    at: datetime | None = None


class Observation(Strict):
    uid: str
    name: str
    kind: Literal["observation"] = "observation"
    noticed_at: datetime
    session: str
    noticed: str
    anchor: Anchor
    recheck_when: str | None = None
    shape: list[str] = Field(default_factory=list)
    """Empty at intake; filled by the consolidation pass's grouping, never by the noticing session."""
    disposition: ObservationDisposition = Field(default_factory=ObservationDisposition)


# --- fire ---------------------------------------------------------------------

class LatchRef(Strict):
    record: str
    index: int
    """Index into the record's ``all_latches()``."""


class EdgeEvent(Strict):
    evaluation: str
    pass_: int = Field(alias="pass")
    scorer: str
    observed: float | str
    source: str | None = None

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class FireDisposition(Strict):
    act: Term("act-class")
    outcome: str | None = None
    at: datetime | None = None
    by: str | None = None

    @property
    def discharged(self) -> bool:
        return self.outcome is not None


class Fire(Strict):
    id: str
    kind: Literal["fire"] = "fire"
    fired_at: datetime
    latch: LatchRef
    edge_event: EdgeEvent
    guard_result: bool
    disposer: str = Field(min_length=1)
    """A fire that cannot name its disposer is a standing false alarm by construction."""
    disposition: FireDisposition


# --- use-time disposition -----------------------------------------------------

class Disposition(Strict):
    id: str
    kind: Literal["disposition"] = "disposition"
    session: str
    record: str
    considered: bool
    guard_passed: bool
    disposition: Term("use-time-disposition")
    note: str | None = None


# --- steer --------------------------------------------------------------------

class SteerSource(Strict):
    kind: Term("steer-source")
    anchor: str | None = None


class Indictment(Strict):
    record: str
    slot: Term("slot")
    signature: str


class Steer(Strict):
    id: str
    kind: Literal["steer"] = "steer"
    at: datetime
    source: SteerSource
    correction: str
    indicts: Indictment | None = None
    why_not_caught: str | None = None
    matrix_cell: Term("matrix-cell")


# --- facts (the oracle's floor, mirrored on the session) ----------------------

class Fact(Strict):
    """A settled, as-of-stamped measurement. Absent data reads ``unevaluable``, never zero."""

    series: str
    """``<evaluation>/<scorer>``."""
    value: float | None = None
    unevaluable: str | None = None
    """The reason the scorer could not run; present exactly when ``value`` is absent."""
    as_of: datetime
    source: str | None = None

    @model_validator(mode="after")
    def _oracle_honesty(self):
        if (self.value is None) == (self.unevaluable is None):
            raise ValueError("a fact carries exactly one of value and unevaluable")
        return self


class EvaluationResult(Strict):
    evaluation: str
    run: str | None = None
    suite_hash: str | None = None
    scores: dict[str, Fact] = Field(default_factory=dict)


# --- session ------------------------------------------------------------------

class WorkShape(Strict):
    terms: list[Term("work-shape")] = Field(default_factory=list)
    escapes: list[str] = Field(default_factory=list)


class Consulted(Strict):
    record: str
    disposition: str | None = None
    """The ``U-`` id; ``None`` until close."""


class Considered(Strict):
    """One stage-one selection event: the routing verdict before the pass disposes it."""

    record: str
    terms_matched: list[str] = Field(default_factory=list)
    via: Literal["index", "lexical", "constitution"]
    guard_passed: bool
    owed_act: str


class LensAnswer(Strict):
    lens: str
    answer: str
    findings: list[dict[str, Any]] = Field(default_factory=list)
    call: str | None = None


class Session(Strict):
    id: str
    kind: Literal["session"] = "session"
    pass_: int = Field(alias="pass")
    started_at: datetime
    closed_at: datetime | None = None
    model_id: str | None = None
    trace_root: str | None = None
    work_shape: WorkShape = Field(default_factory=WorkShape)
    considered: list[Considered] = Field(default_factory=list)
    consulted: list[Consulted] = Field(default_factory=list)
    lens_answers: list[LensAnswer] = Field(default_factory=list)
    fires_seen: list[str] = Field(default_factory=list)
    observations_filed: list[str] = Field(default_factory=list)
    steers_filed: list[str] = Field(default_factory=list)
    ledger_entries: list[str] = Field(default_factory=list)
    proposals: list[str] = Field(default_factory=list)
    evaluation: EvaluationResult | None = None
    carry_forward: str = ""
    attached: bool = True
    """``False`` for an ablation pass: same agent, same suite, no boot or close."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


# --- hypothesis ledger --------------------------------------------------------

class AttackClaim(Strict):
    target: str
    """What is attacked: ``premise:p2``, ``payload``, ``activation``, ``warrant`` …"""
    refutation: str
    """Refute-phrased: what reading of the evidence would show the claim false."""
    reading_taken: bool
    landed: bool
    evidence: list[str] = Field(default_factory=list)


class Attack(Strict):
    """The examiner's payload. It carries no verdict; ``pending`` is the only value the schema admits here."""

    claims: list[AttackClaim]
    verdict: Literal["pending"] = "pending"


class Contradiction(Strict):
    source: RoleCall
    attack: Attack | None = None
    coding: dict[str, Any] | None = None


class LedgerEntry(Strict):
    id: str
    kind: Literal["hypothesis"] = "hypothesis"
    at: datetime
    species: Term("species")
    subject: str
    """The draft uid or the record id the entry is about."""
    claim: str
    proposer: RoleCall
    contradiction: Contradiction
    verdict: str = "pending"
    adjudicator: RoleCall | None = None
    amendment: str | None = None
    rung: Term("ladder-rung") | None = None
    outcome: str | None = None
    """What the committer did: ``admitted D-0007`` | ``declined`` | ``escalated`` | ``deferred``."""

    @model_validator(mode="after")
    def _verdict_in_species_vocabulary(self, info: ValidationInfo):
        if self.verdict == "pending":
            return self
        reg = _registry_for(info)
        vocab = f"{self.species}-verdict"
        if vocab in reg.vocabularies:
            reg.check(vocab, self.verdict)
        return self


# --- proposals (the pre-admission tier) --------------------------------------

class Draft(Strict):
    """A candidate record. Eternal identity attaches at admission; a draft carries a non-recycled ``uid`` and a recyclable ``name``."""

    uid: str
    name: str
    kind: Literal["decision"] = "decision"
    drafted_at: datetime
    proposed_by: str
    rung: Term("ladder-rung")
    rung_why: str
    """Why the cheaper rungs do not suffice."""
    body: DecisionBody
    evidence: list[str] = Field(default_factory=list)
    """The observation uids, steer ids and Weave URIs the draft rests on."""


class QueueEntry(Strict):
    """An escalated proposal awaiting a human verdict from the same closed vocabulary."""

    draft: Draft
    ledger_entry: str
    why: str
    queued_at: datetime
    oracle_evidence: dict[str, Any] = Field(default_factory=dict)


# --- lens ---------------------------------------------------------------------

class Externality(Strict):
    contact: Term("lens-contact")
    terminates_in: str


class LensTelemetry(Strict):
    answer_variance: str = "design-stage"
    decoy_rejection: str = "design-stage"
    miss_stream: str = "steers/ citing this lens"


class Lens(Strict):
    id: str
    kind: Literal["lens"] = "lens"
    angle: str
    counterfactual: str
    purpose: Term("lens-purpose")
    externality: Externality
    product: str
    consumer: str
    host: Term("lens-host")
    priced_for: Priced = Field(default_factory=Priced)
    telemetry: LensTelemetry = Field(default_factory=LensTelemetry)


# --- consolidation record -----------------------------------------------------

class Nomination(Strict):
    rung: Term("ladder-rung")
    rung_why: str
    subject: str
    evidence: list[str]
    draft: str | None = None
    """The draft uid, when the nomination produced one."""
    ledger_entry: str | None = None
    outcome: str | None = None


class Consolidation(Strict):
    id: str
    kind: Literal["consolidation"] = "consolidation"
    started_at: datetime
    closed_at: datetime | None = None
    after_pass: int
    sessions_read: list[str]
    brief: dict[str, Any] = Field(default_factory=dict)
    """The consolidation brief: applied ÷ considered per record, groups by shape, escape clusters."""
    analyst_report: str | None = None
    """The ARIA report URI, when the brief was drafted by the analyst."""
    nominations: list[Nomination] = Field(default_factory=list)
    fires_discharged: list[str] = Field(default_factory=list)
    admitted: list[str] = Field(default_factory=list)
    flipped: list[str] = Field(default_factory=list)


# --- kind table ---------------------------------------------------------------

RECORD_MODELS: dict[str, type[BaseModel]] = {
    "constitution": ConstitutionArticle,
    "decision": Decision,
    "observation": Observation,
    "fire": Fire,
    "disposition": Disposition,
    "steer": Steer,
    "session": Session,
    "hypothesis": LedgerEntry,
    "consolidation": Consolidation,
    "lens": Lens,
}
