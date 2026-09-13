# Carry-forward

State of the build as of 2026-09-12, after the world run, with the work
left for the full implementation and the decisions taken along the way —
each with why it may be right and why it may not.

## Where it stands

- Slices 0–3 of spec § 13 ship with their acceptance tests green
  (`uv run pytest`, 94 tests). Slice 4 ships the dashboard, the analyst
  mirror and the retirement leg; the rule tier and the grown floor do not
  exist because the roster is decisions only. Slice 5 (the demo) has run on
  the repository store and is recorded in the README's acceptance table.
- The suite is composed from families under a fault profile (README, *The
  world*): `genesis` (6), `conventions` (10), `mbpp` (257), `tables` (100),
  `api` (100). `experiments/world.toml` samples twelve of each and faults
  the first two HTTP calls. Its arms and their curves are in the README
  (*The world on gpt-oss-120b*); the arm stores are under `runs/world/` on
  this machine.
- The role contracts on `openai/gpt-oss-120b`: every request — classify,
  guard, lens, dispose, propose, coding, nominate, attack, verdict, credit,
  currency — has been read back through `hgi roles try` and parses; every
  role prompt is priced for it. The drafting requests answer with a sketch
  (decision 21); the reply logs of the tries are ephemeral (scratch), the
  world run's log is not kept either — `HGI_REPLY_LOG` recreates one.
- `experiments/baseline.toml` (the six genesis tasks, one 502) is saturated
  for gpt-oss-120b: 1.00 on every pass of both arms. Its three
  consolidations wrote one file, K-0001, three times (the id-minting bug,
  fixed in this build); the after-pass-2 and after-pass-4 records survive
  only in that arm repository's history.
- `experiments/model-sweep.toml` and `cadence.toml` are written and have
  not been run; `probe.toml` ran three passes and was stopped once its
  reply log had been read.
- Weave: traces, evaluations, attributes, feedback → steer, and the mirror
  are verified live in `slavazinevich-worldvue/hgi-dev` and used in
  `slavazinevich-worldvue/hgi` and `hgi-experiments`.

## Leftover work for the full implementation

1. **The belief store** (spec § 4.2, § 6, § 8.5). Records, the per-pass
   prediction at close (step 5), the reference at entry, settlement through
   dispositive fires, the status projection at boot (step 6), the
   calibration table, lens L-0005. The watch evaluator and fire emission in
   `hgi/evaluate.py` already run over any record kind that exposes revisit
   latches, so beliefs plug into `index.triggers` and `emit_fires` as-is.
2. **The rule store** (§ 6.4, § 10.10). Rule records with the hand-authored
   adoption register, enrollment on observed non-propagation, the rule index
   that leads with the residue, demotion on applied ÷ considered, coverage
   migration, and the ladder rungs `adoption-row` and `rule-enrollment` as
   executed operators. `registry/ports.json` needs the rule declarations.
3. **The world, next.** The families that are here grade breadth; the ones
   that would grade *transfer* are not: a second family with the same
   conventions in different clothes (the paging and the `/v2` move on a
   different API, the no-trailing-newline files under different names), so
   a record admitted on one family is scored on another. `nestful`
   (multi-step tool composition with a scalar gold) and a shell family from
   `InterCode-Corrections` were surveyed and not transcribed. The
   `tables`/`api` tolerance (1% relative) is lenient on large totals. MBPP
   and TableBench are in every model's pretraining; absolute scores are
   inflated, the arm-against-arm comparison is not.
4. **The lenses on the real model.** L-0002 (the boot lens for unreached
   records) answers "no hook reached" for every task on an empty store;
   L-0003 (what the pass made false) names tasks and call URIs where it
   must name a record id, so nothing files from it. Both are walked once
   per pass and cost a call each; neither has a consumer yet that would
   miss them. The lens battery (§ 9.2, slice 6a) would score exactly this.
5. **TypeSafe System1.** `hgi/coder.py` assumes an OpenAI-compatible surface
   behind `TYPESAFE_BASE_URL`; the real API shape is unverified (waitlist as
   of 2026-09-12). The role is the invariant; only the adapter changes.
