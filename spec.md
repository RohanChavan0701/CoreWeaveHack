
---
title: HGI — an attached associative memory for agent loops
class: specification
status: draft for implementation
as_of: 2026-09-12
target: CoreWeave Hacks — Agent Loops Hackathon, San Francisco, 2026-09-12 to 2026-09-13
---

# HGI — an attached associative memory for agent loops

## 0. Status and reading guide

This document specifies **HGI**: a store that attaches to an agent loop and
gives a frozen model a memory that learns between passes. It states the
principles, the record shapes, the read path (the forward pass), the write
path (the backward pass), the oracle that settles what is true, and the
slices and milestones that reach a demonstrable deliverable by the
submission deadline on 2026-09-13 at 13:00.

Read §§ 1–5 for the principles and the entry contract, § 6 for every record
schema, §§ 7–10 for the two passes and the oracle, §§ 11–12 for enforcement
and telemetry, § 13 for the build plan, § 14 for the demo and its acceptance
bar. Appendices carry worked records, the repository layout, and the closed
vocabularies.

Conventions. Directives are written as **Do / Don't** pairs: the Do names
the obligation; the Don't names the specific overshoot a builder lands in
when steering away from the original failure. A bare directive with no pair
is a defect in this document. Dates are absolute. Every closed vocabulary
ships an escape (`other(<what>)`); a forced pick is a defect. Store names,
record kinds and field names are `code`; the lexicon in § 2 is binding.

## 1. Purpose

### 1.1 The constraint and the thesis

The most capable component of an agent loop — the model — is frozen and
rented. It learns nothing between passes and holds no memory of the task,
the project, or its own prior mistakes. Everything the loop *knows* must
therefore live in text the loop owns: what enters context, what leaves as
action, what gets written down.

HGI treats that as a design constraint with an architectural answer rather
than a deficiency to patch with a memory feature. The loop's typed record
corpus **is** its learning system, and it is run as one:

- **T1 — Unbundling.** The three functions weight training bundles —
  storage, generalization, behavior binding — are separated and reassigned.
  Storage goes to a typed corpus. Generalization splits: the frozen model
  generalizes in-context at read time; the backward pass generalizes at
  write time by restating an instance at transferable altitude before it
  moves up a tier. Behavior binding goes to mechanical floors plus disclosed
  residue.
