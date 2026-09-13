"""The seed: the smallest configuration that runs one full cycle.

The loop's first organs cannot have been admitted by the loop and need not
be. Genesis writes the registry (Appendix C of the specification), the
constitution under its cap (Appendix A.1), the genesis work-shape terms
(A.2), the boot and close lens fans (A.3), and the id counters. Everything
else is minted by the loop from its own miss stream, through the ladder, at
the bars. Genesis articles and terms carry ``warrant.evidence: genesis`` and
earn an anchor by the third consolidation pass or are evicted.

``store/registry/*.json`` and ``store/constitution/*.json`` in the repository
are this module's output at genesis; afterwards they are registers the loop
corrects in place, and git carries the divergence.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from hgi import registry as _registry
from hgi.registry import write_json

GENESIS_DATE = "2026-09-12"


def _terms(*pairs: tuple[str, str]) -> dict[str, dict[str, str]]:
    return {term: {"means": means, "since": GENESIS_DATE} for term, means in pairs}


VOCABULARY: dict[str, dict] = {
    "work-shape": {
        "means": "the closed vocabulary of task presentations a consultation hook keys on; minted from the task suite's known presentations",
        "terms": _terms(
            ("tool-call-retry", "the task involves retrying a tool call that failed transiently"),
            ("http-tool", "the task calls the HTTP tool"),
            ("shell-tool", "the task calls the shell tool"),
            ("file-tool", "the task reads or writes through the file tool"),
            ("output-schema", "the task's output must conform to a declared schema"),
            ("test-failure-triage", "the task diagnoses a failing test"),
            ("tool-budget", "the task runs under a call budget"),
            ("error-wrapping", "the task wraps, rethrows or reports an error"),
            ("task-planning", "the task requires a plan before action"),
        ),
    },
    "latch-type": {"means": "the typed activation units of § 6.2", "terms": _terms(
        ("consultation", "keyed on work-shape; polled at boot; the working pass applies the payload"),
        ("revisit", "keyed on world-state; the oracle moving; the backward pass re-adjudicates the warrant"),
        ("wiring", "keyed on a neighbour record changing status; propagation re-derives or checks"),
        ("floor", "keyed on the diff or the proposal at commit; the committer's lint checks"),
        ("retirement", "keyed on competence signals at consolidation; the lifecycle review retires or demotes"),
    )},
    "key-space": {"means": "what a latch's guard is matched against", "terms": _terms(
        ("work-shape", "registered work-shape terms"), ("world-state", "a Weave evaluation, scorer and comparator"),
        ("neighbor", "record ids"), ("diff", "the proposal or diff under commit"), ("competence", "derived telemetry ratios"),
    )},
    "edge-kind": {"means": "how a latch becomes considered", "terms": _terms(
        ("level", "polled while the condition holds"), ("edge", "fires on a transition"), ("schedule", "fires at a scheduled point"),
    )},
    "act-class": {"means": "the closed set an owed act opens with", "terms": _terms(
        ("apply", "apply the payload to the work in hand"), ("re-adjudicate", "re-open the warrant for a verdict"),
        ("re-derive", "recompute a derived field"), ("check", "run a check"), ("retire", "retire or demote the record"),
    )},
    "owed-act-role": {"means": "whether a fire can settle the record", "terms": _terms(
        ("dispositive", "a disposed fire can settle the record"), ("corroborating", "a fire bears, never settles"),
    )},
    "latch-lifecycle": {"means": "the state of a latch", "terms": _terms(("live", ""), ("settled", ""), ("moot", ""))},
    "slot": {"means": "the five slots of the entry contract", "terms": _terms(
        ("activation", ""), ("payload", ""), ("warrant", ""), ("enforcement", ""), ("lifecycle", ""),
    )},
    "constitution-status": {"means": "", "terms": _terms(("live", "loaded every pass"), ("evicted", "displaced under the cap; superseded, never deleted"))},
    "decision-status": {"means": "", "terms": _terms(("proposed", ""), ("accepted", ""), ("superseded", ""), ("moot", ""))},
    "premise-status": {"means": "the one in-place flip a warrant takes; only a disposed fire may flip it", "terms": _terms(
        ("unevaluated", ""), ("supported", ""), ("disputed", ""), ("reversed", ""),
    )},
    "observation-state": {"means": "", "terms": _terms(("open", ""), ("promoted", "delete-with-pointer"), ("dismissed", ""), ("expired", ""))},
    "use-time-disposition": {"means": "the verdict a consulted record receives from the pass that consulted it", "terms": _terms(
        ("applied", "the payload bore on the work and was applied"),
        ("considered-not-applicable", "the hook fired on presentation alone; routing working as designed"),
        ("fired-off-map", "applied outside the declared hook, or the work matched no hook at all"),
        ("guard-failed", "considered but the guard did not pass"),
    )},
    "steer-source": {"means": "", "terms": _terms(("human", "a note on a call"), ("oracle", "an evaluation regression attributed by the adjudicator"))},
    "matrix-cell": {"means": "the detection matrix of § 10.1: did the store catch it, did the world or a human", "terms": _terms(
        ("system-catches/oracle-catches", "redundant catch; demotion-side evidence"),
        ("system-catches/human-catches", "redundant catch; demotion-side evidence"),
        ("system-catches/none-catches", "the amortization working"),
        ("system-misses/oracle-catches", "the steer: credit assignment plus a free miss report"),
        ("system-misses/human-catches", "the steer: credit assignment plus a free miss report"),
        ("system-misses/none-catches", "the true miss, repaired backwards from the manifested defect"),
    )},
    "species": {"means": "the kinds of hypothesis-ledger entry", "terms": _terms(
        ("attack", "the examiner's refute-phrased attack on a draft"), ("collision", "a derivation disagreeing with an implementation"),
        ("forecast", "a settled prediction"), ("reality", "a design premise contradicted by the world"),
        ("currency", "a premise re-checked for currency"), ("coding", "a blind second coding of observations"),
    )},
    "attack-verdict": {"means": "", "terms": _terms(("pending", ""), ("survived-with-attack-named", ""), ("attack-landed", ""), ("premise-killed", ""))},
    "collision-verdict": {"means": "", "terms": _terms(("pending", ""), ("derivation-wrong", ""), ("implementation-wrong", ""), ("contract-open", ""))},
    "forecast-verdict": {"means": "", "terms": _terms(("pending", ""), ("true", ""), ("false", ""), ("unevaluable", ""), ("void", ""))},
    "reality-verdict": {"means": "", "terms": _terms(("pending", ""), ("reducible", "a duty was missed; route it"), ("irreducible", "no authoring duty could have prevented it"))},
    "currency-verdict": {"means": "", "terms": _terms(("pending", ""), ("still-holds", ""), ("reversed", ""), ("moot", ""))},
    "coding-verdict": {"means": "", "terms": _terms(("pending", ""), ("agree", "ratifies the class"), ("disagree", "keeps the boundary open"))},
    "adjudicator-verdict": {"means": "the one token the adjudicator returns", "terms": _terms(
        ("admit", ""), ("admit-amended(<amendment>)", "amends only the slot the attack indicted"),
        ("decline(<why>)", "drops the draft"), ("defer(<until>)", "re-queues with the condition as a latch"),
        ("escalate(<why>)", "routes to the human queue"),
    )},
    "ladder-rung": {"means": "the cheapest sufficient home for a ratified recurrence, in order", "terms": _terms(
        ("counterfactual-edit", "1. an edit to an existing record's counterfactual or not_this"),
        ("adoption-row", "2. a row in an existing rule's adoption register"),
        ("rule-enrollment", "3. a new rule enrolled under an existing decision"),
        ("hook-edit", "4. a hook edit on an existing latch"),
        ("new-decision", "5. a new decision, only on a genuinely undecided fork"),
        ("floor", "6. a mechanical floor, only where the check is fully mechanical"),
        ("article", "7. a constitution article, only with a forced eviction"),
    )},
    "lens-purpose": {"means": "", "terms": _terms(("adjudicative", "terminates in an authority, never in the answerer"), ("generative", "touches the item; is never handed an answer"))},
    "lens-contact": {"means": "the strongest contact outside the answerer the lens forces", "terms": _terms(("record", ""), ("artifact", ""), ("oracle", ""), ("none", ""))},
    "lens-host": {"means": "the step that walks the lens", "terms": _terms(("boot", ""), ("close", ""), ("examiner", ""))},
    "role": {"means": "the four contexts of the separation of powers, plus the pass and the coder", "terms": _terms(
        ("pass", "the working pass — the agent under test and its boot and close steps"),
        ("consolidator", "nominates"), ("examiner", "contradicts"), ("adjudicator", "verdicts"),
        ("committer", "admits mechanically"), ("coder", "the blind second coder"), ("human", "the escalation queue"),
    )},
}

PORTS = {
    "decision": {
        "proposed": {"consultation": "required", "revisit": "optional", "wiring": "optional", "floor": "forbidden", "retirement": "forbidden"},
        "accepted": {"consultation": "required", "revisit": "optional", "wiring": "optional", "floor": "forbidden", "retirement": "required"},
        "superseded": {"consultation": "forbidden", "revisit": "forbidden", "wiring": "required", "floor": "forbidden", "retirement": "forbidden"},
        "moot": {"consultation": "forbidden", "revisit": "forbidden", "wiring": "optional", "floor": "forbidden", "retirement": "forbidden"},
    },
}

BARS = {
    "as_of": GENESIS_DATE,
    "observation": {"noticings": 1, "anchors": 1},
    "decision": {
        "independent_observations": 2,
        "or_steer_attributed_regressions": 1,
        "independence": "observations from distinct sessions",
    },
    "retirement": {"applied_over_considered_below": 0.1, "window_passes": 6},
    "vocabulary": {"independent_escapes": 2, "independence": "escapes from distinct sessions; two from one pass are one datum"},
    "consolidation_every_passes": 2,
    "genesis_anchor_deadline_consolidations": 3,
    "proposal_ttl_consolidations": 2,
}

CONSTITUTION_CAP = {"max_articles": 7, "max_bytes": 4096}

ARTICLES: list[tuple[str, str]] = [
    ("The pass proposes; the backward pass admits. No pass writes to an eternal store.",
     "The overshoot: a pass that files nothing because it cannot admit — proposals are the pass's product, not a courtesy."),
    ("Consultation is reported as a count with ids and dispositions; a bare assurance is a defect.",
     "The overshoot: opening every record to inflate the count — the count nominates precision review, never quality."),
    ("Every claim is a hypothesis with an anchor; suspected and verified never share a register.",
     "The overshoot: refusing to file a suspicion until it is verified — the observation ledger exists for the unverified."),
    ("The oracle grounds, the adjudicator decides, the committer writes; no context holds two roles.",
     "The overshoot: an adjudicator that defers every verdict to escalation — escalate is for ambiguity, not for reluctance."),
    ("Promotion raises abstraction; a copied instance is refused.",
     "The overshoot: an abstraction the anchors no longer instantiate — a floating entry."),
    ("Every floor discloses its residue; absent data reads unevaluable, never zero.",
     "The overshoot: a residue list so long the floor is not worth running — a floor with no bindable part is not a floor."),
    ("Every threshold has a retirement leg; nothing is deleted, everything is superseded.",
     "The overshoot: retiring the rarely-binding record for low salience — the killer-item is exempt regardless of count."),
]

LENSES = [
    {"id": "L-0001", "host": "boot", "purpose": "adjudicative",
     "angle": "Which consulted record's hook fired on presentation alone and does not bear on this task? Name it and dispose it considered-not-applicable.",
     "counterfactual": "The overshoot: disposing every record not-applicable to shorten the read — a record applied nowhere in the pass is a demotion datum, and the trace will show it.",
     "externality": {"contact": "record", "terminates_in": "the index and the consulted records, cited by id"},
     "product": "a list of {record, disposition, why}; empty is a legal answer", "consumer": "the working pass"},
    {"id": "L-0002", "host": "boot", "purpose": "generative",
     "angle": "The store holds a record this task needs and no hook reached it — which?",
     "counterfactual": "The overshoot: inventing a need to have a finding; an answer with no record id is not filed.",
     "externality": {"contact": "record", "terminates_in": "the decision store's summary lines"},
     "product": "a list of {record, why}; empty is a legal answer", "consumer": "the working pass; the structural-zero audit"},
    {"id": "L-0003", "host": "close", "purpose": "adjudicative",
     "angle": "What did this pass make false in the store — which premise, which hook?",
     "counterfactual": "The overshoot: manufacturing a falsification; empty is a legal answer.",
     "externality": {"contact": "record", "terminates_in": "the store's premises and hooks, cited by id"},
     "product": "a list of {record, slot, what-changed, anchor}; empty is a legal answer", "consumer": "the backward pass"},
    {"id": "L-0004", "host": "close", "purpose": "generative",
     "angle": "The first attempt in this pass was wrong somewhere — where, and which record should have fired?",
     "counterfactual": "The overshoot: grading the pass's own lesson as settled — the answer is an observation at the floor, never a rule.",
     "externality": {"contact": "artifact", "terminates_in": "the trace: a call URI per finding"},
     "product": "for the failed task in the subject, at most one {noticed, anchor, recheck_when}: `noticed` names the task, what its first attempt did, and what would have passed — the convention of this world it missed — in one or two sentences; `anchor` is {call: the row's call URI, path: null}; `recheck_when` says when to look for the same miss again; empty when the failure was not the pass's to avoid",
     "consumer": "the observation ledger; the backward pass"},
]


def seed(root: Path | str, model_id: str | None = None, now: datetime | None = None) -> _registry.Registry:
    """Write the seed into ``root`` and return the loaded registry. Idempotent over an empty store."""
    root = Path(root)
    now = now or datetime.now(timezone.utc)
    reg_dir = root / "registry"
    write_json(reg_dir / "vocabulary.json", VOCABULARY)
    write_json(reg_dir / "ports.json", PORTS)
    write_json(reg_dir / "bars.json", BARS)
    write_json(reg_dir / "constitution.json", CONSTITUTION_CAP)
    write_json(reg_dir / "lenses.json", [
        {**lens, "kind": "lens", "priced_for": {"model_id": model_id},
         "telemetry": {"answer_variance": "design-stage", "decoy_rejection": "design-stage", "miss_stream": "steers/ citing this lens"}}
        for lens in LENSES
    ])
    write_json(reg_dir / "ids.json", {"C": len(ARTICLES)})
    reg = _registry.load(root)

    from hgi.store import Store  # lazy: the store validates against this registry
    from hgi.types import ConstitutionArticle

    store = Store(root, registry=reg)
    for n, (article, counterfactual) in enumerate(ARTICLES, start=1):
        store.write(ConstitutionArticle(
            id=f"C-{n:04d}", status="live", created_at=now,
            admission={"proposed_by": "genesis", "verdict": "admit", "committed_at": now},
            article=article, counterfactual=counterfactual,
            warrant={"evidence": "genesis"}, priced_for={"model_id": model_id},
        ))
    for d in ("decisions", "observations", "ledger", "fires", "dispositions", "steers", "sessions",
              "proposals", "queue", "index", "consolidations"):
        (root / d).mkdir(parents=True, exist_ok=True)
    return reg