6. **ARIA.** Interactive only. `hgi mirror` publishes the datasets it needs;
   the brief it drafts is recorded by URI with `hgi consolidate
   --analyst-report`. A programmatic surface would replace `build_brief`'s
   local derivation with the analyst's report as the primary input.
7. **Split and fold** (§ 10.6) as executed operators; today `lineage.split_from`
   and `folded_from` exist on the envelope and nothing writes them.
8. **Genesis anchoring.** All seven articles are past the three-consolidation
   deadline without an anchor (the lint warns). The consolidator needs a
   nomination that anchors an article to an instance, or evicts it.
9. **The `defer` verdict** is accepted by the vocabulary but nothing turns its
   condition into a latch; the draft simply stays in `store/proposals/` and,
   being the backward pass's, is exempt from the proposal expiry.
10. **Wiring latches** are written on supersedure but nothing consumes them:
    propagation (`re-derive` / `check` on a neighbour's status change) is not
    run at consolidation.
11. **Structural-zero audit and escape recurrence** are projected but not
    nominated on; vocabulary growth by the route-before-mint ladder is
    `Registry.add_term` with no caller. The real model classifies every
    pass with the escape `other(task)`, which is exactly the recurrence the
    audit would read.
12. **`admission.commit`** is not stored (see decision 4 below); `hgi lineage`
    does not yet read the admitting commit from git history.
13. **Model-pricing** warns only; nothing re-prices.
14. **The watch a model sketches** is sometimes a watch on success
    (`task_pass_rate == 1.0`, seen in a nominate try): the revisit latch
    then fires when the record works. Nothing checks a watch's direction
    against the decision's stakes; the examiner could, and does not yet.
15. **Executing model-written code.** `mbpp` tasks run `python3 tests.py`
    over a file the model wrote, on this machine, with a timeout and
    nothing else; the shell tool already ran model commands the same way.
    A sandbox is a tool-layer concern, not the suite's.

## Decisions taken, and their risk

1. **Decision-only roster.** Beliefs and rules were dropped by instruction;
   the store, ports, bars, lint and projections are written so that adding a
   kind is a new model in `hgi/types.py`, a row in `LAYOUTS`, a port
   declaration and a projection. *Right if* the kinds really are coordinates
   of one contract (the spec's claim). *Wrong if* rule routing and the
   adoption register need read paths the decision path does not anticipate —
   the boot's stage one only knows the hook-major index over decisions.
2. **All vocabularies live in `registry/vocabulary.json`; types validate
   against the registry in scope** (`Term(vocab)` with a context variable)
   rather than as Python `Literal`s. *Right:* one source, growth without a
   code change, `other(<what>)` everywhere. *Risk:* no static typing of enum
   values; a test that forgets to put a registry in scope validates against
   `./store`.
3. **Observations and fires are file-per-record, not JSON Lines**, because
   each receives one in-place flip (promotion pointer, fire disposition). The
   spec calls both ledgers. *Right:* same-commit settlement without rewriting
   a ledger. *Risk:* a reader expecting `observations.jsonl`.
4. **`admission.commit` is derived, not stored.** A commit cannot contain its
   own hash; the commit message names the ids it admitted, so the anchor is
   `git log --grep`. *Risk:* the spec puts the field on the envelope; a
   consumer expecting it there finds nothing.
5. **Facts are mirrored on the session record** (`evaluation.scores` and
   `evaluation.rows`) with the Weave run URI as `source`, and the watch
   evaluator reads them from the session ledger, not from Weave. Each row
   also carries its own scores, so the close can see which task the hidden
   test failed. *Right:* offline runs, reproducible tests, one read path.
   *Risk:* the spec keeps facts in the oracle; a fact edited on a session
   file is not the oracle's.
6. **The session record is written at boot and completed at close** (one
   file, `closed_at` null in between). The spec's ledger is append-only.
   *Risk:* a crashed pass leaves an open session; `hgi boot` refuses a
   duplicate id but nothing closes an orphan.
7. **The hypothesis-ledger entry is appended once, with the verdict**, after
   the adjudicator returns; the examiner's attack payload lives inside the
   entry with its own `verdict: "pending"` field that the schema fixes as a
   `Literal`. *Right:* the ledger is never edited, and the lint can prove
   verdict authority on it. *Risk:* an attack with no adjudication is never
   written anywhere.
8. **Credit assignment is task-level**, not series-level: a record's applied
   tasks' pass fraction before and after, and only a record whose fraction
   did not improve reaches the adjudicator, which names the slot. *Right:*
   two records applied in the same passes are not confounded; the model no
   longer writes a steer for every applied record. *Risk:* `before` is the
   same tasks' earliest history, which conflates "the record didn't help"
   with "the tasks were always hard".
9. **The retirement in the demo is a supersedure**, nominated by the credit
   table and the retry observations, not a status flip to `moot` by the
   ratio. The ratio-driven leg exists and is tested (`tests/test_retirement.py`)
   but did not trigger in six passes. The README says so.
10. **The stub decides verdicts by rules that can only decline on evidence
    the examiner reads** (fault rate, independence, a task id in the
    payload) and escalates only on an unevaluable watch series. *Right:* no
    verdict without evidence. *Risk:* the stub adjudicator admits almost
    everything the consolidator nominates, so the demo's ledger has no
    decline; the decline and escalate paths are proven by tests only.
11. **Watch predicates on the demo's decisions never fired**: the cause
    decision watches `error_cause_present < 0.5`, which its own application
    raises. A watch on `task_pass_rate` would have fired at pass 4 and made
    the steer a redundant catch instead of a store miss. The choice kept the
    steer cell populated; it also left the fire ledger empty in the demo.
12. **Trace attributes are a nested `hgi` object** (`attributes.hgi.session`),
    not dotted keys, because Weave's query language resolves nested fields
    and not keys containing dots. The UI renders both the same.
13. **The consolidation window shrinks nothing**: bars stay at six passes;
    with six passes the retirement leg cannot trigger. The drop-order rule
    (6) was not applied because the supersedure satisfied the row.
14. **The Evaluation summary is overridden to scorers only**
    (`hgi.evaluate.Evaluation.summarize`), because Weave's auto-summary
    tries to average the heterogeneous task outputs and raises; the same
    override keeps each row's scores aside for the session. *Risk:* the
    Weave UI's evaluation comparison shows no model-output block.
15. **Experiment arms run in a git repository each, under `runs/`, which
    the code repository ignores.** *Right:* the write law holds per arm
    (every write ends in a commit), arms cannot clobber each other or the
    demonstration's `store/`, and the code history stays the code's.
    *Risk:* an arm's result is not in the code repository's history; the
    README table is copied from `hgi experiment report` by hand, and a
    reader of the code repository cannot regenerate it.
16. **A round is a consolidation cycle; the cadence is written into the
    arm's bars at seed.** `rounds × passes_per_round` is the run's length
    and `consolidation_every_passes` is the round size, so the file states
    the cadence once. *Risk:* the brief reads only the sessions since the
    last consolidation, so a round size of one may never meet the
    two-distinct-sessions bar — `cadence.toml` measures this rather than
    fixing it.
17. **W&B Inference is the endpoint the shipped experiment files use**, not
    a CoreWeave endpoint, because a key for it exists on this machine and
    none did for CoreWeave; the role is the invariant and a CoreWeave model
    is one more `[models.*]` entry with its own `base_url`. *Risk:* the
    sponsor binding in the README now names both.
18. **Backends are installed per role in the process** (`hgi.model.use(b,
    role=…)`), so one arm can act on one model and adjudicate on another.
    *Risk:* the session record carries one `model_id` (the pass's); the
    per-role ids are on the ledger entries' role calls and on `arm.json`.
19. **The reply shape travels with the request, not in the prompt**
    (`hgi.roles.REPLIES`, `roles.request`). *Right:* one table, the stub
    and the model read the same contract, and a shape change is one edit.
    *Risk:* the model echoes what it is shown — a placeholder inside a list
    came back as a literal element, and a `reply` key came back as a
    wrapper; both are read defensively, and the test on `REPLIES` forbids a
    string beside an object in any list.
20. **Each role receives only the record shapes it reads** (`roles.schemas(role)`):
    the drafting roles the Sketch, the judging roles the Draft and the
    ledger entry, the coder none. *Right:* a third of the tokens per call,
    and no schema a role cannot act on. *Risk:* the vocabularies are still
    validated at runtime only — the schema says `string`.
21. **Drafting roles return a sketch; the code derives the record**
    (`hgi/drafting.py`). The model judges the five slots — payload,
    overshoot, cue and exclusions, premises as falsifiers, watch, residue,
    moot condition — and `drafting.body` builds the latches, the owed acts,
    the retirement guard from the bars. *Right:* on gpt-oss-120b the full
    body came back as placeholders in every try and the sketch parses and
    clears the floor in every try since; the stub answers in the same
    shape. *Risk:* the ladder's other rungs (`counterfactual-edit`,
    `hook-edit`) still have no operator, so a sketch is always a new
    decision whatever rung it names; and a sketch cannot express a latch
    the derivation does not know (a wiring latch, a second consultation
    hook).
22. **Ids are minted against the counters on disk**, re-read before every
    reservation. *Right:* a long-running runner and the commands it drives
    hold separate registry objects; the baseline arm's three consolidations
    overwrote one file before this. *Risk:* one file read per mint; a
    process that edits `ids.json` by hand between mints is obeyed.
23. **The suite is an object in scope**, like the registry: `suite.current()`
    is what the experiment installed or what `$HGI_SUITE` names, and every
    module that read `suite.tasks.TASKS` reads it. Faults are keyed on the
    task's name within its family, so a family keeps its faults when
    composed with others. *Risk:* a test that forgets to install a suite
    runs the genesis family silently; the session records only the hash,
    not the spec — `arm.json` records the spec, a hand-run's `.env` does.
24. **The close lens that touches the artifact is walked once per failed
    row.** *Right:* over sixteen rows in one context the model filed
    nothing for two failed tasks; per row it files one anchored observation
    each. *Risk:* one call per failure — a pass that fails thirty tasks
    makes thirty lens calls — and a failure that was the model's own
    arithmetic still files, so the coder's grouping has more noise to
    separate.
25. **A pass proposal reaches the consolidator through the brief and is
    adopted by uid or expires** (`proposal_ttl_consolidations`, 2). *Right:*
    the pass proposes, the backward pass admits, and the pass's draft keeps
    its provenance on the admitted record. *Risk:* on the real model the
    pass proposes the same retry decision every pass with thin evidence;
    the consolidator has not been seen to adopt one yet.
26. **The adjudicator's reply carries a rationale**, recorded on the ledger
    entry, and a token outside the vocabulary escalates. *Right:* the
    first verdict on the real model admitted over a landed premise kill
    with no trace of why; now the weighing is on the ledger. *Risk:* the
    rationale is prose the lint cannot read.
27. **A regression is nominated mechanically before credit runs** (decision
    8): the adjudicator sees only rows whose applied tasks did not improve.
    *Risk:* a record whose tasks improved for another reason earns no steer
    even when it was wrong — the oracle's floor, disclosed.

## Housekeeping

- `smoke_test.py` is the original W&B/Weave connectivity check and is not
  part of the package.
- The store's genesis articles and lenses are priced for `stub`; reseed with
  `HGI_MODEL_ID=<model> uv run hgi genesis --force` before a hand-run on a
  real model (this resets the store). An experiment arm seeds its own store
  and needs no reseed. The demonstration store's L-0004 product text
  predates the per-row walk; an arm seeded now carries the current text.
- `runs/smoke/`, `runs/baseline/`, `runs/baseline-precontract/`,
  `runs/probe/` and `runs/world/` on this machine are the 2026-09-12 runs;
  they are ignored by git. The baseline-precontract arms are the only
  record of the pre-contract run.