- **T2 — The store space.** Two axes partition the stores: decay profile,
  and the truth-maker — the live question whose answer would falsify a
  record. The truth-maker cuts the live stores into a **belief** store
  ("is this still true of the world?"), a **case** store ("is this still
  correct?"), and a **duty** store ("did you actually do it, at every
  site?"), above a settled fact-and-trace floor.
- **T3 — The entry contract.** Nothing global carries the learning loop
  for a frozen model, so every persistent record carries it locally in five
  slots: activation, payload, warrant, enforcement split, lifecycle.
- **T4 — A governed write path.** Beliefs are ledgered hypotheses exposed
  to structurally independent contradiction; the adjudicator is distinct
  from proposer and contradictor; refinement is damped by recurrence
  evidence graded by blast radius; and every permanent write passes a
  gate. In HGI that gate is the **oracle gate** (§ 9): the sponsor
  evaluation stack settles what the world says, an unstaked adjudicator
  context renders the verdict, and a human is an optional escalation
  rather than a required step.

In borrowed training vocabulary — words, never mechanism — each pass of the
loop is the **forward pass**, the oracle's scores are the **loss signal**,
the loop's agents compute **proposed updates** with evidence attached, and
the consolidation pass is the **backward pass**: one deliberate,
low-frequency step that alone applies updates.

### 1.2 The deliverable

An attached associative memory: a Python package and CLI that

1. **stores** typed records in legible text under an event-sourced write
   law (§ 7);
2. **assembles context** for each pass through two-stage attention —
   legible symbolic keys select records, authored lenses condition the
   read (§ 8);
3. **settles** predictions and contradictions against an oracle built
   from the sponsor stack — W&B Weave traces, evaluations and feedback
   as the world channel; ARIA as the consolidation analyst; marimo as the
   projection and escalation surface; the CoreWeave inference endpoint as
   the frozen model (§ 9);
4. **consolidates** signal into refined records through a slot-factored
   backward pass under separation of powers (§ 10);
5. **discloses** what its floors check and what they do not (§ 11), and
   instruments itself on behavior only (§ 12).

The demonstration (§ 14) runs one agent loop over a fixed task suite for
several passes with HGI attached and, as the ablation, detached, and shows
the oracle's score curve, the records the loop minted, retired and applied,
and the calibration of the loop's own predictions.

### 1.3 Non-goals

- Not a fine-tuning substitute: no weights change; the store is
  context-resident by design.
- Not retrieval-augmented generation: the read path is retrieval-shaped, but
  the write-side lifecycle — promotion, abstraction, retirement, credit
  assignment — is the product.
- Not an embedding index: stage-one keys are symbolic and legible; no
  learned router or tuned embedder sits in the retrieval path. A lexical
  matcher over governed vocabulary is legal; a latent one is not.
- Not a simulator or a probabilistic database: the belief store holds
  falsifiable text commitments settled by the oracle, never rollouts.
- Not a safety system. The human gate of the parent doctrine is relaxed to
  an oracle gate with human escalation; §§ 9–10 state the structural
  substitutes that keep the write path from collapsing into a self-grading
  loop.

## 2. Vocabulary

A closed lexicon. Use these words for these concepts, no synonyms, and none
of them for anything else. A concept fitting no term enters as
`other(<what>)` with a definition, never as a private synonym.

| Term | Means | Not to be called |
|---|---|---|
| store | one directory holding one kind of record under one lifecycle | database, pile, collection |
| record / entry | one item in a store, carrying the five-slot contract | doc, note, item |
| register | a current-state surface, corrected in place | log, history |
| ledger | an append-only history; entries frozen at admission | list, archive |
| admission | the act that turns a draft into a record — the committer's write after the adjudicator's verdict | creation, saving |
| supersede | retire a record by pointing to its successor | edit, update |
| status flip | the only in-place change a frozen record receives | amendment |
| payload | the cached judgment a record exists to deliver | summary, description |
| warrant | what grounds a payload, causally independent of it | context, rationale |
| anchor | a reference tying a claim to evidence — a trace call id, a commit, a path, a record id | link, example |
| falsifier | the nameable event or predicate that would kill a claim | risk, caveat |
| latch | a typed activation unit attached to a record slot: ⟨key-space · edge · guard · consumer · owed act · lifecycle⟩ | trigger |
| hook | a latch's recognition condition — its edge plus guard — matched against the work in hand | trigger |
| not-this | a hook's declared exclusions — shapes it matches but must not bind | exception |
| revisit trigger | a latch keyed on the world: `{when, then, settled}` | a hook |
| fire | a reified event: a latch whose guard passed, recorded in the fire ledger and owed a disposition | a status change |
| disposition | the terminal act on something pending: a consulted record's use-time verdict, a fire's discharge, a candidate's admission or decline | outcome |
| disposer | the party a fire names as owing its act | owner |
| act class | the closed set a `then` opens with — `apply`, `re-adjudicate`, `re-derive`, `check`, `retire`, `other(<what>)` | instruction |
| oracle | the world channel: the evaluation stack that scores behavior and settles predictions; it contradicts and grounds, it never authors | judge, reward model |
| adjudicator | the unstaked context that renders a verdict on a proposal given the oracle's evidence and the contradictor's attack | reviewer |
| committer | the mechanical write gate that admits an adjudicated proposal after the floor passes | saver |
| steer | a correction — human, or oracle-attributed — that performs credit assignment: which record, which slot | feedback |
| residue | what a record's enforcement does not check, stated on the record | limitation |
| duty | the obligation a rule's payload carries, as narrow as is true | guideline |
| site | a distinct surface a duty can bind at — a tool, a prompt, a task family, a store | place |
| floor | what mechanically checks part of a record, by name, or `none` | the whole check |
| lens | a typed question walked against an item, paired with its counterfactual | checklist item |
| observation | a noticing below every store's admission bar — one anchored instance in the observation ledger | a decision or rule |
| prediction | a belief record: a claim frozen with a reference at entry, kill criteria and a deadline, settled by the oracle | forecast, guess |
| promotion | tier movement that raises abstraction — observation → decision → rule → floor | copy, upgrade |
| pass / session | one iteration of the loop: boot, act, evaluate, reflect, propose, close | run |
| consolidation | the scheduled backward pass that moves knowledge between tiers | cleanup |
| work-shape | the closed vocabulary of task presentations a hook keys on | tag |

## 3. Architecture

### 3.1 Components

```
                 ┌───────────────────────────────────────────────┐
                 │                  HGI store                     │
                 │  constitution/  decisions/  rules/  beliefs/   │
                 │  observations/  fires/  dispositions/ steers/  │
                 │  ledger/ (hypotheses)   registry/ (vocab,ports)│
                 │  sessions/              index/ (projections)   │
                 └────────▲──────────────────────────┬───────────┘
        proposals (draft) │                          │ stage-one selection
        dispositions      │                          │ + lenses (composition)
        observations      │                          ▼
   ┌──────────────────────┴─────────┐     ┌──────────────────────────┐
   │      BACKWARD PASS             │     │      FORWARD PASS         │
   │  consolidator (nominates)      │     │  boot → act → evaluate    │
   │  examiner  (contradicts)       │     │  → reflect → propose      │
   │  adjudicator (verdicts)        │     │  → close                  │
   │  committer (admits)            │     │  the agent under test     │
   └──────────────▲─────────────────┘     └────────────┬─────────────┘
                  │ verdict evidence                    │ traces, scores
                  │                                     ▼
              ┌───┴─────────────────────────────────────────────┐
              │                    ORACLE                        │
              │  Weave: traces (trace store), evaluations (world),│
              │  feedback (steer channel)                        │
              │  ARIA: analysis over runs → nominations          │
              │  marimo: projections, escalation surface         │
              │  Inference endpoint: the frozen model (priced)   │
              └──────────────────────────────────────────────────┘
```

### 3.2 The loop

**Forward pass** (§ 8). A pass opens by assembling its context from the
store: the constitution loads unconditionally; the previous session's
carry-forward header restores continuity; the pass classifies its
work-shape; stage one selects the records whose hooks match; lenses
condition the read. The agent acts, every call traced. The oracle evaluates
the pass's outputs. The pass reflects: every consulted record receives a
use-time disposition, noticings land as observations, the pass's frozen
prediction is scored, contradictions file to the hypothesis ledger. The
pass proposes candidate records and closes with a session record.

**Backward pass** (§ 10). At scheduled points — every *k* passes, or on a
fired trigger — the consolidator reads the accumulated ledgers and the
oracle's telemetry, groups them by shape, and nominates: promotions,
slot-local refinements, splits, folds, retirements. The examiner attacks
each nomination. The adjudicator renders a verdict from the closed
vocabulary. The committer admits what the verdict allows and the floor
passes. Nothing structural updates on one instance.

**Oracle** (§ 9). Traces are the trace store. Evaluation results are the
fact floor — settled, as-of-stamped measurements. Feedback attached to
calls is the steer channel. The analysis agent is a nominator over runs,
never a verdict. Absent data reads `unevaluable`, never zero.

### 3.3 Separation of powers

Four roles, four contexts. Each collapse of two roles is a named failure:

| Collapse | Failure |
|---|---|
| proposer = contradictor | no contradiction is ever generated; hypotheses survive their author's scrutiny by default |
| contradictor = adjudicator | the attacker grades its own attack; every contradiction is "confirmed" |
| proposer = adjudicator | the self-warranting verifier — the disagreeing party decides the disagreement |
| adjudicator = committer, unattended | the ungoverned auto-write loop, with its measured collapse and self-bias |

**Do:** run each role in its own model context with no authoring stake in
the artifact it judges; feed the adjudicator the oracle's evidence and the
examiner's attack, never the proposer's narrative. **Don't:** don't simulate
independence inside one context by instruction ("now be skeptical") — a
single context cannot be instructed into genuine self-skepticism;
independence is structural or it is absent.

The human gate is relaxed, not removed: a verdict of `escalate(<why>)`
routes a proposal to the human queue on the marimo surface; every other
verdict commits mechanically. The escalation vocabulary is closed (§ 10.9).

## 4. The store space

### 4.1 Two axes

**Decay profile.** Different knowledge rots at different rates, is recalled
at different moments, and fails differently. One store per decay profile;
never one governance. Heterogeneous records sharing one retrieval space
contaminate each other.

**Truth-maker.** The live question whose answer would falsify a record:

| Leg | Live question | Contradicted by | Dominant machinery |
|---|---|---|---|
| belief | is this still true of the world? | the oracle: scores, settled outcomes | frozen claims, watches, evidence state, skill scoring |
| case | is this still correct? | currency: a premise reversing, a constraint dissolving | the falsification-list warrant, revisit triggers, supersedure |
| duty | did you actually do it, at every site? | the estate: the loop observing its own uptake | the adoption register: per-site triage, carry reasons, gap cells |

The trichotomy is a nested dichotomy: first cut, world-facing versus
internal; second cut, within internal, correctness versus propagation.
Membership test: **a record belongs to the belief store iff its entry-price
slot is fillable** — iff its truth-maker admits an independent reference
that can be frozen at entry. Everything internal has bars and caps, not
references.

Beneath the legs sit two organs with no live question: the **fact layer**
(settled measurements, as-of-stamped — a belief whose price is identically
zero) and the **trace** (the event record). In HGI both are hosted by the
oracle: evaluation results are facts; traces are the trace store.

### 4.2 The store roster

A roster is an output of the loop, not an input; this one is the minimum
that runs one full cycle, and growth happens through the ladder in § 10.3.

| Store | Leg | Holds | Recall mode | Forgetting | Directory |
|---|---|---|---|---|---|
| constitution | duty apex | the always-loaded articles | every pass, unconditionally | **hard cap with forced eviction** — the only fixed-width layer | `constitution/` |
| rules | duty | recurring conditional duties: hook → duty, with a floor and residue | routed by declared work-shape at boot | demotion review on applied ÷ considered; probation; tombstones | `rules/` |
| decisions | case | settled point decisions constraining future forks | full scan of one-line summaries + hook match | status flip (superseded / moot); never deleted | `decisions/` |
| beliefs | belief | predictions: priced claims with watches and deadlines | trigger-fired + a status projection | settlement retires them to the fact floor | `beliefs/` |
| observations | pre-admission stratum | noticings with anchors; latch-stripped advisories | the consolidation pass | delete-with-pointer on promotion; expiry | `observations/` |
| ledger | contradiction | hypothesis-ledger entries by species | the consolidation pass, wholesale | classification pass; never edited | `ledger/` |
| fires | activation events | fire records owed a disposition | the disposer at the next boot; the consolidation pass | discharged fires leave the live projection by mootness | `fires/` |
| dispositions | telemetry | use-time dispositions per consulted record per pass | the demotion review | none — a ledger | `dispositions/` |
| steers | reward | corrections with credit assignment | the consolidation pass | none — a ledger | `steers/` |
| sessions | trace header | one record per pass: what was consulted, predicted, filed | the next boot's carry-forward; projections | none | `sessions/` |
| registry | schema surface | the closed vocabularies and port declarations | every read that validates | route-before-mint; escape recurrence nominates growth | `registry/` |
| index | projection | regenerated read models: hook-major index, live triggers, evidence states | stage one of every pass | regenerated; never hand-edited | `index/` |

Traces and facts are not directories: they live in the oracle and are
referenced by anchor (§ 9.2).

### 4.3 The constitution cap

The always-loaded tier is hard-capped on article count and total bytes.
Adding an article means evicting one. The cap forces the ranking
conversation a growing pile silently avoids.

**Do:** pin the cap in `registry/constitution.json` (`max_articles`,
`max_bytes`) and let the lint refuse a commit that exceeds it. **Don't:**
don't soft-budget the tier ("keep it small") — soft budgets fail, and the
context-rot literature is unambiguous that an always-loaded surface that
grows unbounded degrades every pass.

Pinned values for the hackathon build, dated 2026-09-12: seven articles,
four kilobytes.

## 5. The entry contract

Every persistent record carries the whole learning loop locally, in legible
text — five slots, one contract:

1. **Activation** — when does this enter context, or fire? A fan of typed
   latches (§ 6.2), each attached to a specific slot.
2. **Payload** — the cached judgment, at transferable altitude.
3. **Warrant** — what grounds it: anchors, truth-maker, adjudication —
   causally independent of the record itself.
4. **Enforcement split** — the mechanical floor, by name, plus the
   disclosed residue.
5. **Lifecycle** — the named consumer plus the retirement leg.

Each missing slot names a failure mode:

| Missing | Failure |
|---|---|
| activation | the **structural zero** — stored, unreachable, never recalled |
| independent warrant | the **floating entry** — reads as whatever the surrounding context suggests; worst case, the self-warranting verifier |
| floor disclosure | complacency about what enforcement does not check |
| lifecycle consumer | the graveyard — entry without retirement |
| abstracted payload | the recall cache — a stored instance that transfers negatively |

**The complement law.** Every declared positive carries its declared
negative, because a frozen generalizer interpolates beyond any unbounded
pointer:

| Slot | Complement member |
|---|---|
| activation | the not-this clause — the router's declared exclusions |
| payload | the **counterfactual** — the directive's named overshoot, stated as a concrete, plausible alternative failure, never bare negation |
| warrant | the falsification list — constraining facts written as what would refute them |
| enforcement | the disclosed residue |
| lifecycle | the retirement leg |
| every closed vocabulary | the escape `other(<what>)` |

**Do:** author every counterfactual from an observed instance — a ledgered
defect, a caught over-claim, a steer — and cite it. **Don't:** don't
author a counterfactual from imagination ("don't overdo it" bounds
nothing); a pair with no anchored instance is priming, and the lint
(§ 11) warns on a counterfactual with no anchor.

**Slot fillings are coordinates, not choices.** Record kinds differ because
each evaluates the contract at its own position: recall economics,
truth-maker, bindability, decay profile, moment in the loop. § 6 states
each kind's coordinates before its fields.

## 6. Record schemas

### 6.0 Conventions

- **Format.** One JSON file per record in its store directory, named by id
  (`decisions/D-0007.json`). Ledgers are JSON Lines, one entry per line,
  append-only. The registry is JSON. Projections under `index/` are
  regenerated by `hgi index` and never edited by hand.
- **Typing.** Records are declared once as typed models (pydantic v2) in
  `hgi/types.py`; JSON admission, the lint, and the generated reference
  derive from the declarations. No hand-maintained parallel field list.
  Parse, don't validate: a malformed record is refused before the first
  byte lands.
- **Identity.** Ids are reserve-once, immutable, gap-tolerant, and encode
  no tier, status or revisable slot. Prefixes: `C-` constitution article,
  `D-` decision, `R-` rule, `B-` belief, `O-` observation (name; see the
  pre-admission tier, § 7), `L-` lens, `S-` session, `F-` fire, `H-`
  hypothesis-ledger entry, `T-` steer, `U-` use-time disposition.
- **Dates** are ISO-8601 with timezone. `as_of` marks a frozen measurement;
  `settled_at` marks an adjudication event. An undated sentence asserts an
  until-falsified truth.
- **Closed vocabularies** live in `registry/vocabulary.json` and every
  enumerated field admits `other(<what>)`. Nothing else in a record is
  free-form enum.
- **Model pricing.** Every record that carries authored conditioning text
  (a lens, a rule's duty sentence, a checkpoint's procedure) records
  `priced_for.model_id`: the frozen model it was authored against. A model
  swap re-prices every such record in both directions.

### 6.1 The envelope

Every record carries:

```json
{
  "id": "D-0007",
  "kind": "decision",
  "status": "accepted",
  "created_at": "2026-09-12T18:40:00-07:00",
  "lineage": {
    "supersedes": ["D-0003"],
    "superseded_by": null,
    "split_from": null,
    "folded_from": []
  },
  "admission": {
    "proposed_by": "S-0014",
    "ledger_entry": "H-0021",
    "verdict": "admit",
    "adjudicator": {"role": "adjudicator", "model_id": "…", "call": "weave:///…"},
    "committed_at": "2026-09-12T19:02:11-07:00",
    "commit": "a1b2c3d"
  }
}
```

`status` vocabulary per kind is stated with the kind. `lineage` edges are
the corpus graph: successor edges compose into the lineage DAG; `split_from`
and `folded_from` are the vertex-split and edge-contraction operators of
§ 10.6. `admission` is stamped by the committer, never by the proposer.

### 6.2 The latch

The activation slot is a fan of typed latches. Each latch is a tuple
attached to a specific pentad slot:

```json
{
  "type": "consultation",
  "slot": "payload",
  "key_space": "work-shape",
  "edge": {"kind": "level", "at": "boot"},
  "guard": {"terms": ["tool-call-retry", "json-output"], "not_this": ["schema-migration"]},
  "consumer": "the working pass",
  "owed_act": {"class": "apply", "role": "dispositive"},
  "lifecycle": {"status": "live", "settled_at": null, "settled_by": null}
}
```

| Latch type | Key-space | Edge | Consumer | Owed act |
|---|---|---|---|---|
| `consultation` | work-shape | boot (level-sensitive: polled at plan assembly) | the working pass | `apply` the payload |
| `revisit` | world-state | the oracle moving (edge-triggered) | the backward pass | `re-adjudicate` the warrant |
| `wiring` | neighbor identity | a referenced record changing status | propagation | `re-derive` / `check` |
| `floor` | the diff / the proposal | commit | the committer's lint | `check` the floor |
| `retirement` | competence signals | the consolidation pass | the lifecycle review | `retire` / demote |

Rules that hold across the fan:

- The **edge** makes a latch *considered*; the **guard** makes a considered
  latch *fire*. Together they are the hook. Three telemetry verdicts follow:
  considered-but-guard-failed (routing working as designed),
  fired-but-not-applicable (indicts the guard), fired-off-map (indicts the
  declared domain).
- Hooks may overlap freely across the fan; **each owed act has exactly one
  owning latch**.
- The owed act's `class` is a typed reference into the act-class
  vocabulary — never an arbitrary instruction. A latch whose `then` is prose
  is refused by the lint.
- The owed act's `role` is `dispositive` (a fire can settle the record once
  disposed) or `corroborating` (a fire bears, never settles).
- A latch is a **non-unique secondary index, never the primary key**; ids
  never derive from hooks.
- **Key-space governance.** `work-shape` terms come only from
  `registry/vocabulary.json`; a hook naming an unregistered term is refused.
  `world-state` predicates name a Weave evaluation, scorer and comparator
  (§ 9.2). `neighbor` keys are record ids. A latch is worth exactly as much
  as the governance of its key-space.
- **The reified fire.** A latch whose guard passes emits a fire record
  (§ 6.8); the fire is an event in a ledger, not a state change in the
  record. Fired and discharged are distinct states.

**Port declarations.** `registry/ports.json` declares, per record kind and
per lifecycle status, which latch types are admissible with an obligation
mark (`required` | `optional` | `forbidden`). A latch off-declaration is
admitted only with an explicit `warrant` field on the latch; a recurring
off-declaration channel nominates widening the declaration.

```json
{
  "decision": {
    "proposed": {"consultation": "required", "revisit": "optional", "wiring": "optional", "floor": "forbidden", "retirement": "forbidden"},
    "accepted": {"consultation": "required", "revisit": "optional", "wiring": "optional", "floor": "forbidden", "retirement": "required"},
    "superseded": {"consultation": "forbidden", "revisit": "forbidden", "wiring": "required", "floor": "forbidden", "retirement": "forbidden"}
  }
}
```

### 6.3 Decision record (case store)

Coordinates: recalled by full scan of cheap one-line summaries, so activation
*is* the summary line plus a hook; the payload constrains future forks rather
than commanding present work, so enforcement nearly vanishes and the warrant
dominates — a falsification list, because "is this still correct?" is the
live question.

```json
{
  "id": "D-0007",
  "kind": "decision",
  "status": "accepted",
  "scopes": ["tools/http", "task-family/api-calls"],
  "summary": {
    "latch": "a tool call that can time out; a retry wrapper; an HTTP client in the tool layer",
    "not_this": ["a retry inside the model's own reasoning loop"],
    "stakes": "a silent retry hides the cause the oracle scores on; passes score green while the fault persists"
  },
  "context": "…what was open, and why a fork had to be settled once…",
  "options": [
    {"name": "A — retry with cause preserved", "judged": "chosen", "why": "…"},
    {"name": "B — retry and swallow", "judged": "rejected", "why": "…"}
  ],
  "decision": "A wrapper that retries a tool call carries the underlying cause on every rethrow.",
  "counterfactual": "The overshoot is a wrapper that carries the cause but never retries — observed in O-0031, where a single transient 502 failed the whole task.",
  "warrant": {
    "anchors": ["weave:///proj/call/…", "O-0031", "O-0044"],
    "premises": [
      {"id": "p1", "statement": "the oracle's scorer reads the final error message", "falsifier": "a scorer change that grades on exit code only", "status": "supported"},
      {"id": "p2", "statement": "transient tool failures recur across the suite", "falsifier": "two consecutive consolidation passes with zero transient failures in the trace store", "status": "supported"}
    ],
    "adjudication": {"ledger_entry": "H-0021", "species": "attack", "verdict": "survived-with-attack-named"}
  },
  "latches": [
    {"type": "consultation", "slot": "payload", "key_space": "work-shape", "edge": {"kind": "level", "at": "boot"}, "guard": {"terms": ["tool-call-retry", "http-tool"], "not_this": ["reasoning-loop-retry"]}, "consumer": "the working pass", "owed_act": {"class": "apply", "role": "dispositive"}, "lifecycle": {"status": "live"}},
    {"type": "revisit", "slot": "warrant", "key_space": "world-state", "edge": {"kind": "edge", "predicate": {"evaluation": "suite-v1", "scorer": "error_cause_present", "comparator": "<", "value": 0.5, "persistence": 2}}, "guard": {}, "consumer": "the backward pass", "owed_act": {"class": "re-adjudicate", "role": "dispositive"}, "lifecycle": {"status": "live"}}
  ],
  "enforcement": {"floor": ["schema", "settlement-test", "complement-law"], "residue": ["whether the retry policy is the right one is judgment; the floor checks shape only"]},
  "lifecycle": {
    "consumer": "the working pass, at boot, on a matching work-shape",
    "moot_when": "the tool layer stops exposing retryable calls",
    "retirement": {"type": "retirement", "slot": "lifecycle", "key_space": "competence", "edge": {"kind": "schedule", "at": "consolidation"}, "guard": {"applied_over_considered_below": 0.1, "over_passes": 6}, "consumer": "the lifecycle review", "owed_act": {"class": "retire", "role": "corroborating"}, "lifecycle": {"status": "live"}}
  },
  "priced_for": {"model_id": "…"}
}
```

Status vocabulary: `proposed` → `accepted` → `superseded` | `moot`. A
decision is never edited after acceptance; a still-standing change folds
into a successor record with reciprocal `lineage` pointers. A premise's
`status` (`unevaluated` | `supported` | `disputed` | `reversed`) is the one
in-place flip a warrant takes, and only a disposed fire may flip it.

**Do:** write the `decision` field as one constraint on future forks,
object-decoupled ("errors that wrap carry their cause"). **Don't:** don't
write a duty sentence into a decision ("always add a cause when retrying")
— a present-tense obligation binding future work is a rule, and carrying it
in a frozen record is duty conflation: the adoption state silently rots.

### 6.4 Rule record (duty store)

Coordinates: recalled associatively over dozens of heavy duties, so
activation must be a routable key with a precision control; the payload
binds at work time, so the enforcement slot is obligatory; the live
question is propagation, so the register is the dominant instrument.

```json
{
  "id": "R-0003",
  "kind": "rule",
  "status": "enrolled",
  "fires_when": {"terms": ["tool-call-retry", "error-wrapping"], "not_this": ["reasoning-loop-retry", "a mocked tool in the evaluation harness"]},
  "duty": "When authoring a wrapper that retries or rethrows a tool call, carry the underlying cause on the rethrown error.",
  "counterfactual": "The overshoot: wrapping every exception including cancellation, which turned a user abort into a retry storm (O-0052).",
  "warrant": {
    "decisions": ["D-0007"],
    "enrollment": {"non_propagation_instance": "O-0049", "anchors": ["weave:///…"]},
    "adjudication": {"ledger_entry": "H-0030", "verdict": "admit"}
  },
  "enforcement": {
    "floor": [{"gate": "lint.retry_wrapper_has_cause", "checks": "the wrapper constructor receives a cause argument"}],
    "residue": ["whether the cause passed is the *right* cause is judgment"]
  },
  "adoption": [
    {"site": "tools/http.py", "cell": "adopted", "anchor": "commit:…", "reason": null},
    {"site": "tools/shell.py", "cell": "checked-N/A", "anchor": null, "reason": "no retry path"},
    {"site": "tools/browser.py", "cell": "unchecked", "anchor": null, "reason": "carried: not touched since enrollment; site still owes a triage"}
  ],
  "lifecycle": {
    "consumer": "the working pass on a matching work-shape; the demotion review",
    "review": {"applied_over_considered": "derived from dispositions/", "window_passes": 6},
    "moot_when": "no tool exposes a retry path",
    "coverage_migration": "when lint.retry_wrapper_has_cause owns the whole duty, de-enroll; D-0007 stays as warrant"
  },
  "priced_for": {"model_id": "…"}
}
```

Status vocabulary: `proposed` → `probation` → `enrolled` → `demoted` |
`retired` (`retired` carries `reason`: `mootness` | `coverage-migration`
| `other(<what>)`). The adoption register is hand-authored — the
`unchecked` cell is the absence of a decision and cannot be derived — and
every `unchecked` cell carries a mandatory carry reason. Cells:
`adopted` | `adopted-partial` | `checked-N/A` | `unchecked` | `inherited`.

**Do:** state the duty as narrow as is true and the hook as broad as is
predictive; recover precision through `not_this`, never by shaving the
hook. **Don't:** don't broaden the hook past any plausible route to the
payload — a hook matching shapes with no relation to the duty trains the
reader to skim, and skimming is a miss factory.

### 6.5 Observation record (pre-admission stratum)

Coordinates: the entry bar sits at the floor — one noticing, one anchor,
seconds of cost — so the record carries only activation and anchor. It
belongs to no leg until promotion.

```json
{
  "uid": "018f3c2e-…",
  "name": "O-0031",
  "kind": "observation",
  "status": "open",
  "noticed_at": "2026-09-12T14:03:22-07:00",
  "session": "S-0009",
  "noticed": "the http tool's retry wrapper drops the original 502 body when it rethrows",
  "anchor": {"call": "weave:///proj/call/…", "path": "tools/http.py:41"},
  "recheck_when": "touching error wrapping in any tool",
  "shape": [],
  "disposition": {"state": "open", "pointer": null, "at": null}
}
```

`recheck_when` on an observation is an **advisory, not a latch**: the same
words on a decision are a governed latch; here they are a note-to-self. The
class decides, not the field's shape. `shape` is empty at intake and filled
by the consolidation pass's grouping, never by the noticing session (labels
minted ahead of instances are priming). `disposition.state`: `open` |
`promoted` | `dismissed` | `expired`; a promoted observation is
delete-with-pointer — the pile empties *by* promotion.

Identity: the `uid` never recycles; the `name` is a momentary handle that
may recycle. Eternal identity attaches at admission (§ 7).


### 6.8 Fire record (ledger)

```json
{"id": "F-0187", "kind": "fire", "fired_at": "2026-09-12T20:11:04-07:00",
 "latch": {"record": "B-0012", "index": 0},
 "edge_event": {"evaluation": "suite-v1", "pass": 5, "scorer": "task_pass_rate", "observed": 0.58, "source": "weave:///…"},
 "guard_result": true,
 "disposer": "the backward pass",
 "disposition": {"act": "re-adjudicate", "outcome": null, "at": null, "by": null}}
```

A fire that cannot name its disposer is a standing false alarm by
construction and is refused. `hgi boot` prints every undischarged fire whose
disposer is the working pass; `hgi consolidate` prints those owed to the
backward pass. Same-commit settlement is the degenerate case: a fire whose
disposition is the settling commit itself.

### 6.9 Use-time disposition (ledger)

```json
{"id": "U-1042", "kind": "disposition", "session": "S-0014", "record": "R-0003",
 "considered": true, "guard_passed": true,
 "disposition": "applied",
 "note": "wrapper in tools/http.py rewritten to carry cause"}
```

`disposition` vocabulary: `applied` | `considered-not-applicable` |
`fired-off-map` | `guard-failed` | `other(<what>)`. Written once per
consulted record per pass; the demotion review reads the ratios. Catch
rate is never a target.

### 6.10 Steer record (ledger)

```json
{"id": "T-0009", "kind": "steer", "at": "2026-09-13T09:20:00-07:00",
 "source": {"kind": "oracle", "anchor": "weave:///proj/feedback/…"},
 "correction": "the pass applied R-0003 and the suite still regressed on error-cause scoring",
 "indicts": {"record": "R-0003", "slot": "payload", "signature": "recalled-applied-still-corrected"},
 "why_not_caught": "no floor reads the cause's content; residue as disclosed",
 "matrix_cell": "system-misses/human-catches"}
```

`source.kind`: `human` | `oracle` | `other(<what>)`. An oracle-sourced
steer is an evaluation regression whose credit assignment (record, slot)
was performed by the adjudicator, never by the pass that produced the
regression. Yield per steer is the quantity to maximize; steer count is
never a target.

### 6.12 Session record

```json
{"id": "S-0014", "kind": "session", "pass": 5,
 "started_at": "…", "closed_at": "…", "model_id": "…",
 "trace_root": "weave:///proj/call/…",
 "work_shape": {"terms": ["tool-call-retry", "json-output"], "escapes": ["other(streaming-tool)"]},
 "consulted": [{"record": "R-0003", "disposition": "U-1042"}, {"record": "D-0007", "disposition": "U-1043"}],
 "fires_seen": ["F-0186"],
 "predictions_frozen": ["B-0012"],
 "observations_filed": ["O-0058", "O-0059"],
 "proposals": ["draft:…"],
 "evaluation": {"evaluation": "suite-v1", "run": "weave:///…", "scores": {"task_pass_rate": 0.58}},
 "carry_forward": "…what the next pass boots from: open fires, live triggers, the one-paragraph state…"}
```

The session ledger is append-only; the `carry_forward` field is the one
register-shaped surface inside it and is rewritten only by the closing pass
that owns it.

### 6.13 Lens

A lens is a duty class, never a record class: it fills a host's payload
slot with a question. It is stored under `registry/lenses.json` so it can be
versioned and priced, and hosted by a boot step, a close step, or an
examiner dispatch template. It still evaluates the whole contract at the
lens's coordinates: activation is its host's walk; the payload a question,
never an answer; the **warrant** is effect evidence — `warrant.evidence:
genesis` at seed, and `anchors` derived at consolidation from the products
that reached a consumer (an observation promoted, a contradiction settled, a
claim upheld, a steer citing the lens); enforcement is the floor's shape
checks, answer truth the residue; the **lifecycle** is a `status` (`live` |
`retired`) with two doors — variance-collapse, when its product stops
varying over the review window, and the genesis deadline every seed shares
— each a nomination the adjudicator decides. An examiner-hosted lens
declares `claims`: the attack-claim target classes its angle may land on.

```json
{"id": "L-0002", "kind": "lens", "status": "live",
 "warrant": {"evidence": "genesis", "anchors": []},
 "angle": "What did this pass make false in the store — which premise, which hook, which adoption cell?",
 "counterfactual": "The overshoot is inventing a falsification to have one to report; an answer with no record id is not filed (T-0003).",
 "purpose": "adjudicative",
 "externality": {"contact": "record", "terminates_in": "the store's premises and cells, cited by id"},
 "product": "a list of {record, slot, what-changed, anchor}; empty is a legal answer",
 "consumer": "the backward pass",
 "host": "close",
 "priced_for": {"model_id": "…"},
 "telemetry": {"answer_variance": "design-stage", "decoy_rejection": "design-stage", "miss_stream": "steers/ citing this lens"}}
```

`purpose`: `adjudicative` (terminates in an authority — a record, the
oracle, a vocabulary — never in the answerer) | `generative` (touches the
item, is never handed an answer). A lens whose answer could have been
produced without reading the item — the sub-second "checked" — is the
ceremony tell; the count-and-provenance form of § 8.4 is the standing
countermeasure.

### 6.14 Registry

`registry/vocabulary.json` holds every closed vocabulary with per-term
`means` and `since`; `registry/ports.json` the port declarations;
`registry/constitution.json` the cap; `registry/lenses.json` the lens
register; `registry/bars.json` the promotion bars (§ 10.4). The registry is
a register: corrected in place, git carries history. Growth is by the
route-before-mint ladder on escape recurrence — two same-shaped escapes from
**independent** passes nominate a term; two from one pass are one datum.

## 7. Identity and the write law

Writes are event-sourced. One canonical source per record; every index a
regenerated projection; ids reserve-once, immutable, gap-tolerant;
retirements tombstone with successor pointers; refinement is a successor
record or a status flip, never a rewrite of evidence. Git is the commit
substrate: **admission is a commit**, and the `admission.commit` field on
the envelope is the anchor.

**Register versus ledger.** A register is a hand-authored statement of
current state, corrected in place (the registry, a session's
`carry_forward`, a rule's adoption register). A ledger is an append-only
history, never edited (observations before promotion, fires, dispositions,
steers, hypotheses, sessions). A current state maintained as history rots
into archaeology; a history amended in place stops being evidence.

**The pre-admission tier.** Observations and drafted proposals live below
the eternal store. Eternal identity attaches at admission, not at intake:
a draft carries a non-recycled `uid` and a recyclable human-facing `name`;
the committer mints the eternal id (`D-0007`) at admission and stamps
provenance from the draft's frozen date. Membership test: referenced by no
admitted record and named in no ledger — no in-edge from the eternal graph.
A declined draft is dropped without a tombstone, because a vertex with no
in-edges breaks no path.

**Do:** mint eternal ids only in the committer, from a monotone counter
kept in `registry/ids.json`, in the admitting commit. **Don't:** don't
encode tier, status, or any revisable slot in an id — promotion would break
it; and don't let the proposing pass reserve an eternal id "to reference
later" — a proposal references its draft `uid`, and the committer rewrites
the reference at admission.

**Same-commit settlement.** A revisit trigger's `settled` field, a fire's
`disposition`, a premise's `status` flip, and the change that settles them
land in one commit. A fired-but-unsettled latch is a standing false alarm;
a settled-elsewhere latch is a silent one.

**The lineage DAG.** Successor edges compose into a DAG, not a chain:
a fold has one successor with two predecessors, a split one retiree with
several heirs. The history of being wrong is read off it as a path query
(`hgi lineage D-0007`).

**Projections.** `index/` holds regenerated read models only: the
hook-major index (§ 8.2), the live-trigger list, the evidence-state table,
the undischarged-fire list, the adoption gap list. `hgi index` regenerates
them; a gate refuses a commit whose committed projections differ from
regeneration (materialized-and-gated).

## 8. The forward pass — the read path and the pass

Every read surface is one pattern: **a mechanical, legible, hard
pre-attention stage assembles what enters context, and the model's native
attention does the conditioning.** Stage one has two design surfaces —
selection (which records enter) and composition (what authored text
accompanies them) — and no gradient will ever repair either, so both stay
legible, auditable and rewritable.

### 8.1 Boot assembly

`hgi boot --session S-0015 --pass 6` performs, in order:

1. **Constitution** — every article loads unconditionally, under the cap.
2. **Carry-forward** — the previous session's `carry_forward` header and
   its undischarged fires whose disposer is the working pass.
3. **Work-shape classification** — the pass names its work-shape in terms
   from the registry, with `other(<what>)` for any presentation the
   vocabulary lacks. The classification is a model call whose output is
   parsed against the registry; escapes are recorded on the session.
4. **Stage-one selection** — the hook-major index is matched against the
   work-shape terms (§ 8.2). Considered, guard-failed and fired latches are
   distinguished and logged.
5. **Composition** — the boot lenses walk (§ 8.3) and the consultation
   plan prints: the count and the ids of records entering context, each
   with the owed act.
6. **Belief status projection** — every active prediction whose deadline
   is this pass or earlier, with its computed evidence state.

The assembled window is the query's result set. Progressive disclosure
throughout: every store leads with the cheapest cue that can carry
recognition and defers its mass until the cue fires.

**Do:** presume the store when a step is a consultation — "print the index
and open every record whose hook matches" — so the pass's only degree of
freedom is what the store holds. **Don't:** don't hedge a consultation into
an option ("consider whether a decision might apply"); a hedged step lets
the pass skip the read and call the skip a judgment.

### 8.2 Selection: the hook-major index and the settlement test

Storage is record-major; the stage-one index is **hook-major**: for each
work-shape term, the records whose consultation latches carry it, with the
records' `not_this` exclusions. Matching is exact over registered terms;
a lexical fallback (stemmed token overlap against `summary.latch` prose)
is legal only as a *nominator* whose hits are logged as
`considered` with `guard_passed: false` unless a registered term also
matches.

Which stage owns which selection tracks corpus size × per-item weight ×
miss cost. Rules — heavy, numerous, high-miss-cost — get routed activation
with declared firing shapes. Decisions — cheap one-line summaries — get a
bare full scan of summaries plus the hook match. Beliefs have no
consultation hook: they are reached by the status projection and their
revisit ports.

**The settlement test** governs every index cell: *a projection cell may
carry anything a reader cannot comply with without opening the record;
anything a reader can obey directly from the cell is evicted to the full
record.* Titles, hook terms, stakes, and a trigger's `when` pass; a rule's
duty sentence and a trigger's `then` fail. Consuming a conclusion from a
summary cell is the named failure — authority leak. The lint (§ 11)
enforces the test mechanically on projection templates.

Store-derived composition at the index: the **decision index hides the
rule** (hook, stakes, live trigger conditions — never a compliable
sentence); the **rule index hides the duty and leads with the residue** —
what the floor does not check — because leading with the duty invites
automation complacency.

### 8.3 Composition: lenses

Alongside every selected record travels authored text — a question, a
schema, a directive's wording — and that text is a design surface with its
own leverage: hold the model, the retrieval and the selected context fixed,
and varying only the authored question moves task outcomes by double
digits in the controlled literature. Composition is *unstably* powerful:
meaning-preserving rewording alone moves accuracy by tens of points, in
both directions. A piece of composition is therefore never prose: it
carries an id, an effect claim, a model it is priced for, and its repair is
a governed rewrite.

The lens is composition's unit (§ 6.13). Boot and close each walk a small
fan; the examiner's dispatch hosts the attack lenses — one call per angle,
each contributing only the claims of its declared class, the adjudicator
joining them (Appendix A.3). Laws:

- **The externality law.** Every lens forces the strongest contact outside
  the answerer its subject affords — a record read, an artifact cited, an
  oracle value read off — and declares the residue where the answerer is
  the authority. An adjudicative lens terminates in an authority, never in
  the answerer; a generative lens touches the item and is never handed an
  answer.
- **The fan law.** A fan earns its plurality only as decorrelation: one
  angle per context, a distinct product per angle, the adjudicator never
  the answerer. A fan violating any clause is a longer prompt, not an
  ensemble.
- **Refutation phrasing and stipulated certainty.** An adjudicative lens
  asks what would make the answer false and whether that reading was taken
  ("what reading of the trace would show the rule was not applied, and has
  it been read?"); a generative lens stipulates the failure ("the first
  attempt was wrong somewhere — where?"), because a lens asked as a
  possibility is answered no by default.

**Do:** keep the boot fan to the angles the loop's miss stream has earned
— a lens with no anchored instance in `steers/` or `ledger/` is ceremony.
**Don't:** don't hand an adjudicative lens its expected answer — a lens
that names the refutation it expects is a consultation in a lens's
clothes, and the supplied answer substitutes for the contact the lens
exists to force.

### 8.4 Work and use-time dispositions

Work proceeds with micro-decisions delegated to the strongest available
adjudicators — the tool results, the tests, the oracle's scorers — and
verification behavioral. Every model call and tool call is traced through
the oracle's tracer (`@weave.op`), and the session id and the ids of the
records in context ride on the trace as attributes, so every trace call
can be joined back to what the pass was conditioned on.

**Consultation reporting.** The pass reports its consultation as a count
with ids and dispositions — "consulted 3: R-0003 applied, D-0007
considered-not-applicable, F-0186 discharged" — because a count with ids is
a pointer no answer can fabricate without the reads behind it. Each entry
becomes a use-time disposition record (§ 6.9). An empty count is a fact the
close records as `fired-off-map` when work matched no hook.

Candidate signal is jotted at the observation floor as work runs: one
noticing, one anchor, seconds of cost. Capture must stay near-free or the
capture problem wins.

### 8.5 Evaluate

At the end of the act phase the oracle runs the pass's evaluation (§ 9.2):
the task suite is scored, the results land as facts with `as_of`, and the
watch predicates of every active belief are evaluated against them. Fires
are emitted for every watch whose guard passes; each names its disposer.
Predictions whose deadline is this pass settle through their dispositive
fires; the settlement writes `verdict` and `score` in the same commit as
the fire's disposition.

### 8.6 Close

`hgi close` produces the backward pass's inputs — the step pile-based
practice omits:

1. **Reflect, streams first.** The close lenses walk against the session's
   typed event streams — fires, dispositions, the evaluation delta — before
   free recall.
2. **Dispositions** — every consulted record has a use-time disposition
   or the close is refused.
3. **Observations** file to `observations/` with anchors; caught
   contradictions file to `ledger/` with the verdict `pending`.
4. **Steer capture** — a correction, human or oracle-attributed, lands as a
   steer record at the moment of correction, before the context that
   understood it is destroyed.
5. **The next prediction** — the pass freezes one belief record for a
   future pass: claim, kill criteria, deadline, reference at entry.
6. **Proposals** — candidate records drafted as `proposed` in the
   pre-admission tier, all five slots filled, every counterfactual
   anchored. The pass proposes; nothing it proposes is yet true.
7. **The session record** appends, with its `carry_forward`; `hgi index`
   regenerates the projections; the commit lands.

Boot consumes what the backward pass produced; close produces what it will
consume. That closure — not any individual store — is the system.

### 8.7 The iteration as a pass

The agent loop under test maps onto the pass one-to-one:

| Loop phase | HGI step | Artifacts |
|---|---|---|
| plan | `hgi boot` | consultation plan, fires owed, belief status |
| act | traced work | trace calls carrying record ids |
| evaluate | oracle evaluation | facts; fires; settlements |
| reflect | `hgi close` steps 1–4 | dispositions, observations, ledger entries, steers |
| predict | `hgi close` step 5 | one belief record |
| propose | `hgi close` step 6 | drafts in the pre-admission tier |
| learn | `hgi consolidate` (every *k* passes) | admitted, refined, retired records |

The loop "catches its own mistakes" through three channels and no fourth:
the oracle contradicts (scores, settlements), the examiner attacks
(proposals before commitment), and the store's own telemetry indicts slots
(§ 10.5). A pass grading its own work is self-noticed signal — lowest
trust — and never drives permanent structure alone.

## 9. The oracle

### 9.1 Roles

The oracle occupies four roles of the parent doctrine and refuses a fifth:

| Role | Occupied by | Never |
|---|---|---|
| the world — contradiction source | evaluation scores and settled outcomes | authoring a record |
| the fact floor | evaluation results, as-of-stamped, transcribed never adjudicated | a judgment |
| the trace store | traces of every call, joined to record ids | a projection to hand-edit |
| the steer channel | feedback attached to calls, human or oracle-attributed | a reward to maximize |
| the adjudicator | — | the oracle: it grounds, it does not decide the lesson |

**Oracle honesty.** Absent data reads `unevaluable`, never zero. A scorer
that cannot run reports `unevaluable` with a reason; a belief whose watches
are all `unwatched` displays `unwatched`, loudly. A watch on a surrogate
that is exactly wrong is worse than no watch: `unwatched` with the unblock
named is preferred over a crisp threshold on the wrong quantity.

### 9.2 W&B Weave — traces, evaluations, feedback

The exact SDK names below are stated as of 2026-09-12 from the Weave
Python SDK's public surface and are verified against the installed
version at slice 0 (§ 13); a rename changes this table, not the design.

| Need | Weave surface | HGI binding |
|---|---|---|
| trace store | `weave.init(project)`; `@weave.op` on every model and tool call; `weave.attributes({...})` | each call carries `hgi.session`, `hgi.pass`, `hgi.records_in_context`; the session's `trace_root` is the root call's URI |
| the world | `weave.Evaluation(dataset=…, scorers=[…])`, `weave.Scorer` subclasses, `weave.Dataset`; `await evaluation.evaluate(model)` (a coroutine as of weave 0.53.9; the op's `.call` form returns the summary and the root call) | the task suite is a `Dataset`; each scorer is a fact series named `<evaluation>/<scorer>`; results land in the fact floor with `as_of` and the evaluation-run URI as `source` |
| watch predicates | scorer outputs per evaluation run, read back through the Weave client (`weave.init(...).get_calls` / evaluation result objects) | `{evaluation, scorer, comparator, value, persistence}` evaluates against the last *persistence* runs |
| steer channel | feedback on calls: `call.feedback.add_note(...)`, `call.feedback.add_reaction(...)`, `call.feedback.add("hgi.steer", {...})`; read back with `client.get_calls(query=…, include_feedback=True)` — attributes must be a nested `hgi` object for `attributes.hgi.session` to resolve | a human note on a call becomes a steer with `source.kind = human`; an adjudicator-attributed regression becomes a steer with `source.kind = oracle` |
| fact anchors | call and object URIs (`weave:///…`) | every `anchor.call` and `reference_at_entry.source` is a Weave URI |
| model pricing | the model id on each call | `priced_for.model_id` on lenses and rules |

The evaluation battery has two members from slice 2 onward: the **task
suite** (the world the loop is judged on) and the **lens battery** (decoy
rejection for the close lenses — a louder non-causal signal planted in a
fixed dataset that the counterfactual must reject). The second is
design-stage in the parent doctrine and is the first thing HGI runs
because Weave makes it cheap.

### 9.3 ARIA — the consolidation analyst

ARIA reads runs, metrics and traces at scale, surfaces patterns, and drafts
reports of what changed and why. In HGI it is the **nominator** of the
backward pass and nothing more:

- **Reads:** the evaluation runs, the disposition ledger mirrored to Weave
  as a dataset, and the trace store.
- **Produces:** the consolidation brief — applied ÷ considered per record,
  fired-off-map clusters, the score delta per pass joined to the records in
  context, and escape-term clusters — as a report the consolidator agent
  reads, and as a persistent dashboard.
- **Never:** a verdict, a record, an edit. Its output is a proposal row the
  adjudicator disposes.

As of 2026-09-12 ARIA is invoked through the in-app chat and not through a
public API; the brief is produced interactively and its report URI is
recorded on the consolidation session. If a programmatic surface is
available at slice 4, the consolidator calls it; otherwise the consolidator
reads the exported report. Either way the machine enumerates, proposes and
audits — it never authors.

### 9.4 marimo — projections and the escalation surface

marimo notebooks are reactive Python scripts: a cell re-executes when a
value it depends on changes, and the file is plain `.py` under git. HGI
uses one notebook, `dashboard.py`, as:

- **the projection surface** — every `index/` read model rendered live
  from the store, regenerated on change, never hand-edited — the
  projection law of § 7 as a UI;
- **the escalation queue** — proposals whose verdict is
  `escalate(<why>)` appear with their attack, the oracle evidence and a
  two-button disposition that writes the verdict through the committer;
- **the runnable spec** — the demo's score curve, the lineage DAG, and the
  detection matrix, each a cell.

The notebook reads the store; it writes only through `hgi` commands.

### 9.5 TypeSafe AI — the machine-native adjudicator

TypeSafe's System1 model targets machine-to-machine execution and
real-time decisions. Where it is available at build time, HGI uses it in
the two roles that want a deterministic, non-narrative answerer:

- **the blind second coder** (the `coding` species): classifies raw
  anchored observations against the registry's shape terms *without seeing*
  the consolidator's candidate labels; agreement ratifies a class,
  disagreement keeps the boundary open;
- **the guard evaluator**: given a work-shape classification and a hook,
  returns the guard result, so the same context that will apply the payload
  does not decide whether it fires.

Fallback: a second, separately prompted frozen-model context with the
candidate labels withheld. The role is the invariant; the vendor is a
coordinate.

### 9.6 The inference endpoint — the frozen model, priced

The CoreWeave inference endpoint serves the frozen model for the pass, the
examiner, the adjudicator and the consolidator — four contexts, one model
or several. Every call records its model id; every lens and rule records
the model it was priced for. A model swap re-prices every conditioning
surface in both directions, and `hgi lint` warns on a lens whose
`priced_for` differs from the session's model.

### 9.7 What the oracle cannot do

The oracle settles claims and scores behavior; it cannot say what the
lesson is worth, which record absorbs it, or at what altitude. Those are
the adjudicator's and the consolidator's, under the separation of § 3.3.
A loop that lets scores write records directly has built a reward hacker
with a filing system.

## 10. The backward pass — consolidation

The forward pass generates signal; the backward pass consumes it and moves
knowledge between tiers. `hgi consolidate` runs every *k* passes (pinned:
`k = 2` for the demo) and on any fire whose disposer is the backward pass.
Consolidation runs at these passes and nowhere else.

### 10.1 Signals and the detection matrix

Four signal classes, never conflated: **the steer** (human or
oracle-attributed correction — credit assignment included); **the world**
(scores, settlements, fires — grounds claims, rewards nothing);
**recurrence counters** (the accumulator — nothing structural updates on
one instance); **self-noticed signal** (observations — lowest trust, never
permanent structure alone).

Every catch-or-miss event falls in a two-by-two:

| | oracle or human catches | neither catches |
|---|---|---|
| **store catches** (a latch fired, a floor refused) | redundant catch — demotion-side evidence; coverage migration nominated | the amortization working — the majority cell by design |
| **store misses** | **the steer** — reward and credit assignment, plus a free miss report: why did no latch fire? | the true miss — invisible until the world votes; repaired backwards from the manifested defect; counts are floors |

Health is mass migrating out of the bottom-left cell into the top row.

### 10.2 Noise-filter before updating process

Every failure is classified **irreducible** (no authoring duty could have
prevented it) or **reducible** (a duty was missed — route it). Irreducible
recurrences tune detection, never authoring. The classification is an
adjudicator verdict, not the consolidator's: the **triage leg** runs before
nomination over every observation group at the independence bar, the
adjudicator reading the observations and the rows they anchor; the verdict
lands on a `reality` entry (the observations' passes proposed the lesson,
the oracle's rows contradict or bear it), and an irreducible group is
dismissed with a pointer to the entry and leaves the brief, so no slot can
update on it.

### 10.3 Route before minting

A ratified recurrence lands at the cheapest sufficient home, walked in
order:

1. an edit to an existing record's counterfactual or `not_this`;
2. a row in an existing rule's adoption register;
3. a new rule enrolled under an existing decision;
4. a hook edit on an existing latch;
5. a new decision (only on a genuinely undecided fork);
6. a mechanical floor (only where the check is fully mechanical);
7. a constitution article (only with a forced eviction).

Refusal is a first-class outcome: every standing record taxes every future
pass, and the ladder prices that at admission. The consolidator's
nomination names the rung and why the cheaper rungs do not suffice.

### 10.4 Bars graded by blast radius

House convention, pinned in `registry/bars.json` as of 2026-09-12:

| Tier | Bar |
|---|---|
| observation | one noticing, one anchor |
| decision (promotion candidate) | two anchored observations of one undecided fork from independent passes, **or** one oracle-scored regression attributed by a steer |
| rule | an accepted decision plus one observed non-propagation instance |
| floor | two instances of silent failure through the same residue |
| constitution article | repeated evidence across at least three consolidation passes plus a forced eviction |

Counts nominate; the adjudicator decides; promotion raises abstraction.
Deeper, wider layers update slower — the damper an unreliable attribution
channel requires.

### 10.5 The slot-factored backward pass

Text space has no gradient, and "this rule seems wrong; rewrite it"
inherits the field's measured attribution weakness. The entry contract
restores tractability: **the five slots are the coordinate system in which
credit assignment becomes local.** Each signal carries a slot signature:

| Accumulated evidence | Indicted slot | Slot-local operator |
|---|---|---|
| fired-but-not-applicable dominates (applied ÷ fired low) | activation — precision | tighten the guard; grow `not_this` |
| fired-off-map — applied outside the declared hook | activation — boundary | widen or re-shape the hook |
| should-have-fired, surfaced by a steer or a defect backtrace | activation — recall | re-key; add a term; audit for the structural zero |
| recalled, applied — and the oracle still regressed | payload | re-abstract (altitude fault) or re-derive (content fault) |
| clean application on one recurring sub-shape, never on another | payload — fused | split: leaf the record |
| a premise reversed; a revisit trigger fired; anchors rotted | warrant | re-adjudicate; supersede or flip status |
| a defect shipped green through a floor | enforcement | grow the floor if newly mechanical; otherwise re-disclose the residue |
| the floor refuses correct behavior | enforcement — over-reach | shrink the floor to the invariant it serves |
| never fired across the review window; domain no longer entered; duty absorbed by a floor | lifecycle | demote, retire on mootness, or de-enroll by coverage migration — after the killer-item check |

Three properties keep the pass honest. **Locality:** the pass asks "which
slot does this evidence indict, and which way?", never "is this record
good?". **Typed sparsity:** the noise filter runs first; the evidence type
supplies the direction, the recurrence count the nomination, the
adjudicator the magnitude and verdict. **Floors, not rates:** several rows
read detection-limited streams, and should-have-fired has no complete
instrument; the pass treats those as lower bounds.

### 10.6 Split and fold

Two operators act on record granularity and both are moves on the lineage
DAG. **Split** (vertex split): dispositions bimodal across recognizable
sub-cases mark a fused record; it splits into leaves, each re-satisfying
the whole contract, the parent retiring by coverage migration or surviving
as the leaves' shared warrant — one tombstone, several heirs. **Fold**
(edge contraction): two records whose answers converge put their
differentiation under stress; entailment between their payloads is the
edge, and confirming it licenses the merge — two records, one successor.
Default fold-before-split; every split or fold is ratified against the raw
anchors, never the labels.

A belief record settles partially when a contradiction lands on a proper
region of its declared dimensions: the cut falls at the region boundary,
the falsified cell tombstones with a successor, surviving cells stand
untouched. A recurring **basis-free** contradiction — naming no declared
dimension — indicts the warrant wholesale, not any cell.

### 10.7 Promotion raises abstraction

Promotion that copies builds a recall cache, not a learning system: stored
raw instances transfer negatively, and the sign flips when they are stored
as abstracted insights. **Do:** restate the instance object-decoupled at
transferable altitude ("errors that wrap carry their cause"), and keep the
instance as the anchor. **Don't:** don't abstract past the evidence — a
payload the anchors no longer instantiate is a floating entry; the
adjudicator refuses a promotion whose anchors do not exemplify its payload.

### 10.8 Retirement legs

Every threshold pairs with a scheduled reverse: applied ÷ considered as
nominator, never verdict; mootness and coverage migration as retirement
keys, never low salience — the rarely-binding record can be the
killer-item, exempt regardless of count. Running the up-pipeline without
the down-pipeline accumulates confidently-wrong rules.

### 10.9 The adjudication protocol

For each nomination the consolidator emits, in its own context:

1. **Proposal** — the draft record, five slots filled, the ladder rung
   named, the verdict `pending`.
2. **Attack** — the examiner, in a fresh context per angle with the
   verbatim draft and read access to the store and the oracle, attacks the
   draft's claim list refute-phrased: each examiner-hosted lens is one call
   and contributes only the claims of its declared class (independence,
   the premise kill — the highest-value attack class — abstraction, watch
   direction), every claim naming its angle and call. Output: one attack
   payload with `verdict: pending`, the angles' union.
3. **Verdict** — the adjudicator, in a fresh context with the draft, the
   attack, the oracle evidence (scores, fires, settlements) and the bars,
   returns one token from the closed verdict vocabulary:
   `admit` | `admit-amended(<amendment>)` | `decline(<why>)` |
   `defer(<until>)` | `escalate(<why>)` | `other(<what>)`.
   `admit-amended` may amend only the slot the attack indicted, and the
   amendment is recorded on the ledger entry.
4. **Commit** — the committer runs the floor (§ 11) and admits on `admit`
   or `admit-amended`; declines drop the draft; `defer` re-queues with its
   condition as a latch; `escalate` routes to the marimo queue where a
   human returns a verdict from the same vocabulary.

The four contexts share no prompt beyond the store's schemas and the
lenses registered for each role, and the adjudicator sees the oracle's
evidence and the attack — never the proposer's narrative of the pass. A
nomination at a rung this roster has no operator for (`adoption-row`,
`rule-enrollment`, `floor`, `article` while the roster is decisions only)
is refused and recorded, never drafted as a decision under the rung's
name. Every ledger entry, of every species, names three distinct parties:
the currency species' contradictor is the oracle — the fire, the ratio,
the instance — never the adjudicator that verdicts it, and a pass that
contradicts a standing record at close contradicts a claim its admitter
proposed; the `role-separation` check proves it on every line.

**Do:** log every role's call to the trace store with its role attribute
so the ledger entry's `contradiction.source.call` and
`adjudicator.call` are joinable. **Don't:** don't let a `pending` verdict
be filled by any context but the adjudicator's — the schema refuses a
proposal or attack payload carrying a verdict.

### 10.10 The pipeline, worked end-to-end

One lesson through every tier:

**Noticing (bar: one instance).** Pass 3 notices the http tool's retry
wrapper drops the 502 body on rethrow. One line lands in `observations/`
with a trace anchor. No classification, no change.

**Promotion (observation → decision).** Pass 5 hits the same shape on the
shell tool. The consolidator groups the pile by shape: two anchored
instances of one undecided fork from independent passes — this move's bar.
A decision drafts in the case store's shape (options; constraining facts as
a falsification list), the examiner attacks premise p2, the adjudicator
returns `admit`; the payload is object-decoupled — *errors that wrap carry
their cause*, not *fix http and shell*. The observations flip to
`promoted` with pointers.

**Proceduralization (decision → rule).** The decision binds only if
recalled, and its domain is entered on every retry path. Pass 7's
dispositions show D-0007 `considered-not-applicable` while its trace shows
a fresh wrapper without a cause — observed non-propagation, the tell that a
case needs a rule form. The rule is the decision's duty form: its hook
`tool-call-retry`, the duty sentence carrying the obligation, the decision
cited as warrant. The case keeps the *why*; the rule the *when-and-what*.

**Mechanization (rule → floor).** Part of the duty proves fully
mechanical — *the wrapper constructor receives a cause argument* — and
fails silently twice (a green pass with the cause dropped). A lint takes
it; the rule's floor grows and its residue is re-disclosed: the gate checks
that *a* cause is passed; judgment still owns whether it is the right one.

**And back down.** Six passes later R-0003's dispositions read applied ÷
considered near zero because the lint owns the duty: de-enroll by coverage
migration, the rule living on at its floor, the decision staying as
warrant. The decision itself retires only on mootness.

At each handoff the slots change hands exactly as the coordinates predict:
the noticing had activation and anchor; the decision added a warrant; the
rule added routable activation and an enforcement obligation; the floor is
all floor.

## 11. Enforcement: floors and residue

Behavior binding is every context system's weakest link — a record acts
only if retrieved *and* applied. HGI binds mechanically where bindable and
directs attention to the rest by disclosure. `hgi lint` is the floor; its
docstring is the home of the check list, and this table is a dated
illustration of it as of 2026-09-12.

| Check | Seam | Fails / warns | What it does not check (residue) |
|---|---|---|---|
| schema | write | fails a record that does not parse against its declared type | truth of any field |
| closed vocabulary | write | fails an enum value outside the registry without an `other(<what>)` escape | whether the escape should have been a term |
| complement law | write | fails a decision without falsifiers, a rule without `not_this` and a counterfactual, a trigger without an act class; warns on a counterfactual with no anchor | whether the pair is non-vacuous |
| settlement test | write | fails a projection template whose cell carries a compliable sentence (a duty, a `then`) | compliance by omission — a stakes cell reading "low" is compliable by not opening the record |
| verdict authority | write | fails a proposal or attack payload carrying a verdict other than `pending` | whether the adjudicator's verdict is right |
| role separation | write | fails a ledger entry whose proposer, contradictor and adjudicator are not three distinct roles, or whose two role calls are one call | whether two contexts of one model share a prior |
| key-space | write | fails a neighbour latch naming a record that does not exist; fails a world-state watch naming a scorer or evaluation the oracle does not run | whether the referent is the right quantity to watch |
| fire disposer | write | fails a fire record naming no disposer | whether the disposer discharged it well |
| disposition completeness | close | fails a close with a consulted record lacking a disposition | whether the disposition was honest |
| constitution cap | write | fails a commit exceeding `max_articles` or `max_bytes` without an eviction | the ranking |
| adoption triage | consolidation | warns on an `unchecked` cell without a carry reason | whether the triage judgment was right |
| projection coherence | commit | fails a commit whose `index/` differs from regeneration | nothing — total |
| consumer-edge acyclicity | commit | fails a latch whose owed act modifies a latch that keys on it, over declared edges | undeclared edges |
| model pricing | boot | warns on a lens or rule priced for a model other than the session's | the size of the re-pricing |
| oracle honesty | runtime | fails a fact with a missing value written as zero | a scorer measuring the wrong quantity |

Two seams beyond the lint: the **review seam** (the examiner over a
committed draft) and the **consumption seam** — read the record, never only
its projection, and treat a conclusion found only in a projection as an
undecided fork to reopen. The consumption seam cannot be mechanized in a
corpus a model reads as text; the settlement test moves what it can to the
write side and the boot lens carries the rest.

**Do:** grow a floor only when the failed part is newly mechanical and has
failed silently twice; re-disclose the residue in the same commit.
**Don't:** don't grow a floor to the whole duty because a check *can* be
written — a floor that refuses correct behavior is over-reach, and the
slot-factored pass shrinks it back to the invariant it serves.

## 12. Telemetry and health

Feedback is behavioral only; catch-rate is never a target. Every
instrument reports floors, never rates, because observed-zero is
detection-limited.

| Instrument | Source | Reads |
|---|---|---|
| applied ÷ considered per record | `dispositions/` | the demotion nominator |
| fired-off-map count | `dispositions/`, sessions' `work_shape.escapes` | hook boundary defects; vocabulary growth |
| considered-but-guard-failed vs fired-but-not-applicable | latch telemetry | routing working vs guard indicted |
| should-have-fired | `steers/` archaeology | recall — a floor, never complete |
| attacker precision | `ledger/` attack entries: landed ÷ dispatched | a persistently-zero rate interrogates the dispatch bar before targets are declared clean |
| skill per settled belief | `beliefs/` verdicts vs reference | the planner's calibration prior |
| detection matrix | steers × fires | health trajectory: mass migrating out of the steer cell |
| structural-zero audit | index × records | records no consultation hook reaches |
| recall stream | the boot recall lens's probes; steers indicting activation | should-have-fired per record — a floor; the `hook-edit` nominator |
| attacker precision | `ledger/` attack entries: landings upheld ÷ entries with a landing, per angle; the should-have-been-caught-by stream | a persistently-zero landing count interrogates the dispatch bar; a precision of one over zero overrulings is a ceiling artifact |
| unwatched | `summaries` | a record no world-state watch can send back for re-adjudication — displayed, never defaulted |
| lens variance and decoy rejection | the lens battery evaluation | crystallization signal; the floor gate of the close lenses |
| escape recurrence | sessions, ledger | vocabulary and port widening nominations |

The marimo dashboard renders every row live. ARIA reads the mirrored
datasets and drafts the consolidation brief from them. No instrument
settles anything: the net may be shown; it may never settle; the
adjudicator disposes.

## 13. Build plan: slices and milestones

The hackathon window: hacking opens 2026-09-12 at 11:15; the venue closes
at 21:00; doors reopen 2026-09-13 at 09:00; submissions are due at 13:00;
judging starts 13:30. Clock targets below assume slice 0 begins by 12:30 on
2026-09-12; a slip shifts every later target, and § 13.3 states what to
cut.

Each slice names its deliverable, its acceptance test, and the evidence
the demo takes from it. A slice ships only when its acceptance test runs
green; a slice that cannot ship declares what it left out — never a weaker
test that happens to pass.

### 13.1 Slices

**Slice 0 — Skeleton and floor.** Target 2026-09-12 14:00.
Deliverable: the repository (Appendix B); `hgi/types.py` with every record
kind of § 6 as typed models; the registry seeded (Appendix C: vocabulary,
ports, bars, constitution cap, the boot and close lens fans); the store
directories; `hgi lint` with the write-seam checks of § 11; `hgi index`
regenerating the hook-major index and the fire and trigger lists; id
minting in the committer; the Weave SDK names of § 9.2 verified against the
installed version and corrected in this document if they differ.
Acceptance: a hand-authored decision and rule admit through the committer;
a malformed record, a proposal carrying a verdict, a fire without a
disposer, and an eighth constitution article are each refused with the
named check; `hgi index` is idempotent.
Demo evidence: none directly; everything later stands on it.

**Slice 1 — The oracle.** Target 2026-09-12 16:00.
Deliverable: the task suite as a Weave `Dataset` with a `suite_hash`
scorer; the scorers of § 14.1; `hgi evaluate` running the evaluation for a
pass and writing facts (`<evaluation>/<scorer>`, `as_of`, source URI); the
watch evaluator over the last *persistence* runs; fire emission with
disposer; postdiction transcription for a claim whose deadline predates it.
Acceptance: one evaluation run lands as facts; a belief with a `falsify`
watch fires when the fact crosses; the fire names the backward pass; a
scorer that cannot run yields `unevaluable`, and a fact of zero from a
missing value is refused.
Demo evidence: the first point on the score curve.

**Slice 2 — The forward pass.** Target 2026-09-12 18:30.
Deliverable: `hgi boot` (§ 8.1) and `hgi close` (§ 8.6) end to end; trace
attributes carrying session, pass and records-in-context; the
count-and-provenance consultation report; use-time dispositions enforced
at close; observation intake; steer capture from Weave feedback; the
per-pass prediction; drafts into the pre-admission tier; the session record
with `carry_forward`. The agent under test wrapped as a `weave.Model`.
Acceptance: two consecutive passes run with the store attached; each
session record lists its consulted ids with dispositions; the second pass
boots from the first's carry-forward and sees its undischarged fires; a
close with a missing disposition is refused.
Demo evidence: the consultation reports; the trace joined to record ids.

**Slice 3 — The backward pass.** Target 2026-09-12 21:00.
Deliverable: `hgi consolidate`: the consolidator's nomination brief
(observations grouped by shape under the independence qualifier; applied ÷
considered; the slot-indictment table of § 10.5); the examiner dispatch;
the adjudicator verdict from the closed vocabulary; the committer; the
ladder with the rung named; the bars; the observation → decision
promotion with abstraction; `decline` and `escalate` paths; the
hypothesis ledger populated with joinable call URIs.
Acceptance: from two seeded, independent observations of one fork the
pipeline admits a decision whose payload is object-decoupled and whose
observations flip to `promoted` with pointers; an attack that kills a
premise yields `decline` and drops the draft; an `escalate` lands on the
queue file the dashboard reads; no context but the adjudicator's ever
writes a verdict (the lint proves it on the ledger).
Demo evidence: one lineage path from observation to decision with its
ledger entry.

**Slice 4 — The duty store, retirement, projections, the analyst.**
Target 2026-09-13 10:30.
Deliverable: rule enrollment on observed non-propagation with the adoption
register; one mechanical floor grown from a rule's residue after two
silent failures; the retirement leg on applied ÷ considered over the
review window; coverage migration; the marimo `dashboard.py` rendering the
index, the evidence-state table, the lineage DAG, the detection matrix and
the escalation queue with its two-button disposition; the ARIA
consolidation brief over the mirrored runs, its report URI recorded on the
consolidation session.
Acceptance: a rule enrolls under an accepted decision and its hook routes
it at the next boot; one record demotes or de-enrolls on telemetry alone;
the dashboard renders from the store with no hand-edited cell; the
escalation button writes through the committer and the lint stays green.
Demo evidence: the promotion chain completed to the rule tier; a
retirement; the dashboard.

**Slice 5 — The demo run and the ablation.** Target 2026-09-13 12:15.
Deliverable: the full run of § 14 — six passes with the store attached,
six detached, same suite hash, both in Weave; the score curve; the
calibration table over settled beliefs; the detection matrix; the README
(what it is, how to run it, what the curve shows, what it does not show);
the two-minute recording; the submission.
Acceptance: § 14.3 in full.
Demo evidence: everything.

**Slice 6 — Stretch, in order.** Only after slice 5 is submitted or
clearly safe: (a) the lens battery with decoy rejection scored in Weave;
(b) the TypeSafe blind coder and guard evaluator with the fallback context
measured against them; (c) a conditioned belief with a mechanism-named
proxy and the per-conjunct trigger split; (d) the leaf cut on partial
settlement; (e) split and fold as executed operators rather than
nominations.

### 13.2 Milestones

| Milestone | Target | Means |
|---|---|---|
| M0 skeleton green | 2026-09-12 14:00 | slice 0 acceptance |
| M1 the world speaks | 2026-09-12 16:00 | slice 1 acceptance; first score on the curve |
| M2 a pass remembers | 2026-09-12 18:30 | slice 2 acceptance; two passes chained |
| M3 the loop learns | 2026-09-12 21:00 | slice 3 acceptance; one promotion admitted through attack and verdict |
| M4 the loop forgets and binds | 2026-09-13 10:30 | slice 4 acceptance; a rule routed, a record retired, the dashboard live |
| M5 the case is made | 2026-09-13 12:15 | slice 5 acceptance; ablation recorded; README and recording done |
| M6 submitted | 2026-09-13 13:00 | the submission form, the repository public, the recording linked |

### 13.3 Drop order under slip

Cut from the bottom, never from the middle: (1) slice 6 entirely; (2) the
ARIA brief becomes an interactive session whose report is pasted into the
consolidation brief by hand, its URI still recorded; (3) the dashboard
reduces to the score curve, the lineage DAG and the escalation queue;
(4) split and fold stay nominations without an executed operator; (5) the
mechanical floor grown in slice 4 is replaced by a re-disclosed residue and
the demo says so; (6) the review window for retirement shrinks from six
passes to three, pinned in the bars file and stated in the README.

Never cut: the separation of roles (§ 3.3), the disposition-completeness
check, the fire disposer, the ablation. A demo without the ablation shows
a curve with nothing to compare it to; a demo where the pass writes its own
records shows the collapse the design exists to avoid.

### 13.4 Genesis rules

The loop's first organs cannot have been admitted by the loop and need not
be — they are the seed. The seed is the smallest configuration that runs
one full cycle: the registry, the constitution under its cap, an empty
observation ledger with mandatory anchors, an empty decision store, the
session ledger. Everything else — every rule, every floor beyond the lint's
write seam, every vocabulary term past the seed — is minted by the loop
from its own miss stream, through the ladder, at the bars. Genesis
articles and genesis terms carry `warrant.evidence: genesis` and earn an
anchor by the third consolidation pass or are evicted.

**Do:** start the ledgers before the checkpoints — the loop generates
contradictions from pass one, and the ledger reveals which rules and floors
*this* loop needs. **Don't:** don't copy another project's rule roster into
`rules/` to look mature at the demo; a roster encodes its origin's failure
history, and a rule with no local non-propagation instance is a floating
entry the examiner will kill.

## 14. The demonstration and its acceptance bar

### 14.1 The task suite

Pinned as of 2026-09-12; a different suite changes this subsection, not the
design. A tool-using coding agent runs over a fixed suite of small Python
tasks, each graded by hidden unit tests, through a tool layer with
injected transient faults: an HTTP tool that returns a transient 5xx on a
fixed fraction of calls, a shell tool with a call budget, and a file tool.
The faults exist so that lessons are learnable across passes and the
oracle can score whether they were learned.

Scorers: `task_pass_rate` (hidden tests), `error_cause_present` (a failed
task's final error names its root cause), `tool_budget_respected`,
`output_schema_valid`, `suite_hash` (the composition guard). Every scorer
returns a value or `unevaluable`.

Alternative, if the coding harness is not ready by M1: a data-analysis
agent over a fixed set of marimo notebooks with hidden assertion cells,
the same tool faults, the same scorer shapes.

The suite is composed, not fixed by hand: task *families* — hand-written,
or transcribed once from a public dataset and pinned in the repository —
under one *fault profile* (how many leading calls of a faulted task fail,
which tools are budgeted, whether output truncates). The composition is a
parameter of the experiment, and the hash covers every task's
presentation, its world (files, routes) and the profile, so a harder world
is a different suite and the report keys on the arm. The families that
earn their place are the ones whose lessons are conventions of the world
rather than facts about one task: a convention recurs across tasks, so a
promoted record has anchors and a hook, and a budget makes it cost a call,
so the oracle can score whether it was learned.

### 14.2 The run

Six passes with the store attached; six passes detached (same agent, same
model, same suite hash, no boot or close); consolidation every two passes.
Each attached pass freezes a prediction about a later pass's
`task_pass_rate` with a reference at entry from the last run. Both runs are
recorded as Weave evaluations under one project.

### 14.3 Acceptance

The deliverable is accepted when every row holds, and the README reports
each row honestly, including any that fails:

1. **Curve.** Both curves are shown, memory-on and memory-off, over the
   same suite hash. The design is accepted whether or not the attached
   curve dominates — the honest reading is the deliverable; a reversed
   result files as a `reality` species entry against the design's own
   premises.
2. **One full chain.** At least one lineage path observation → decision →
   rule exists, with each admission's ledger entry, attack and verdict
   joinable to Weave call URIs.
3. **One retirement.** At least one record demoted, de-enrolled or made
   moot on telemetry, with the nominating ratio shown.
4. **Dispositions complete.** Every consulted record in every attached
   pass has a use-time disposition; at submission no fire whose disposer
   is the working pass is undischarged.
5. **Calibration.** At least four beliefs settled with reference-relative
   scores, in a table: claim, reference, outcome, score.
6. **Floor green.** `hgi lint` green; committed projections equal
   regeneration.
7. **Matrix populated.** The detection matrix shows at least one event in
   the steer cell and at least one in a system-catches cell.
8. **Roles separate.** Every ledger entry's proposer, contradictor and
   adjudicator calls are distinct traces with distinct role attributes.

### 14.4 What the demo does not show

Transfer to a second task family; behavior under a model swap; the lens
telemetry (design-stage unless slice 6a ships); anything about rates — every
count is a floor from one run.

## 15. Failure surface and boundary conditions

Stated honestly: the advantages and the costs are one design from two
sides.

1. **One frozen model judges everything.** Pass, examiner, adjudicator and
   consolidator may share a model; role separation buys structural
   independence of *context*, not of prior. Self-bias amplification is
   damped, not eliminated. The countermeasure that stays: self-graded
   labels never drive permanent structure alone — every admission cites
   oracle evidence.
2. **The oracle gate is weaker than a human gate.** A scorer measuring a
   surrogate lets the loop optimize the surrogate; the `unwatched`
   discipline and the settlement test are the defenses, and the
   escalation path is the relief valve. The design says so rather than
   pretending the relaxation is free.
3. **Silent misses are floors.** Should-have-fired has no complete
   instrument; recall is unmeasurable without ground truth.
4. **Thresholds are house convention.** The bars are pinned, dated and
   under-derived; the demo's few passes cannot calibrate them.
5. **Composition is priced per model.** A model swap re-prices every lens
   and duty sentence in both directions, and without the lens battery
   nothing would detect a swap voiding half the register.
6. **Presence, not quality.** The floor checks that records exist, parse
   and carry their slots; quality stays unmechanized by design, so the
   design's core quality claims are exactly its unmeasured ones.
7. **Forgetting is relocated.** Weight-forgetting is traded for retrieval
   failure; the structural zero is the new forgetting, and the audit only
   finds records with no hook, not records with the wrong one.
8. **Vendor surfaces move.** ARIA is interactive as of 2026-09-12; the
   TypeSafe model is behind a waitlist; SDK names change. Every binding in
   § 9 names the role as the invariant and the vendor as the coordinate.
9. **Twenty-six hours.** The floors are thin, the vocabularies are seed,
   and the ledgers are short. What the build proves is that the loop
   closes — boot consumes what consolidation produced, close produces what
   it will consume — not that the curve generalizes.

## Appendix A. Seed content

### A.1 Genesis constitution (seven articles, under the cap)

Each carries `warrant.evidence: genesis` and a counterfactual to be
anchored or evicted by the third consolidation pass.

| Id | Article | Counterfactual |
|---|---|---|
| C-0001 | The pass proposes; the backward pass admits. No pass writes to an eternal store. | The overshoot: a pass that files nothing because it cannot admit — proposals are the pass's product, not a courtesy. |
| C-0002 | Consultation is reported as a count with ids and dispositions; a bare assurance is a defect. | The overshoot: opening every record to inflate the count — the count nominates precision review, never quality. |
| C-0003 | Every claim is a hypothesis with an anchor; suspected and verified never share a register. | The overshoot: refusing to file a suspicion until it is verified — the observation ledger exists for the unverified. |
| C-0004 | The oracle grounds, the adjudicator decides, the committer writes; no context holds two roles. | The overshoot: an adjudicator that defers every verdict to escalation — `escalate` is for ambiguity, not for reluctance. |
| C-0005 | Promotion raises abstraction; a copied instance is refused. | The overshoot: an abstraction the anchors no longer instantiate — a floating entry. |
| C-0006 | Every floor discloses its residue; absent data reads `unevaluable`, never zero. | The overshoot: a residue list so long the floor is not worth running — a floor with no bindable part is not a floor. |
| C-0007 | Every threshold has a retirement leg; nothing is deleted, everything is superseded. | The overshoot: retiring the rarely-binding record for low salience — the killer-item is exempt regardless of count. |

### A.2 Genesis work-shape terms

Minted from the task suite's known presentations; each retires if unused
across three consolidation passes.

`tool-call-retry` · `http-tool` · `shell-tool` · `file-tool` ·
`output-schema` · `test-failure-triage` · `tool-budget` ·
`error-wrapping` · `task-planning` · `other(<what>)`

### A.3 Genesis lens fans

Boot fan (walked after selection, one context per angle):

| Id | Angle | Counterfactual | Purpose · contact |
|---|---|---|---|
| L-0001 | Which consulted record's hook fired on presentation alone and does not bear on this task? Name it and dispose it `considered-not-applicable`. | The overshoot: disposing every record not-applicable to shorten the read — a record applied nowhere in the pass is a demotion datum, and the trace will show it. | adjudicative · the index |
| L-0002 | The store holds a record this task needs and no hook reached it — which? | The overshoot: inventing a need to have a finding; an answer with no record id is not filed. | generative · the store |

Examiner fan (one call per angle; each lens declares the claim classes it
may land on; the adjudicator joins the angles):

| Id | Angle | Claims | Counterfactual |
|---|---|---|---|
| L-0005 | Do the draft's anchored observations come from independent passes, or is one context counted twice? | `warrant:independence` | The overshoot: landing independence on every draft whose observations share a task — independence is by session, never by task. |
| L-0006 | For each premise: what reading of the oracle's evidence would show it false — and taken, did it? | `premise:` | The overshoot: killing a premise from what the evidence does not show — `unevaluable` is never a refutation. |
| L-0007 | Does the payload name the transferable shape, or an instance — a task id, a file name, a path? | `payload:` | The overshoot: reading every concrete noun as an instance — a payload about the HTTP tool may name HTTP. |
| L-0008 | Does the revisit watch fire on the failure the stakes name, or on success? | `warrant:watch-direction` | The overshoot: landing on a watch a failing score also satisfies — it fires on the regression too. |

Close fan:

| Id | Angle | Counterfactual | Purpose · contact |
|---|---|---|---|
| L-0003 | What did this pass make false in the store — which premise, which hook, which adoption cell? | The overshoot: manufacturing a falsification; empty is a legal answer. | adjudicative · the store, by id |
| L-0004 | The first attempt in this pass was wrong somewhere — where, and which record should have fired? | The overshoot: grading the pass's own lesson as settled — the answer is an observation at the floor, never a rule. | generative · the trace |
| L-0009 | What would make the frozen prediction false before its deadline, and is each such event watched? | The overshoot: a watch on a surrogate that is easy to read — `unwatched` with the unblock named beats a precise wrong predicate. | adjudicative · the belief record |

## Appendix B. Repository layout and command surface

```
hgi/
  pyproject.toml
  hgi/
    types.py          # every record kind, declared once
    registry.py       # vocabulary, ports, bars, cap, lenses — loaders and validators
    store.py          # read/write, ids, the committer, the pre-admission tier
    index.py          # projections: hook-major index, triggers, fires, evidence states
    lint.py           # the floor; its docstring is the check list's home
    boot.py           # § 8.1
    close.py          # § 8.6
    evaluate.py       # § 9.2: evaluations, facts, watches, fires, settlement
    consolidate.py    # § 10: consolidator, examiner, adjudicator, committer
    roles/            # the four role prompts, each a file, each priced
    cli.py            # hgi boot | close | evaluate | consolidate | lint | index | lineage
  store/
    constitution/ decisions/ rules/ beliefs/ observations/ ledger/
    fires/ dispositions/ steers/ sessions/ registry/ index/
  suite/              # the task suite: tasks, hidden tests, the faulty tool layer, scorers
  experiments/        # experiment files; their arms run under runs/<experiment>/<arm>/, a repository each
  dashboard.py        # the marimo notebook
  README.md
```

Commands:

```
hgi boot        --session S-nnnn --pass n      # assemble; print the consultation plan
hgi evaluate    --session S-nnnn               # run the oracle; write facts; emit fires; settle
hgi close       --session S-nnnn               # dispositions, observations, steers, prediction, proposals, session record
hgi consolidate                                 # the backward pass over the ledgers
hgi lint                                        # the floor
hgi index                                       # regenerate projections
hgi lineage     D-0007                          # the path query over the DAG
hgi experiment  run experiments/<name>.toml      # every arm of an experiment file, each in a store of its own
```

Every command that writes ends in a commit whose message names the record
ids it admitted, flipped or retired.

## Appendix C. Closed vocabularies

Each ships `other(<what>)`; the registry is the home, this table an
illustration dated 2026-09-12.

| Vocabulary | Members |
|---|---|
| latch type | `consultation` · `revisit` · `wiring` · `floor` · `retirement` |
| key-space | `work-shape` · `world-state` · `neighbor` · `diff` · `competence` |
| edge kind | `level` · `edge` · `schedule` |
| act class | `apply` · `re-adjudicate` · `re-derive` · `check` · `retire` |
| owed-act role | `dispositive` · `corroborating` |
| latch lifecycle | `live` · `settled` · `moot` |
| decision status | `proposed` · `accepted` · `superseded` · `moot` |
| rule status | `proposed` · `probation` · `enrolled` · `demoted` · `retired` |
| belief status | `active` · `settled` · `moot` |
| belief verdict | `true` · `false` · `unevaluable` · `void` |
| reference class | `consensus` · `base-rate` · `persistence` · `incumbent` |
| watch mode | `falsify` · `corroborates` · `revisits` · `unwatched` |
| evidence token (derived) | `corroborated` · `rebutted` · `undercut` · `holding` · `unevaluated` · `unwatched` · `conflicted` |
| observation state | `open` · `promoted` · `dismissed` · `expired` |
| use-time disposition | `applied` · `considered-not-applicable` · `fired-off-map` · `guard-failed` |
| adoption cell | `adopted` · `adopted-partial` · `checked-N/A` · `unchecked` · `inherited` |
| steer source | `human` · `oracle` |
| species | `attack` · `collision` · `forecast` · `reality` · `currency` · `coding` |
| attack verdict | `pending` · `survived-with-attack-named` · `attack-landed` · `premise-killed` |
| collision verdict | `pending` · `derivation-wrong` · `implementation-wrong` · `contract-open` |
| forecast verdict | `pending` · `true` · `false` · `unevaluable` · `void` |
| reality verdict | `pending` · `reducible` · `irreducible` |
| currency verdict | `pending` · `still-holds` · `reversed` · `moot` |
| coding verdict | `pending` · `agree` · `disagree` |
| adjudicator verdict | `admit` · `admit-amended(<amendment>)` · `decline(<why>)` · `defer(<until>)` · `escalate(<why>)` |
| ladder rung | `counterfactual-edit` · `adoption-row` · `rule-enrollment` · `hook-edit` · `new-decision` · `floor` · `article` |
| slot | `activation` · `payload` · `warrant` · `enforcement` · `lifecycle` |
| lens purpose | `adjudicative` · `generative` |
| lens contact | `record` · `artifact` · `oracle` · `none` |
| lens host | `boot` · `close` · `examiner` |
| lens status | `live` · `retired` |
| role | `pass` · `consolidator` · `examiner` · `adjudicator` · `committer` · `coder` · `human` · `oracle` |
| retirement reason | `mootness` · `coverage-migration` |
