# Carry-forward

State of the build as of 2026-09-13, after the world run, the stream run, the review
pass, the instruments pass (the true-miss floor, the precision slot, the
second retirement key, anchor resolution, the late steer sweep, the antichain
flag and the seeded controls) and the stream pass (lessons, the curriculum,
the stream runner and the evolution log), with the work left for the full
implementation and the decisions taken along the way — each with why it may
be right and why it may not.

## Where it stands

- Slices 0–3 of spec § 13 ship with their acceptance tests green
  (`uv run pytest`, 263 tests). Slice 4 ships the dashboard, the analyst
  mirror and the retirement leg; the rule tier and the grown floor do not
  exist because the roster is decisions only. Slice 6(e) — split and fold
  as executed operators — ships, with the other backward-pass legs that
  were nominators without a consumer: deferral latches, propagation over
  wiring latches, the structural-zero audit and the edit rungs, genesis
  anchoring, and vocabulary growth (README, *The backward pass*). Slice 5 (the demo) has run on
  the repository store and is recorded in the README's acceptance table.
- The suite is composed from families under a fault profile (README, *The
  world*): `genesis` (6), `conventions` (10), `mbpp` (257), `tables` (100),
  `api` (100), `transfer` (6, the `conventions` conventions re-dressed in
  different clothes; `experiments/transfer.toml`). `experiments/world.toml` samples twelve of each and faults
  the first two HTTP calls. Its `120b-attached` arm ran to completion
  (README, *The world on gpt-oss-120b*): 0.81 0.73 0.75 0.90 0.83 0.83,
  six decisions admitted over three consolidations — one by adopting the
  pass's own proposal — three retired moot, four fires discharged, 31 of 60
  observations still open. The detached arm was stopped in its first pass;
  pass 1 of the attached arm is the no-store draw. The arm store is under
  `runs/world/120b-attached/` on this machine. The `20b-attached` and
  `split-roles` arms have not run.
- The role contracts on `openai/gpt-oss-120b`: every request — classify,
  guard, lens, dispose, propose, coding, nominate, attack, verdict, credit,
  currency — has been read back through `hgi roles try` and parses; every
  role prompt is priced for it. The drafting requests answer with a sketch
  (decision 21); the reply logs of the tries are ephemeral (scratch), the
  world run's log is not kept either — `HGI_REPLY_LOG` recreates one.
- The review pass (doctrine v2, §§ 1–9, 13, 14, 16 read against this
  roster) landed as decisions 42–52 below: the noise filter, the examiner
  fan, role separation on every species, consumers for the pending
  contradictions and the recall probes, the lens lifecycle, attacker
  precision, revision routing, the port miss stream, and the small floors.
  The new requests — `triage`, `ports`, the `lens`-bearing `attack` and
  `currency` — have been read back on the stub only; their reply shapes
  are not yet priced for `openai/gpt-oss-120b` (see item 18).
- The instruments pass landed as decisions 53–59 below: the matrix's
  true-miss cell counts rows, the precision slot signature is live, a record
  never considered across a full window reaches the adjudicator, a
  counterfactual's anchor must resolve, a late note is swept at the next
  close, the antichain is flagged on the plan, and the examiner fan and the
  blind coder have seeded-positive controls. Every one is proven on the stub;
  none has been run on `store/` or read back on a real model (items 8, 18,
  23, 24).
- `experiments/baseline.toml` (the six genesis tasks, one 502) is saturated
  for gpt-oss-120b: 1.00 on every pass of both arms. Its three
  consolidations wrote one file, K-0001, three times (the id-minting bug,
  fixed in this build); the after-pass-2 and after-pass-4 records survive
  only in that arm repository's history.
- `experiments/model-sweep.toml` and `cadence.toml` are written and have
  not been run; `probe.toml` ran three passes and was stopped once its
  reply log had been read.
- The stream pass (decisions 60–65 below): `suite/lessons.py` names the
  seven lessons with their tiers and derives the naive outcome and the
  symptom; `suite/families/curriculum.py` generates 84 tasks; `suite/stream.py`
  deals a pool into batches; `hgi experiment` runs a `[stream]` arm (a new
  batch every pass, revisit passes, detached draws on their own batches)
  and `hgi/evolution.py` derives the log. `tests/test_stream.py` proves
  every clothing fails naively and passes when known within budget, the
  deal, the symptom rules and the stub smoke (351 tests green).
  `experiments/stream.toml` has run (item 25; README, *The stream on
  gpt-oss-120b*; `experiments/results/stream/`): the plain pool did not
  separate the arms, the strict pool did on one lesson and lost it on the
  rows the record overshot onto; `stream-probe.toml` was the endpoint check
  that preceded it.
- Weave: traces, evaluations, attributes, feedback → steer, and the mirror
  are verified live in `slavazinevich-worldvue/hgi-dev` and used in
  `slavazinevich-worldvue/hgi` and `hgi-experiments`.

## Leftover work for the full implementation

1. **The belief store** (spec § 4.2, § 6, § 8.5). Records, the per-pass
   prediction at close (step 5), the reference at entry, settlement through
   dispositive fires, the status projection at boot (step 6), the
   calibration table, the belief-watch lens (spec Appendix A.3's L-0009;
   L-0005 to L-0008 are the examiner fan). The watch evaluator and fire emission in
   `hgi/evaluate.py` already run over any record kind that exposes revisit
   latches, so beliefs plug into `index.triggers` and `emit_fires` as-is.
2. **The rule store** (§ 6.4, § 10.10). Rule records with the hand-authored
   adoption register, enrollment on observed non-propagation, the rule index
   that leads with the residue, demotion on applied ÷ considered, coverage
   migration, and the ladder rungs `adoption-row` and `rule-enrollment` as
   executed operators. `registry/ports.json` needs the rule declarations.
3. **The world, next.** The transfer half now ships: `suite/families/transfer.py`
   re-dresses three of the `conventions` conventions in different clothes —
   the no-trailing-newline files under new names (`part-*.tsv`, `chunk_*.dat`),
   the paging API on a different surface (`/records`, `/accounts`), the `/v2`
   move on different endpoints (`/account/42`, `/health`) — reusing
   `conventions`' `_no_newline` and `_naive_count` so the convention is shared
   and only the clothes differ. `experiments/transfer.toml` composes it beside
   `genesis`, `conventions` and `api` under the world's two-call fault profile,
   so a record admitted while scoring a convention on its source family is
   scored again on the same convention re-dressed. `tests/test_transfer.py`
   proves each convention fails naively and passes when known, that the
   transfer tasks' work-shape terms are a subset of `conventions`' while their
   file names and API paths are disjoint from it, and that the paged and moved
   routes behave. What the transfer half still leaves undone: the CSV-quoted-comma
   and byte-order-mark conventions are **not** yet re-dressed (only the three
   named ones are), and the transfer is proven structurally offline — no
   real-model arm has run to show the attached curve holding on `transfer`
   where a path-memorising record would break. What grades breadth-not-transfer
   remains: `nestful` (multi-step tool composition with a scalar gold) and a
   shell family from `InterCode-Corrections` were surveyed and, per the item,
   deliberately not transcribed. The `tables`/`api` tolerance (1% relative) is
   lenient on large totals, and `transfer`'s paged answers are exact integers
   so that caveat does not touch it. MBPP and TableBench are in every model's
   pretraining; absolute scores are inflated, the arm-against-arm comparison is
   not.
4. **The lenses on the real model.** L-0002 (the boot lens for unreached
   records) answers "no hook reached" for every task on an empty store;
   L-0003 (what the pass made false) names tasks and call URIs where it
   must name a record id, so nothing files from it. Both now have consumers
   (decisions 45 and 46): L-0002's probes are the brief's `recall` rows and
   nominate a hook-edit, L-0003's pending entries reach the adjudicator at
   the next consolidation. What is still unverified is the *content* on a
   real model — whether a probe names the right record, whether a
   contradiction names a premise — and the lens review will retire either
   lens through the genesis-deadline door if nothing it produces is ever
   consumed, which on the world run's pattern (nothing filed from L-0003)
   is the likely outcome for L-0003.
5. **TypeSafe System1.** `hgi/coder.py` assumes an OpenAI-compatible surface
   behind `TYPESAFE_BASE_URL`; the real API shape is unverified (waitlist as
   of 2026-09-12). The role is the invariant; only the adapter changes.
6. **ARIA.** The programmatic surface is now wired: `hgi consolidate
   --analyst-report <uri>` resolves the URI through `hgi.mirror.read_report`
   and the backward pass reads the report as the consolidation brief's
   primary input (`consolidate.consolidation_brief` → `analyst_brief`),
   replacing `build_brief`'s local derivation of the nominator's rows; the
   analyst's coding is stamped onto the open observations exactly where the
   local grouping would write it. A URI that resolves to no machine-readable
   report — an interactive chat report recorded only as provenance, or a
   Weave ref that cannot be fetched — falls back to the local derivation, so
   the interactive path is unchanged and the URI is still recorded. What is
   *not* here: nothing yet **produces** an ARIA report programmatically —
   `read_report` reads a Weave ref or a JSON file (a hand-exported or offline
   report), and no code publishes the brief as a fetchable object, so a live
   run still drafts the report interactively and records its URI. The report
   is trusted whole: a field it omits is empty, not re-derived per-field, and
   the score facts, accepted bodies, proposals and owed fires stay the
   store's (the analyst never authors a record or a fact). `read_report`'s
   Weave branch is offline-untested (guarded by try/except); the file and
   None branches are covered in `tests/test_analyst.py`.
7. **Split and fold nominations on a real model.** The operators execute
   (`tests/test_lineage_ops.py`); the stub's leaves share the parent's payload
   with the hook narrowed per sub-shape, which is a hook-edit wearing a
   split's lineage. A real consolidator drafts distinct leaf payloads; the
   `nominate` request carries the whole body of every record `fusion` or
   `convergence` names, and neither row has yet appeared on a real-model
   arm.
8. ~~**The lens battery** (§ 9.2, slice 6a): decoy rejection scored in Weave;
   `LensTelemetry` fields are all `design-stage`.~~
   *Mechanism done (this build); the live Weave scoring is a run.*
   `hgi/lens_battery.py` plants two decoys and two genuine signals per close
   lens (L-0003, L-0004) and scores decoy rejection as a traced
   `weave.Evaluation` (`hgi lens-battery`); `telemetry_from` computes
   `decoy_rejection` and `answer_variance` and `populate_telemetry` writes
   them onto `registry/lenses.json`, off `design-stage`
   (`tests/test_lens_battery.py`). The seeded-positive controls ship beside it
   (decision 59): the examiner control scores each examiner lens's landing on
   a planted fault of its class and its non-landing on a plausible draft, onto
   the same register; the coder control scores the blind coder's term on a
   known shape and its escape on a misfit, to `index/controls.json`. Left for
   a run: with `HGI_WEAVE_PROJECT` and the real model as the backend, confirm
   the `lens-battery-v1/*` scorer series appear in Weave with a non-null run
   URI for all three evaluations, and commit the demonstration store's
   real-model telemetry — the committed `store/registry/lenses.json` is
   deliberately left at `design-stage` and no `controls.json` is committed,
   because on the stub every control passes by the stub's own keyword rules
   (verified end to end on a scratch copy of `store/`: 1.00 on every axis).
9. **The demonstration store's seven articles are still unanchored.** The
   anchoring review exists and runs at every consolidation, and the stub
   anchors all seven from the demo's own ledgers (`tests/test_genesis.py`),
   but `store/` has not been consolidated since the review shipped: a
   `hgi consolidate --force` on it with no `HGI_WEAVE_PROJECT` would leave
   untraced ledger entries beside the traced demonstration's, so the next
   consolidation is left to a traced run. Until then the lint's seven
   `genesis-anchor` warnings stand.
10. **Genesis term retirement.** Appendix A.2 retires a work-shape term
    unused across three consolidation passes; nothing does. A retired term
    still parses on the records that carry it, so retirement is a register
    mark (`retired: <date>`) the hook index skips, not a removal.
11. **Propagation's `re-derive` act** has no derived field to recompute in
    a decisions-only roster; every wiring latch is written with `check`.
    The rule tier's adoption cells and a belief's evidence state are the
    fields `re-derive` is for.
12. ~~**Escape recurrence counts only the sessions' work-shape escapes.**~~
    *Done (this build).* `reviews.escape_events` reads an `other(<what>)`
    wherever its closed vocabulary is kept — a work-shape on the pass, a
    key-space on the latch, a `<species>-verdict` on the ledger entry — and
    `escape_clusters` counts those occasions the same way it counted
    sessions. `reviews.vocabulary` runs for every reviewable vocabulary by
    default (decision 40; `tests/test_escape_vocabularies.py`). Left: the
    verdict source reads a species-verdict off the ledger entry but not an
    `adjudicator-verdict` escape off a decision's admission (none is written
    today); a latch-key-space cluster keys on `record#index`, its occasion,
    not on the record's admitting session.
13. **The pass's own proposals** (close step 6) parse and file, and a
    consolidation adopts one whose lesson a ratified group earns; the stub
    adopts (`tests/test_proposals.py`), and the real model may draft its own.
14. **Re-authoring on a re-price — mechanized; the text's quality is
    unverified.** The `reauthor` role and `hgi price --reauthor` ship: the
    role rewrites each conditioning field (a lens's angle, an article, a
    decision's sentence, each with its counterfactual) against the new model,
    and the path stamps the text and the authoring together (`authored_for`
    null), so `model-pricing` clears because the text followed the model —
    where `--restamp` (stamp-only, warning stands) is unchanged. The
    mechanism is proven offline against the stub (`tests/test_price.py`): a
    re-author moves every field, agrees the stamp, and quiets the floor; a
    restamp leaves the warning a later re-author clears. What only a real
    model can verify is the *content*: the stub marks the conditioning it
    stands in for (`[for <model>] …`) rather than rewriting for the model,
    so whether a re-authored angle or article actually conditions the new
    model better than the old text is the same unverified drafting contract
    as item 4 (the lenses on the real model) and needs a live run to read
    back through `HGI_REPLY_LOG`. `--reauthor` has not been run on `store/`;
    the Housekeeping note's `--restamp`-or-`genesis --force` choice now has a
    third option that keeps the store and moves the text.
15. ~~**`hgi experiment`'s genesis message names no article ids** (`Genesis for
    <exp>/<arm>: priced for …`), so `hgi lineage C-0003` finds no admitting
    commit in an arm's store.~~ *Done (this build).* The arm's genesis commit
    subject now appends the constitution range (`, constitution
    C-0001..C-0007`, endpoints derived from `store.articles()`, decision 28),
    so `hgi lineage <C-id>` resolves an admitting commit inside an arm's store
    as it does in the demonstration store (`hgi/experiment.py._genesis_message`;
    `tests/test_experiment.py`).
16. ~~**The watch a model sketches** is sometimes a watch on success.~~
    *Done (this build).* `drafting.fires_on_success` reads a revisit watch's
    direction against the oracle's convention (a higher-is-better score in
    `[0, 1]`, `1.0` ideal): a predicate the ideal satisfies but a failing
    score does not fires when the record works. The examiner lands a
    `warrant:watch-direction` claim on such a watch and the adjudicator
    declines it (decision 41; the examiner and adjudicator prompts carry the
    same check; `tests/test_watch_direction.py`).
17. **Executing model-written code.** `mbpp` tasks run `python3 tests.py`
    over a file the model wrote, on this machine, with a timeout and
    nothing else; the shell tool already ran model commands the same way.
    A sandbox is a tool-layer concern, not the suite's.

18. **The new role requests are unpriced for the real model.** `triage`
    (the noise filter), `ports` (the port miss stream), the `lens`-bearing
    `attack` (one angle per call), the `lens`-, `finding`- and
    `domain_entered`-bearing `currency` requests, the `precision` row on
    `nominate` and the `co_applying` content on `dispose` parse on the stub
    and have not been read back through `hgi roles try` on
    `openai/gpt-oss-120b`; `role-pricing` will not warn,
    because the prompt files still list the model. A live run's first
    consolidation now costs four examiner calls per draft instead of one,
    plus one triage call per group at the bar.
19. **The `article` rung has no operator.** The ladder's top rung — a
    constitution article with a forced eviction — is carried as a decision
    like the rule rungs (decision 42), so a lesson meant for every pass is
    only consulted on a matching hook. The constitution is in this roster,
    so the operator is in scope: a nomination carrying the article, its counterfactual and
    the article it evicts, through attack and verdict, written with the
    eviction in one commit under the cap. It needs a draft kind beside the
    decision draft, which the queue and the committer currently assume.
20. **No collision species writer.** The species is declared with its
    verdict vocabulary and nothing writes it; the doctrine's canonical
    instance — a test author deriving expectations blind from committed
    artifacts — has no analogue in the loop yet. The blind coder is coded as
    `coding`, which is its own species.
21. ~~**The antichain is displayed as a list, not as a conflict.**~~ *Done
    (this build; decision 58).* `boot.co_applying` reads the consulted records
    whose hooks share every term with no lineage edge between them; the plan
    prints them on one `co-applying:` line and the dispose request carries the
    same reading. Still left: the leaf lattice that would give them regions is
    a split nomination only, and a real pass's disposition notes have not been
    read to see whether they say which applied where.
22. **Yield per steer is not instrumented.** The matrix counts steers and
    the credit table attributes them; nothing reads how much each steer
    moved — the quantity the doctrine says to maximize, against steer count,
    which it says never to target.
23. **The precision slot on a real model is unverified.** The stub's
    disposition note names the pass's tasks after a fixed marker and the
    stub consolidator reads them back as `not_this` entries; a real pass's
    note is prose ("which rows it bore on, or why it did not") and a real
    consolidator must turn it into a presentation exclusion — the prompt says
    so, no reply has been read. And the stub's guard matches `not_this` by
    substring over the prompts, so a task-name exclusion excludes nothing at
    the stub's guard: on the stub the successor is proven admitted, not
    proven quieter.
24. **The true-miss join reads the row's call, or the task name in the
    noticing when the row carries none.** A pass whose lens files an
    observation anchored on a path alone and naming no task hides its failed
    row from the cell — the count stays a floor, but one that a lens's
    anchoring habit can lower. The late steer sweep re-reads every earlier
    closed session's calls at every close: one trace-store query per earlier
    session per close, which on a long run is a cost the channel's
    best-effort clause hides rather than prices.
25. **The stream run.** `experiments/stream.toml` ran on 2026-09-13 (README,
    *The stream on gpt-oss-120b*; `experiments/results/stream/`): every arm,
    from the tree at 67c9ff0 with the close fix 1707b72, the detached arms
    redrawn alone afterwards, the strict attached arm rerun from scratch
    after the close bug stopped its first run at pass 7. What it answered:
    ten batches do give a lesson enough same-shaped observations to group —
    the coder shaped the moved-v2 and token-route observations alike in
    every 120b arm and the groups reached the bar from the first
    consolidation — and the drafts then died at the contract's floors and
    the examiner's attacks in the plain arm (11 refused at parse, 5
    declined, 1 admitted, a record that names no lesson) while the strict
    arm admitted the fused `/v2`-plus-token record at its first
    consolidation and five more after. The strict pool separated the arms
    on one lesson (moved-v2: 0.58 attached, 0.00 detached, the naive shape
    3/3 before the record and 0/9 after) and lost the gain on the rows the
    record overshot onto (paged-api 0.08 against 0.75; token-route blocked
    to zero calls by D-0002), for a tie over the stream. The plain pool did
    not separate (0.46 against 0.54) and its no-store passes differ from the
    detached draws of the same batches by up to 0.37, the noise floor of
    eight tasks on this endpoint. The probe's concern — observations naming
    the task and the number but not the convention — did not recur: the
    stream's closes named the route and the `/v2` fix. What did not happen:
    footer-row and trailing-newline earned no record on any arm, and the
    one record drafted from the newline observations fired on file rows
    and left them failing the naive way. The first strict run and its
    rerun met the same batches with the same model at temperature 0 and
    consolidated differently (the first refused both lesson drafts at
    parse after pass 2 and declined the versioning draft after pass 4; the
    rerun admitted the fused record after pass 2): admission is a draw, and
    the first run's store is gone (`--force` discards it) — its two
    consolidations survive only in this note. The evidence for the
    reject-vs-amend and admission-slack changes is item 32 and the task
    spun from it.
26. **Retention and forgetting beyond one revisit.** `revisit` re-meets
    whole batches after the stream; the modes a continual-agent benchmark
    scores (AgentMemoryBench: improvement, retention, forgetting,
    generalization, conflict) would take a revisit at fixed checkpoints
    during the stream and a held-out probe set met with the store and never
    closed on — the `evaluate --detached` path has no store, and no probe
    mode (boot + evaluate, no close) exists yet.
27. **A mixed stream.** The stream's pool can name any families
    (`families = ["curriculum", "tables"]`; a task with no lesson is dealt
    under its family), but no shipped experiment mixes lesson tasks with
    distractors, so the loop's grouping has not been tried where most
    failures carry no lesson.
28. **The mention heuristic.** `evolution` marks a record as mentioning a
    lesson by keywords over its decision, latch and context; a record that
    teaches a lesson in other words is missed and a record that names the
    words without teaching it is counted. The join that would replace it —
    the applied dispositions of the record on rows of that lesson — is in
    the store (`rows[].applied`, keyed to the task) and not yet read by the
    log.
30. **The economy run.** `experiments/economy.toml` — 120b attached and
    detached on the plain pool under a different deal (seed 2) — is the
    stream graded on quality (`solution_economy`, `turn_economy`,
    `method_transfer`); it had not run when this was written, and no real
    model has yet scored the three series (the stub's smoke scores them
    zero and unevaluable on its failed rows). The two runs are additive:
    the stream run's evolution log already shows `economy`, derived from
    the counts, and only `turns` and `transfer` need the new envelope.
    It has since run on `openai/gpt-oss-120b` (2026-09-13, brought over
    from `claude/nervous-rubin-e8e759`; `experiments/results/economy/`):
    pass rate did not separate (38/80 attached against 42/80 detached) and
    quality could not have, because no record was in context on any
    first-sight pass — D-0001 sat behind a guard the boot failed and went
    moot, D-0002's consultation latch was scoped to a work-shape term
    (`test-failure-triage`) so the boot index matched it to nothing,
    D-0003 landed after pass 10 and failed both moved-v2 rows it was
    applied to. The run's own findings — the retrieval miss, the close
    naming scores not world-facts, the parse refusals and the malformed
    tool call — are items 39–42 below and are the evidence for gap fixes
    beyond the admittance bar.
31. **Quality beyond the shell lessons.** `method_transfer` replays a
    shell command, so it grades the three shell lessons only; the API
    lessons' method is the walk and transfers trivially, and `bom` has no
    budget so no economy floor. A hidden-assert variant of `mbpp` (one
    assert shown, two held out) with a lint or complexity column would be
    the lesson-free family with a graded quality metric, for a mixed
    stream; not built.
38. **The review's reject-vs-amend change is proven on the stub only.**
    Decisions 73–75 — independence and watch direction read by the code,
    a landed abstraction claim amended through one promote re-ask, a
    decline standing only on an upheld premise kill — are proven by the
    stub's paths and the tests (`tests/test_mechanical_review.py`,
    `tests/test_abstraction_amend.py`, `tests/test_decline_override.py`)
    and by no real-model run. The evidence they answer is the stream run's
    ledgers (`runs/stream/*/store/ledger/ledger.jsonl`, 2026-09-13): three
    lesson drafts on gpt-oss-120b — endpoint versioning, the moved-v2
    route, after passes 2 and 6 of the attached arm and in the strict arm —
    were declined on abstraction and watch direction alone and dropped.
    The test of whether the run now admits the moved-v2 record is a rerun
    of `experiments/stream.toml` arm `120b-attached`; not run.
29. **Public continual-learning suites.** SWE-Bench-CL, AgentMemoryBench,
    AgentCL and the procedural-memory-retrieval benchmark were surveyed
    (2026-09-13) as the scale-up path for the stream shape — repository
    feature work with recurring conventions — and not transcribed: each
    needs a repository-scale agent and a run measured in hours, where the
    curriculum measures the mechanism in minutes. The curriculum's lessons
    are the conventions of a small world; the claim that the shape carries
    to a codebase's conventions is untested.

32. **Admission slack — notes for easing the floors that refused every
    lesson draft of the stream run.** The stream run (item 25) filed an
    observation on every failed row, the blind coder shaped same-lesson
    observations alike and groups reached the two-session bar, and the
    consolidator nominated the right lessons (endpoint versioning, auth,
    budget, csv-header); then every gpt-oss-120b draft died before or at
    adjudication and nothing was admitted. Four gates did it, in order of
    cost, each with the slack proposed and what it risks:
    - **`not_this` must be non-empty** (`hgi/drafting.py`, `Sketch.not_this:
      Field(min_length=1)`, refused at parse; and again at the write-time
      floor, `hgi/lint.py` complement-law, "consultation latch declares no
      not-this exclusions", which refuses a draft the adjudicator admitted).
      Seven of the run's nine 120b new-decision drafts were refused here.
      The exclusion exists to recover precision for a hook biased broad —
      but a false fire costs one disposition and is telemetry (the
      consolidator's own register says so), and the precision leg
      (`counterfactual-edit`, grow `not_this` from `not_applicable`
      notes) exists to add exclusions after the record has fired wrongly.
      Gating admission on an exclusion the drafter has not yet seen the
      need for gates helpfulness behind compliance. *Slack:* default
      `not_this` to `[]` in the sketch (`Field(default_factory=list)`),
      drop the lint `fail` to a `warn` ("declares no exclusions; precision
      review will grow them"), and leave the precision leg as the place
      exclusions come from. *Risk:* a record with no exclusion fires on
      every presentation its terms match; the retirement leg
      (`applied_over_considered_below` 0.1 over 6 passes) retires one that
      never applies, so the cost is bounded by the window. Tests:
      `tests/test_roles.py::sketch_of` (empty `not_this` currently refused),
      the complement-law cases in `tests/test_lint*.py`; `test_precision.py`
      is unaffected (it grows a non-empty list).
    - **An edit rung must supersede exactly one record**
      (`hgi/consolidate.py`, `edited_body`). The 120b consolidator chose
      `counterfactual-edit` and `hook-edit` on an empty store (K-0002 of
      `120b-attached`, K-0003 of `20b-attached` with two records it did not
      name), so the draft was refused for naming no record. *Slack:* when
      `supersedes` is empty and the store holds no record the rung could
      edit, displace the nomination to `new-decision` the way a rung with
      no operator is displaced (`displacement`), keeping `rung_why`;
      when records exist and none is named, refuse as now. *Risk:* a
      displaced edit is drafted as a new decision from the same evidence,
      which is the right outcome on an empty store and a duplicate on a
      full one — hence the guard. Test: a stub nomination on an edit rung
      with an empty store lands as a new decision.
    - **The abstraction attack lands on a payload that names instances**
      (lens L-0007; the adjudicator declined H-0004 of `120b-attached` and
      H-0008 of `120b-strict` on it). The draft said "use /v2/zones/90,
      /v2/projects/82" instead of "a 410 that names a versioned route is the
      route moved; call the named route". The lens is right that the
      instance does not transfer — but the decline drops the draft, and
      the adjudicator has `admit-amended` with an `amendment` that
      replaces the decision text (`store.admit(..., amendment=...)`) and
      never used it on this run. *Slack:* tell the adjudicator (in
      `hgi/roles/adjudicator.md`) that a landed `payload:abstraction` on
      evidence that is otherwise sound is the case for `admit-amended`
      with the promoted payload, not `decline`; or, mechanically, re-ask
      the consolidator once with the landed claim ("promote the payload;
      keep the instances as anchors") before the verdict. *Risk:* the
      adjudicator promotes past the evidence — a floating entry — which the
      genesis article on promotion names as the overshoot; the anchors
      stay, so the lint's anchor checks still bound it.
    - **The watch-direction attack** (L-0008) landed on H-0008 because the
      sketched watch (`error_cause_present == 1.0`, `task_pass_rate >= 0.9`)
      fires on success; `hgi/drafting.py` already checks a watch's
      direction against the stakes (commit 585c1be) for the stub. *Slack:*
      when the watch is wrong, drop the watch (it is optional, `watch:
      null`) rather than the draft — a decision with no revisit latch is
      admissible and the retirement leg still bounds it. *Risk:* none to
      admission; a record without a watch is re-adjudicated only by
      currency and retirement.
    What not to loosen: the independence bar (two sessions) held every
    lesson group on this run and is what makes a recurrence a recurrence;
    and the premise kill (L-0006), which landed once (H-0008, on a missing
    `/v2` route that was in fact the task's own fault injection) — that one
    is an examiner reading error, not a floor to move. The order to take
    them in is the order above: the first two are contract floors that
    refused seven drafts at parse and cost nothing to relax; the third is
    where the lesson records will come from; the fourth is a one-line
    prompt note. A rerun of `120b-attached` alone after the first two is
    the cheapest test of whether the run admits.
33. **The fusion leg did not fold restatements.** The strict arm admitted
    D-0004, D-0005 and D-0006 after pass 10, each restating D-0002 or
    D-0001 almost verbatim (a token before any request; `/v2` plus a
    token; a token before any GET), so the same lesson sits in one store
    five times and every boot carries all of them. Split and fold run on
    the lineage DAG; nothing nominates two records with no lineage between
    them and the same latch for a fold. A textual or hook-overlap nominator
    (two accepted records whose `terms` match the same presentations and
    whose payloads the coder shapes alike) is the missing consumer.
34. **Detached draws lose Weave traces.** A detached arm's passes run in
    thread copies of the runner's context (`_detached_passes`), and Weave's
    trace-batch flush in those threads failed on every pass with
    `Invalid project_id format: . Expected 'entity/project'` ("Task
    failed", 96 times per arm); the evaluations, row calls and scores were
    written with project-qualified call URIs and the log is complete, so
    the cost is some traces of the detached draws, not data. The attached
    arms, which run in the main thread, logged cleanly. Untraced; the fix
    is probably to re-enter the Weave client in each worker or to run the
    draws sequentially under a flag.
35. **Code moved under a running arm.** The arm processes loaded the tree
    at 67c9ff0 when they started; the quality commits (2b0bc96, 4880cb4)
    landed on `main` while they ran and changed the curriculum's data draw
    (decision 68) and `hgi/evolution.py`. The runner imports `evolution`
    lazily at the arm's end, so the 20b arm wrote its log with the new
    module over the old rows (economy columns as dashes) and the plain
    120b arm's end write crashed on `Task.knowing` after its last pass —
    the arm's curve and store were complete and its final commit was made
    by hand. Every log under `experiments/results/stream/` was derived
    from a worktree at 67c9ff0 plus the close fix, with `HGI_RUNS` pointing
    at the main `runs/`; `hgi experiment evolution` on `main` rebuilds
    these arms from their recorded task ids with the pool-changed warning
    and would score the rows against a pool whose data differs. Import the
    log writer eagerly with the runner, and record the tree's commit in
    `arm.json`.
36. **W&B Inference's per-user concurrency.** Five arms at once — two
    attached at six tasks each and two detached at three passes of six —
    put 429s past the client's five retries into the detached rows (6 and
    7 of 80); the attached arms at six took none. The detached arms were
    redrawn alone afterwards (decision 70). The ceiling is somewhere
    between 12 and 30 concurrent requests on `openai/gpt-oss-120b`; a
    runner that serializes detached draws behind attached arms, or reads
    the limit, would let an experiment's arms run together safely.
37. **A lens reply that drops `noticed`.** The strict arm's first run died
    at pass 7's close on an L-0004 finding with an anchor and no `noticed`;
    `file_observations` now skips such a finding (1707b72,
    `tests/test_close_findings.py`). Whether to refuse the reply instead
    (the finding is malformed) is the contract's question; skipping loses
    an observation the pass tried to file.
39. **A consultation latch's scope is drawn from the observation's coding,
    not the task's terms** (economy run, `claude/nervous-rubin-e8e759`).
    D-0002 was admitted for `paged-api` rows and latched on
    `test-failure-triage`, the shape the blind coder gave the observations,
    so the boot index matched it to nothing and its competence window
    closed at zero considered: a record admitted but never retrieved. The
    task's own terms (`http-tool` for every API lesson) are on the
    observation's anchor and could seed the latch's `terms`; today the
    drafter chooses them. This is the retrieval floor the admittance-bar
    raise does not touch — a higher bar admits fewer records, none of which
    fire if the latch scope does not match the task.
40. **The close files observations about its scores, not the world's
    facts** (economy run). The close reads the row's scores by series name
    and the observations say so ("the `method_transfer` check was missed",
    "did not fire a check record to verify the total"); none of the forty
    named the convention (a footer row, a missing newline, a quoted comma)
    in words the blind coder could group on, and the two silent shell
    lessons stayed at 24/24 naive in both arms. The series names should not
    reach the close's brief, and the observation request should ask for the
    world's fact the row met, not the check the row failed.
41. **Drafts refused at parse at the `hook-edit` rung** (economy run). Six
    drafts were refused across three consolidations — three because the
    hook-edit named no record to supersede (`a hook-edit supersedes exactly
    one record; got []` on an empty store), three because `not_this` came
    back empty. These are gates 2 and 1 of item 32 seen again on a second
    run. A repair turn (re-ask with the refusal) or a rung-specific example
    in the request would recover most of them, keeping the contract rather
    than relaxing the floor; item 32 relaxes the floor instead. Every
    refusal is on the ledger, so the count is exact.
42. **A tool call with malformed arguments loses the row** (economy run).
    In the detached arm's pass 10 the model emitted a shell call whose
    arguments string was not valid JSON; `suite/tools.py` answered with a
    *bad tool call* result, but the assistant message carrying the raw
    string went back into the history and the endpoint refused the next
    request outright (`messages[2].tool_calls[0].function.arguments must be
    a valid JSON object string`), so the model never got the turn to read
    the error and retry. The row failed `error:model-call` — a symptom that
    covers a genuine endpoint fault and the model's own malformed output
    alike. The fix is in `suite/agent.py`: replay the assistant turn with
    arguments the endpoint accepts (the raw string wrapped as a JSON
    object) so the conversation continues and the wasted turn still costs
    turn economy; and split the symptom so the two causes read apart.

**Addressed (2026-09-13).** The gaps items 32–42 name are now built and on
`main`, each as a decision below with its risk: parse floors (item 32
gates 1–2, item 41) → decision 78; the hook seeded from the task's terms
(item 39) → 79; folding restatements (item 33) → 80; the close eliciting
the world's fact (item 40) → 81; the malformed tool call (item 42, decision
76) → 82; the runner pinned and its draws serialized (items 34–36) → 83. The
recurrence graded for the adjudicator → 84 and refused observations kept in
the open pile → 85 are the further levers built on top. The shape-radius
sweep (decision 77) found τ\*=1.0 — the coder's shapes already conflate
lessons, so widening the grouping radius is not the lever and item 40's
coding fix is; no `group_observations` change was made. The coder shaping on
the convention rather than the tool — the deeper reading decision 77 exposed
— is now built and measured on the stub (decision 87): the τ=1.0 grouping
moves from impure to pure at the source. What remains untested is a rerun on
the live endpoint — whether drafts now survive to adjudication, the seeded
hook fires, the fold collapses the restatements, and the live coder
normalizes each convention onto its registered term so the pure exact-match
grouping decision 87 shows on the stub holds on `openai/gpt-oss-120b`.

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
   git history, read by `hgi.store.admitting_commit` and printed by `hgi
   lineage` (decision 28). *Risk:* the spec puts the field on the envelope;
   a consumer expecting it there finds nothing.
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
    shape. *Risk:* the rule-tier rungs (`adoption-row`, `rule-enrollment`)
    have no operator in a decisions-only roster; an edit rung derives its
    successor from the record it supersedes rather than from a sketch
    (decision 34), and a sketch cannot express a latch the derivation does
    not know (a wiring latch, a second consultation hook).
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

28. **The admitting commit is the oldest commit naming the id**, rather than
    a commit parsed for the verb that names it. History is append-only and
    no message names a record before the commit that wrote it, so the oldest
    naming is the admission, and no vocabulary of message verbs has to be
    kept in step with the messages. A range such as the genesis message's
    `C-0001..C-0007` names each id it spans. *Risk:* a message that names an
    id it did not write — a revert, a plan, a message quoting another —
    reads as an admission; nothing enforces the convention the messages
    follow.
29. **A re-price that does not re-author says so on the record**
    (`priced_for.authored_for`). *Right:* the stamp cannot launder the swap
    into a green floor; the warning stands until the text follows, and
    swapping back clears the field because stamp and authoring agree again.
    *Wrong if* the two halves are really one act — then a store sits
    indefinitely priced for a model nothing was authored for, behind a
    warning nobody reads, which is exactly what `hgi genesis --force`
    avoided by making a price a fresh seed.
30. **A tombstone's `superseded_by` is a list**, not the scalar the spec's
    envelope example shows, because a split leaves one retiree with several
    heirs and a scalar cannot name them. A record written with a scalar or
    `null` reads as the list it means; `store/decisions/D-0001.json` still
    carries the scalar it was written with. *Risk:* a reader of the spec's
    example expects a string.
31. **A deferral is a latch on the draft itself**, in the pre-admission
    tier, and only that latch is exposed to the watch evaluator — the
    draft's own fan is not yet live. An adjudicator that defers without a
    condition, or returns an escape verdict, re-queues the draft at the
    next backward pass rather than leaving it without a condition that can
    fire. *Risk:* the adjudicator's `until` is read from a fixed shape
    (scorer, comparator, value, persistence — or passes); a condition it
    phrases otherwise becomes the schedule default.
32. **Observations a deferred draft rests on are claimed** until the draft
    is disposed, so it is not nominated twice from the same instances; a
    pass proposal is left unclaimed, so its instances still group and a
    nomination can adopt it. *Risk:* a declined draft frees them, and the
    same fork is nominated again at the next consolidation from the same
    observations.
33. **A wiring latch's guard remembers the status it saw**, and the fire
    ledger carries every later observation, so the latch stays immutable
    and one departure fires once. A warrant that cites a record is wired to
    it at admission, excluding the records the draft retires (the lineage
    edge already carries those, and citing a predecessor would otherwise
    close a wiring cycle the lint refuses). *Risk:* a wiring latch written
    before guards remembered statuses reads its successor as `accepted`.
34. **The edit rungs are successor records** derived from the one record
    they supersede with the named fields replaced — never an edit in
    place, because a decision is frozen after acceptance. The retirement
    review's nomination still names `counterfactual-edit` as its rung for
    want of a `retire` rung in the ladder vocabulary.
35. **Genesis anchoring is a currency question**, not an attack: the
    consolidator proposes an instance, the adjudicator reads the instance
    itself, and the ledger entry's species is `currency` with `still-holds`
    meaning the instance exemplifies the article. No examiner sits between
    them, because the claim is one instance and one article, not a five-slot
    draft. *Risk:* proposer and adjudicator without a contradictor is a
    weaker separation than the protocol of § 10.9; the adjudicator is handed
    the record, never the proposer's `why`.
36. **Vocabulary growth files as a `coding` entry** whose contradictor is
    the blind coder and whose verdict is `agree` | `disagree`; the
    adjudicator's own token (`admit` | `decline(<why>)`) is the entry's
    outcome. A declined term is re-nominated only by escapes from passes
    after the verdict.

37. **Every verdict seam routes through a closed table**
    (`registry.route_table`), and a term the vocabulary admits but the seam
    has no act for raises `Unrouted`; a test proves every table covers its
    vocabulary and the escape. *Right:* the `defer` fall-through of the
    first build cannot recur silently. *Risk:* an act tag is a string the
    seam dispatches on; the table proves coverage, not that the act is
    right.
38. **A settlement cites its licence** — an adjudicated ledger entry, a
    dispositive fire, or the admitted successor — and the committer refuses
    any other, so a corroborating fire nominates and never settles. The
    retirement latch is corroborating, so retirement cites the adjudicator's
    currency entry, and the lint proves the licence on every settled latch.
    *Risk:* `evict_article` cites no licence; the deadline in the bars is
    its only ground.
39. **A fire owed to the working pass is disposed at close** as a consulted
    record is — from the pass's own rows, in the session's commit — or the
    close is refused, and the lint's `fire-completeness` check reads the
    close seam. *Risk:* no latch in the decisions-only roster names the
    working pass as its disposer yet, so the path is proven by tests only.

40. **Escape recurrence clusters every closed vocabulary through one
    counter, keyed on the occasion the escape was written on** — a session
    for a work-shape, a `record#index` for a latch key-space, a ledger entry
    for a `<species>-verdict` — and `reviews.vocabulary` runs for each by
    default. A vocabulary no verdict seam routes (work-shape, key-space)
    grows in place on admit; a routed verdict vocabulary is surfaced but not
    minted, because growing it in place would leave the seam without an act
    for the new head (`registry.route_table` coverage). *Right:* one
    clustering law, and the demonstration store has no such escapes so the
    extra passes are no-ops there. *Risk:* an occasion of unknown pass (a
    verdict entry no session filed) is not gated by the after-pass re-count,
    so it can re-nominate each consolidation until adjudicated — its own
    uniqueness is the only guard; and the coder's contradiction still recodes
    the *suite presentations*, which are a work-shape signal, so its reading
    is weak evidence for a key-space or a verdict term.
41. **A revisit watch's direction is checked against the oracle's
    convention, not the prose stakes** — every scorer is a success rate in
    `[0, 1]` with `1.0` ideal, so a predicate the ideal satisfies but a
    failing score does not fires on success. The examiner (its stub logic
    and its prompt) lands `warrant:watch-direction` and the adjudicator
    declines. *Right:* the mechanical check needs only the two sentinels the
    suite's scorers share, and catches `task_pass_rate == 1.0` and `>= 0.9`
    alike. *Risk:* a scorer where lower is better, or one outside `[0, 1]`,
    would read backwards; the convention holds for `suite/scorers.py` today
    and is asserted nowhere the suite could not silently break.

42. **A nomination at a rung with no operator is carried as a decision that
    records its displacement.** Before this build a `floor`, `article`,
    `adoption-row` or `rule-enrollment` nomination fell through `draft_from`
    and became a decision draft wearing the rung's name; a first cut refused
    it outright, and that was reversed by instruction: the demo learns faster
    with a rule held as a decision than with no record at all, and the
    ideal-home cost is paid later, not never. The nomination's `rung` becomes
    `new-decision`, `displaced_from` keeps the rung it meant, and the
    committer stamps both on `admission`. *Right:* route-before-mint reads
    "cheapest sufficient home" over the homes that exist. *Risk:* a rule
    carried as a decision is recalled by the decision path — a full scan of
    summaries plus the hook — and has no adoption register, so "did you do it
    at every site" is never asked of it; the rule tier, when it comes, reads
    `displaced_from` to find what to re-home.
43. **The contradictor of a currency entry is the oracle, never the
    adjudicator.** Retirement, genesis anchoring, propagation and revisit
    fires wrote the adjudicator's call as the contradiction source, a
    contradictor = adjudicator collapse in name; the `oracle` role now names
    the fire, the ratio or the instance, and a pass's close-time contradiction
    is proposed by the record's admitter and contradicted by the pass. The
    `role-separation` check proves it on every line. *Risk:* the oracle's
    "call" is a fire id or a projection key, not a Weave URI, so the
    contradictor is joinable to the store and not to the trace.
44. **The noise filter is an adjudicator triage over every group at the
    bar** (spec § 10.2), before nomination, on a `reality` entry; an
    irreducible group is dismissed to the entry and never nominated. *Right:*
    I11 — nothing updates process on an irreducible failure — was a
    sentence in the spec and nothing in the code. *Risk:* one more adjudicator
    call per group; the stub classifies by harness markers ("model call
    failed", "turn limit"), which is the stub's reading of irreducible and
    not the doctrine's — a real adjudicator may dismiss a convention missed as
    "the model's own error", which is exactly the reducible case. The
    dismissed observations' recurrence tunes nothing yet: the reality entries
    are written and read by no detection-side leg.
45. **The boot recall lens has a consumer: the `recall` projection.** A
    probe naming an accepted record the pass did not consult, joined with
    steers indicting activation, is the should-have-fired stream; at the
    independence bar the consolidator re-keys the record with a hook-edit on
    the terms the probing passes presented. *Right:* § 16.21 — a lens whose
    product lands nowhere is theater. *Risk:* the stub adds every presented
    term the hook lacks, which widens a hook toward "every term"; the doctrine
    biases broad, but a real consolidator should add the term that names the
    presentation, not all of them.
46. **A pass's pending contradiction reaches the adjudicator at the next
    consolidation**, on a new entry citing the pending one; the pending line
    stays as history. *Risk:* the stub reverses a premise only when the
    finding names its id; a real adjudicator handed a finding with no
    premise id has only the prose.
47. **The examiner's angles are lenses, one call each** (the fan law and the
    host law): L-0005 independence, L-0006 premise kill, L-0007 abstraction,
    L-0008 watch direction, each declaring the claim classes it may land on,
    a claim outside its class dropped, every claim naming its angle and call.
    A register with no examiner lens falls back to the single-context attack.
    *Right:* one context walking four angles is a longer prompt, not an
    ensemble. *Risk:* four calls per draft on a real model, and the angles
    share the draft and the evidence pack, so their decorrelation is of
    context, not of input; the abstraction angle's `task_ids` are now the
    suite's task ids, so a payload naming a task is caught where before the
    list was always empty.
48. **Attacker precision is a projection and a brief row** (I16): landings
    upheld ÷ entries with a landing, per angle, with the
    should-have-been-caught-by misses (a survived record later indicted,
    reversed or moot) and two notes — zero landings interrogate the dispatch
    bar, a precision of one over zero overrulings is a ceiling artifact.
    *Risk:* nothing consumes the row into a nomination; the dispatch bar it
    interrogates is not a parameter anywhere.
49. **A lens carries a warrant and a status, and the lens review runs at
    every consolidation.** Anchors are derived from consumed products — a
    mechanical join, no adjudicator, because a derivable structure is a
    projection (I3) — and a lens at a door (genesis deadline, variance
    collapse over the review window) goes to the adjudicator; `moot` retires
    it, kept in the register and walked by nothing. `registry.lenses()`
    returns live lenses only. *Right:* I7 — every threshold has a retirement
    leg — reached the lens tier. *Risk:* the demonstration store's eight
    genesis lenses are past the deadline and unanchored (fifteen
    `genesis-anchor` warnings now, not seven); the next traced consolidation
    will retire those that were walked and produced nothing, which on the
    world run's evidence is L-0003, and possibly L-0001 and L-0002. A lens
    whose product is always empty is read as "no signal" and kept; a lens
    whose product is always the same non-empty finding is read as
    crystallized — the stub's L-0004 would be, on a suite with one recurring
    failure.
50. **Revision routing runs before a vocabulary grows.** Breadth (how many
    registered members the escaping occasions also carry) and dependence
    (the share carrying the most co-occurring member) read the pile as a
    missing peer, a partition of one member, or a cross-cutting dimension;
    the last is vertical — surfaced on the consolidation record, never
    minted, no ledger entry. Under twice the independence bar the reading is
    ambiguous and horizontal. *Right:* § 7.5 — a wrong axis at genesis
    outranks any number of missing members. *Risk:* the truth-maker feature
    is assumed identical for every escape of one vocabulary; a verdict
    vocabulary's occasions carry one member each, so its escapes always read
    as missing peers; and a vertical reading has no human seat but the
    consolidation record.
51. **The port declaration's miss stream widens a mark.** A latch admitted
    off its declaration on a warrant, recurring across independent records at
    the vocabulary's independence bar, is nominated to the adjudicator; admit
    corrects `registry/ports.json` from `forbidden` to `optional` in place, on
    a currency entry whose verdict is `reversed`. *Risk:* the only widening is
    forbidden → optional; nothing earns `required`, and nothing narrows a
    mark back.
52. **Four small floors from the activation section.** `summaries` carries
    each record's watch or `unwatched` and the consultation plan names the
    unwatched records (§ 16.17); the `key-space` check fails a neighbour key
    that resolves to nothing and a world-state watch on a scorer the oracle
    does not run (referents, never aliases); a human steer's note naming a
    record indicts it, the slot read off the note's words; the credit rows
    ship the counts their fractions are computed from (itemized, never net).
    *Risk:* the slot words are a keyword table; a note that says "hook" about
    a payload indicts activation.

53. **The true-miss cell counts rows, keyed `session/task`, and stays a
    floor.** A task that failed in a closed attached pass that consulted no
    record and filed no observation from the row is the event nothing caught:
    no latch fired, no floor refused, no noticing was made. *Right:* the cell
    was always written as a fixed empty list with a note calling it a "floor
    of zero", which is the one reading a floor forbids — an observed zero
    read as a measurement; now the store counts what it can see. *Wrong if*
    "consulted nothing" is too strict a key: a pass that consulted a record
    on another hook and still failed a row nothing bore on is also a miss
    nothing caught, and the cell does not count it — the applied disposition
    puts that pass in the top row even for the rows it did not touch.
54. **Fired-but-not-applicable is its own column, and precision is a brief
    row that nominates a `counterfactual-edit`**, at a bar of its own
    (`precision.not_applicable_over_considered_above`, 0.5), from the
    not-applicable dispositions' notes across independent passes. Two finer
    diagnoses outrank it in the derivation: a bimodal record is fused (a
    split, not an exclusion) and a record at its retirement door — never
    applied over a full window — is the retirement leg's. *Right:* the first
    slot signature of § 10.5 was a table row in the consolidator's prompt and
    nothing in the brief; the successor keeps the hook and grows `not_this`,
    which is the authoring register's own rule. *Wrong if* the bar is the
    wrong quantity: a record considered twice and not applicable once is at
    0.5 and nominated, and the independence bar on the notes' sessions is
    the only damper; and the stub adds every presentation the notes name,
    which on a real pass could grow `not_this` toward "every task".
55. **Never considered across a full window is the second retirement key,
    through the same currency request.** The record must have been accepted
    before the window opened (its `committed_at` against the first session's
    `started_at`), the window must be full, and the adjudicator sees the
    window's domain evidence — the terms its passes presented, the fault
    rate over its rows — against the record's `moot_when`; the stub keeps
    the record unless that condition is met by keyword (a fault condition
    with a zero fault rate, a budget condition with no budgeted presentation).
    *Right:* § 10.5's lifecycle row named "domain no longer entered" and the
    leg only read the ratio, which is `None` at zero considered; and never
    fired is a count, so the killer-item check sits between the count and
    the flip. *Wrong if* the stub's keyword reading of `moot_when` is taken
    as evidence of anything: it is the stub's, and a real adjudicator handed
    prose and a fault rate may retire a record whose domain would re-enter
    next pass. The nomination's rung is still `counterfactual-edit` for want
    of a `retire` rung (decision 34).
56. **A counterfactual's anchor must resolve, and an unresolved one warns.**
    The complement-law check resolves every id-shaped anchor through one
    store method (`lookup`: a file record, an observation by name or uid, a
    ledger line) that the anchoring review derives from too; a URI, a commit
    and a path are not resolved. *Right:* an anchor that matched the pattern
    and named nothing passed as anchored, which is priming wearing an anchor.
    *Wrong if* warn is too soft: a draft citing an invented observation is
    admitted with a warning nobody reads. Fail was not chosen because a
    conftest draft cites `O-0001` before the test has filed it, and because
    an anchor may name what a later admission holds; the demonstration store
    shows no unresolved anchor (its fifteen warnings are all
    `genesis-anchor`).
57. **The late steer sweep files a note once, keyed on its call URI, and the
    steer names its session.** At close, every earlier closed attached
    session's calls are re-read and a note whose call no steer's
    `source.anchor` carries is filed, stamped with the session it belongs to
    and listed on the closing session's `steers_filed`. *Right:* a note left
    after a close was lost for good, and the channel's whole point is
    capture before the context that understood it is gone. *Wrong if* the
    call URI is not a stable key across trace-store reads, or if re-reading
    every earlier session each close is the cost item 24 names; the sweep
    could be bounded to the review window.
58. **The antichain is printed as one conflict line and travels on the
    dispose request.** Records whose consultation hooks share every term
    with no lineage edge between them (no supersedure, leaf or fold) are
    read as co-applying with no specificity order; nothing ranks or drops
    one. *Right:* § 16.17 — a join over nothing is displayed, never
    tiebroken — and the pass is now told to dispose each on its own rows.
    *Wrong if* "share every term" is too narrow a reading of co-application:
    two hooks that overlap on the term that fired, and differ elsewhere, also
    co-apply on that pass and are not flagged.
59. **The seeded controls reuse the battery's scorers, evaluation and
    writer, one item per context.** Per examiner lens, a signal draft
    carrying a fault of that lens's class (one pass counted twice; a
    transient-fault premise under a zero fault rate; a task id in the
    payload; a watch on success) and a decoy draft with none, attacked
    through `consolidate.attack` with the one angle named; for the coder, a
    known-shape observation and a misfit. The stub passes both by the rules
    it already had (`_attack`, `_coding`) — no special case was added — and
    the examiner telemetry lands on the lens register while the coder's goes
    to `index/controls.json`, a telemetry file beside the projections that
    regeneration leaves alone. *Right:* a decoy-only battery cannot tell a
    lens that never fires from one that discriminates, and the controls give
    each angle a positive it must land on. *Wrong if* one plant per class is
    read as a rate: it is one item, and a lens that lands on it proves it can
    land, not that it does; and `controls.json` under `index/` bends the
    projection law (regenerated, never hand-edited) for the sake of one file
    a reader would look for there.

## Housekeeping

- `smoke_test.py` is the original W&B/Weave connectivity check and is not
  part of the package.
- The store's genesis articles and lenses are priced for `stub`. Before a
  hand-run on a real model, either `uv run hgi price --model <model>
  --restamp`, which keeps the store and leaves `model-pricing` warning that
  the text is still authored for `stub`, or `HGI_MODEL_ID=<model> uv run hgi
  genesis --force`, which prices a seed by writing it fresh and resets the
  store with it. A third option now keeps the store and moves the text with
  the stamp: `HGI_INFERENCE_BASE_URL=… HGI_MODEL_ID=<model> uv run hgi price
  --reauthor`, which re-authors each conditioning field against the model
  through the `reauthor` role and clears `model-pricing` (offline the stub
  answers but only marks the text; a real endpoint actually re-authors it).
  An experiment arm seeds its own store priced for its pass
  model and needs neither. The demonstration store's L-0004 product text
  predates the per-row walk; an arm seeded now carries the current text.
- `runs/smoke/`, `runs/baseline/`, `runs/baseline-precontract/`,
  `runs/probe/` and `runs/world/` on this machine are the 2026-09-12 runs;
  they are ignored by git. The baseline-precontract arms are the only
  record of the pre-contract run.

60. **The stream is prequential: every batch is a test set once and a
    training set afterwards**, and the curve is first-sight performance on
    unseen tasks as the store grows. *Right:* a suite run scores whether the
    store learned the tasks it was scored on, and the world run's curve
    moved within noise on the same 52 tasks; a knowledge base is asked to
    improve work that is always new. *Wrong if* one task per lesson per
    batch is too thin a sample: a lesson's first-sight rate over ten batches
    is ten draws, and the paired difference to the detached arm is the only
    thing that carries; the per-batch curve alone reads batch difficulty as
    learning.
61. **Same-shape failures are decided by the task's naive outcome, not by
    a judge.** Every lesson task carries its naive first-contact policy as
    its scripted policy, so the answer or error first contact produces is
    derivable by running it, and a failed row that reproduces it is the
    lesson missed the naive way — with the row's tool errors read too, so a
    410 met and reported without its cause still counts. *Right:* the
    external-oracle problem (a judge asked "is this the same error?") is
    replaced by a construction the task already has, deterministic and
    offline. *Wrong if* the naive policy is not the way a model misses: a
    model that reads a page and sums it wrong is `wrong`, not `naive`, and a
    lesson whose naive shape a model never reproduces shows no recurrence
    even when the lesson is never learned; the `wrong` and `error` columns
    are kept beside `naive` for that reason.
62. **Lessons are tiered by how the failure shows in the trace** (loud,
    visible, invisible), and the report groups by tier. *Right:* the world
    run's two conventions that never earned a record were silent ones, and
    whether the loop learns only what the trace names is the question the
    tiers put. *Risk:* the tier is asserted per lesson by hand, not
    measured; a model that reads a file with `cat` sees a footer row and one
    that sums with `awk` does not, so *visible* is a property of the pass as
    much as of the lesson.
63. **The curriculum is generated, not transcribed**, from one seeded
    generator per lesson over word lists, with clothes disjoint from the
    hand-written families' file names and routes and budgets that leave the
    knowing policy one call to spare. *Right:* no public dataset carries the
    structure the stream needs — many unseen instances of few recurring
    conventions — and the generator gives as many clothes as a stream asks
    (`CLOTHES`, twelve today; 84 tasks bound the stream at ten batches of
    eight). *Wrong if* generated clothes are too alike: a record that
    memorises "files named `<stem>-<n>.<ext>`" transfers within the family
    where a real world's next instance would break it; the `transfer`
    family's hand-written re-dressing is the stricter test and is not in the
    pool.
64. **The stream faults nothing by default.** The `[stream.faults]` profile
    defaults to no transient 502s, so the lessons are the conventions alone
    and a budget of two on a moved route is reachable (the world run's
    `versioned_status` sat behind two faulted calls under a budget of two,
    which no policy could pass). *Risk:* the retry lesson, the one lesson
    every model already has, is now absent from the stream, so the store's
    first admissions cannot be the tautologies the world run admitted — and
    cannot be the easy win either.
65. **A revisit is an attached pass after the stream with no consolidation
    after it, and a detached arm has none.** A detached pass is one draw of
    an evaluation, so meeting a batch again would repeat pass *k*; the
    attached arm's pass-*k* score is the first-sight baseline for its own
    revisit. *Risk:* the revisit passes are closed on — observations filed,
    proposals drafted — so a second revisit reads a store the first one
    touched, and the lint's per-pass checks run on them like any pass.

66. **Quality is graded by derived floors and a twin world, not by a
    judge.** Economy divides the knowing policy's calls (declared on the
    task; the budget is that plus the family's slack) by the calls spent,
    turn economy the same over model turns, and method transfer replays
    the pass's last shell command in a twin drawn from a second seed over
    the same names and routes. *Right:* the hint's value shows where
    correctness saturates — the probe passed five of seven lessons at
    first contact — and none of it needs a rubric. *Wrong if* the floor is
    gamed: a lucky one-call guess scores full economy, which is why
    transfer stands beside it; and a solution computed in the model's head
    after a `cat` scores zero transfer though it passed, which is the
    scorer's reading (no replayable method) and not the model's.
67. **A failed row's economy is zero, its transfer unevaluable.** Zero
    because a failed pass has no solution to be economical about and the
    series must not reward a cheap failure; unevaluable because a method
    that produced the wrong answer has nothing to transfer. *Risk:* the two
    conventions differ, so the two means over a batch are over different
    denominators; the log prints both with `—` where nothing was
    evaluable.
68. **The twin shares structure and varies data; the structural draw is
    separated from the data draw.** The generator's first seed fixes how
    many files, pages and which route, the second the counts, items and
    rows; the twin reseeds only the second. *Right:* a command replayed in
    the twin meets the same names and shapes and only its arithmetic is
    tested. *Risk:* separating the draws changed the pool since the probe
    ran (the evolution log rebuilds an old arm's batches from recorded task
    ids and says so); and six twins — the moved routes that answer `ok` —
    carry no data to vary and are identical to their tasks.
69. **The stream run's record is derived from the tree that ran it, not
    from `main`.** The logs and the curve report under
    `experiments/results/stream/` were regenerated from a worktree at
    67c9ff0 plus the close fix, and the README's numbers are theirs.
    *Right:* the rows were scored against that pool, and the symptom
    derivation reruns the naive policy against the task's world — a
    different data draw would mislabel rows. *Wrong if* the reader expects
    `hgi experiment evolution` on `main` to reproduce the files: it
    rebuilds the arms from recorded task ids with a warning and the
    symptoms may differ; the results directory is the record.
70. **The detached arms were redrawn alone rather than kept with their
    429 rows.** *Right:* a 429 after five retries is the endpoint's
    concurrency ceiling, not the model's first contact, and six and seven
    such rows in eighty would have moved the detached curves by the size
    of the effects being read. *Wrong if* a redraw is read as the same
    draw: the detached curve is now a second draw of the same batches,
    taken an hour later, and the attached arms' rows show no 429, so the
    comparison is paired per batch but not per hour.
71. **The strict attached arm was rerun from scratch, not resumed.** The
    runner has no resume; `--force` discards the store. *Right:* a resumed
    store would mix a first run that consolidated differently with a
    second; one run is one record. *Wrong if* the first run's
    consolidations mattered: they did (item 25) and survive only in a
    note. A resume that replays the recorded sessions and re-consolidates
    is the mechanism a long run needs.
72. **The arms ran concurrently.** *Right:* the five arms finished in
    ninety minutes instead of four hours on the night before the
    submission. *Risk:* item 36 — the detached draws paid in 429s and were
    redrawn; the attached arms' rows show no rate-limit error, so their
    curves stand.
73. **Independence and the watch's direction are the code's readings, not a
    lens's.** The distinct-session count of a draft's evidence against the
    bar is a lint floor check (`independence`) the committer refuses on,
    and a sketched watch that fires on success is dropped from the draft
    before any context opens — the watch is optional, the draft is not —
    with the drop recorded on the ledger claim; both join the attack first
    with no lens and no call, an examiner claim on either class that
    contradicts the computed reading is discarded, and L-0005 and L-0008
    are seeded retired through the crystallization door. *Right:* over the
    stream run's fifteen attacks `warrant:watch-direction` landed nine
    times and was wrong at least twice (on `task_pass_rate < 1.0` and
    `== 0.0`, both of which fire on failure) and `warrant:independence`
    landed on a draft whose group came from two sessions; a count and a
    comparator are gates, and a gate asked as a question is a lens whose
    answer has crystallized. *Risk:* a register seeded before this change
    still walks the two lenses and pays two calls per draft for claims
    that are then advisory; and a watch dropped is a record unwatched —
    its warrant returns only through the retirement ratio or a pass's
    close-time contradiction, never through the oracle's series.
74. **A landed abstraction claim amends; it never declines.** With no
    premise kill beside it and the bar met, the consolidator is re-asked
    once (the `promote` request: the payload, the refutation, the task ids
    and the instances) to restate the payload at the transferable shape
    with the instances kept as anchors; the abstraction angle is walked
    again over the promoted draft, the entry keeps the nominated text as
    its claim, the promoted text as its amendment and the promotion under
    `coding`; when no promotion comes back the adjudicator's
    `admit-amended` restates the payload and the committer admits the
    amended text. *Right:* on gpt-oss-120b the claim landed four times and
    was right each time, and the adjudicator never once returned
    `admit-amended`: an instance-shaped lesson is a lesson mis-stated, not
    a lesson refuted, and dropping it drops the recurrence with it. *Risk:*
    one more consolidator call per landed claim, whose product only the
    re-walked abstraction angle judges; a consolidator that promotes past
    the evidence yields a floating payload the anchors no longer
    instantiate, which only the adjudicator's exemplification check reads;
    and the re-ask returns the whole payload, so a promotion can change
    more than the instance's name.
75. **A decline stands only on an upheld premise kill.** The adjudicator's
    `decline` with no landed `premise:` claim is overridden to an admit —
    amended where it offered an amendment — the entry keeps the attack
    named (`survived-with-attack-named`) and its outcome says which token
    was overridden and why; the floor still refuses an overridden draft
    below the bar; defer and escalate are the adjudicator's as returned.
    A decline that stands is always `premise-killed`, so `attack-landed`
    is reached only from the human queue. *Right:* the run's two premise
    kills that stood were right, and every other decline was on a class
    that is now mechanical or amend-only. *Wrong if* a refutation exists
    that is neither a premise kill nor a mis-statement — an anchor that
    does not exemplify the payload is the case the prompt still names, and
    its decline is now an admission the floor cannot catch (exemplification
    is residue); the override is written on the outcome so the ledger shows
    where that happens.
76. **A model call the endpoint refuses fails the row, scored, not
    dropped** — and a refusal the model caused, by emitting tool-call
    arguments that are not JSON, is counted the same way (economy run,
    `claude/nervous-rubin-e8e759`). *Right:* a row the harness could not
    finish must not vanish from the denominator, and a model that writes
    malformed output did fail the task. *Wrong if* the endpoint's
    validation is stricter than the loop's: the loop tolerates a bad tool
    call and lets the model recover, the endpoint does not, so the row
    measures the endpoint's contract as much as the model; item 42 carries
    the fix.
77. **The shape-radius sweep: exact match already conflates lessons, so
    widening the Jaccard radius cannot buy precision on this data — τ\*=1.0,
    and the fix is the coding (item 40), not the radius.** A self-contained
    analysis (`hgi/grouping_sweep.py`, `hgi grouping-radius`, scorer test
    `tests/test_grouping_sweep.py`) sweeps τ over
    `{1.0, 0.67, 0.5, 0.33, 0.25, ~0}`, clustering observations by
    single-linkage connected components on `jaccard(shape_i, shape_j) >= τ`
    and scoring each clustering against the curriculum lesson the
    observation's anchor resolves to (the true label). *Dataset:* the
    recorded attached stream arms on disk (`runs/stream/{120b-attached,
    120b-strict, 20b-attached}`, not freshly generated), combined and
    session-namespaced per arm — N=104 labeled observations over 27
    sessions and 6 lessons (only `bom` drew none); the curve and table are
    written to `experiments/results/grouping-radius/radius.{json,md}`.
    *The curve* (τ → homogeneity / cross_lesson_clusters / lessons_at_bar):
    1.0 → 0.45 / 9 / 0; 0.67 → 0.45 / 9 / 0; 0.5 → 0.09 / 3 / 0;
    0.33 → 0.09 / 3 / 0; 0.25 → 0.09 / 3 / 0; ~0 → 0.00 / 1 / 0. *Reading:*
    the win the widening was meant to buy (`lessons_at_bar` — a lesson
    reaching the 2-distinct-session bar inside one pure cluster) is zero at
    every τ, because the precision cost is already paid at τ=1.0: the blind
    coder shapes on the tool or the triage, not the world's convention, so
    one shape covers many lessons before any merge — `[http-tool]` →
    {moved-v2, paged-api, token-route}, `[shell-tool]` → {csv-quoted,
    footer-row, trailing-newline}, `[test-failure-triage]` → four lessons.
    The recommendation rule (lowest τ with `cross_lesson_clusters == 0`,
    max `lessons_at_bar`) has no admissible τ — even exact match is impure
    — so it falls back to the baseline τ=1.0 with the caveat that widening
    the radius cannot recover a precision the join never had. *Right:* this
    is the same diagnosis as items 39 and 40 reached from the run logs, now
    measured — the shapes are generic, so grouping is not the lever;
    fixing the observation coding to name the convention (item 40) is.
    *Caveat:* thin data (N=104, ~15 obs/lesson) combined across two models
    and two families (curriculum, curriculum-strict), so the shape
    vocabulary is heterogeneous; the conflation holds within each single
    arm too, so it is not an artifact of combining. The scorer is trusted
    independently: `test_grouping_sweep.py` builds a synthetic labeled
    fixture whose Jaccard geometry is exact and whose τ\* (0.25) is known,
    and asserts the whole curve and the rule. *Next:* widening the labeled
    set with the real coder over the full 7×12 pool (needs a W&B inference
    endpoint; not run here) would sharpen the curve, but the recommendation
    would only change if fixing the coding first made the shapes
    lesson-specific. The number seeds a tunable registry bar default that a
    separate change wires into `group_observations`.
78. **The two parse floors that refused every draft before adjudication are
    relaxed** (commit `ceb51b6`, addressing item 32 gates 1–2 and item 41).
    `Sketch.not_this` defaults to `[]` and the complement law warns rather
    than fails on a consultation latch with no exclusions; an edit rung
    (`hook-edit`, `counterfactual-edit`) that names no record on an empty
    store is displaced to `new-decision` (keeping `rung_why`) instead of
    refused, while one that names none when records exist is still refused.
    *Right:* seven of nine 120b drafts and six more in the economy run died
    here before any verdict; a floor refusal only kept the lesson out of the
    store where it could be corrected, and the precision leg grows `not_this`
    from `not_applicable` notes after a record fires wrongly. *Risk:* a
    record with no exclusion fires on every presentation its terms match; the
    retirement ratio bounds one that never applies, so the cost is a window,
    not the store. The repair-turn alternative (re-ask the model with the
    refusal, item 41) was left unbuilt — the floor relaxation is item 32's
    prescribed cheaper first move.
79. **A record's consultation hook is seeded from the anchor tasks' own
    declared work-shape terms** (commit `f05eb7b`, addressing item 39). When
    a draft is assembled from a group of observations, the union of the
    tasks' `shapes` (resolved through each observation's anchor call to the
    row that names its task) joins the terms the drafter chose. *Right:* the
    economy run's one admitted record never fired because its hook carried
    only the blind coder's coding of how the failure presented, which the
    next task's classification did not share; the task's own term (`http-tool`)
    is on the anchor and matches the boot index. *Risk:* the seed broadens
    the hook toward whatever the task declares, so a record can be consulted
    on a task that shares the tool but not the fault — the same generic-shape
    problem decision 77 measures, here on the hook rather than the group; the
    not-this exclusions and retirement are what bound it.
80. **Near-verbatim restatements that never co-applied are folded** (commit
    `54635f6`, addressing item 33). `index.restatements` filters the
    shared-hook pairs to those with no lineage relation (connected components
    over the DAG's supersedure/split/fold edges) whose decision payloads
    overlap at or above a token-Jaccard threshold (0.6), and the
    consolidation brief surfaces them as convergence-shaped rows so each is
    drafted as a fold and adjudicated behind the floor. *Right:* the strict
    arm admitted D-0004/5/6 restating D-0001/D-0002, and every boot carried
    all of them; nothing nominated two lineage-unrelated records with the
    same latch and alike payload. *Risk:* the alikeness is a token-overlap
    heuristic that only *proposes* the merge — a threshold too low folds
    distinct records, too high misses restatements; 0.6 separated the run's
    cases but is a tunable parameter, and the floor and adjudicator are the
    real gate.
81. **The close elicits the world's fact, not the score it failed** (commit
    `3131406`, addressing item 40). The observation lens's brief drops the
    row's scores and every series-named field, and the pass is asked to name
    the convention the attempt turned on (a footer row, a missing newline, a
    quoted comma), never the check it scored against. *Right:* in the economy
    run none of forty observations named the convention in words the blind
    coder could group on, so two silent lessons stayed 24/24 naive; grouping
    starved before any bar. *Wrong if* the coder shapes on the tool anyway —
    decision 77 shows the shapes are generic even with better `noticed` text,
    so this fixes the observation's words but not yet the coder's vocabulary;
    making the coder shape on the convention is the unbuilt next lever.
82. **A malformed tool call no longer poisons the conversation, and its
    symptom reads apart from a genuine endpoint fault** (commit `c22f147`,
    addressing item 42 and decision 76). A tool call whose arguments are not
    valid JSON is replayed into history wrapped as a valid object
    (`{"_raw": …}`) so the endpoint accepts the next request and the model
    reads the bad-call result and retries; the wasted turn still costs turn
    economy. `error:model-call` splits into `error:endpoint` and
    `error:malformed-tool-call`. *Right:* one row of 96 was lost outright
    because the raw string made the endpoint refuse the next request, and the
    symptom conflated the model's fault with the endpoint's. *Risk:* the
    malformed flag is sticky for the row, so a later endpoint fault after a
    malformed call reads as `malformed-tool-call` — a retrospective grouping
    choice, defensible since the poisoning mode should no longer recur.
83. **The experiment runner is pinned and its detached draws serialized**
    (commits `0c3e659`, `941a6ef`, `f815546`, addressing items 35, 36, 34).
    The evolution writer imports eagerly with the runner and `arm.json`
    records the tree's commit; detached passes run serially by default
    (`ArmSpec.serial_detached = True`), with the concurrent thread-pool path
    behind the flag and the Weave client re-entered per worker thread when it
    is used. *Right:* quality commits moved the code under a running arm and
    changed a log; five concurrent arms drove the endpoint past its
    concurrency ceiling into 429s on the detached rows; the detached threads
    lost their Weave traces. *Risk:* serial detached draws are slower — a run
    that had headroom under the ceiling now pays wall-clock it need not; the
    flag restores concurrency, and Fix 3's `rejoin` is moot under the serial
    default (no worker threads spawn).
84. **The recurrence count is graded for the adjudicator** (commit `bd5df03`).
    `recurrence_reading` bands the distinct-session count N against the bar
    (below the floor / modest small-N / strong at ≥ 2×bar, mirroring the
    vocabulary nominator's small-N reading) and enters the adjudicator's
    request as context beside the draft, attack and oracle. *Right:* above
    the floor the count was discarded, so N=2 and N=10 read alike; a stronger
    recurrence is corroboration that a pattern is a real world-fact and bears
    on whether a premise refutation holds and on defer-versus-escalate.
    *Risk:* it is adjudicator-facing context only — the floor and the
    premise-kill logic are byte-for-byte unchanged, so N cannot mechanically
    admit a draft; a model that over-weights it could lean toward admitting a
    thinly-founded draft, which the premise checks and the floor still catch.
    Post-elegant-faraday a soft decline is already overridden to admit, so
    the count's remaining room is the adjudicator's reasoning, not a verdict
    override; whether N should ever soften a premise kill was left as the
    owner's call (it does not today).
85. **A refused draft's observations stay in the open pile** (commit
    `5db9358`, a regression lock, addressing the owner's requirement on
    item 39). Only `store.admit` promotes an observation; decline/drop, a
    floor refusal and escalate call only `drop_draft`, which touches no
    observation, and a deferral's claim on a live draft's evidence is the
    intended exception. *Right:* a lesson refused at N=2 must be able to
    regroup with a third instance at N=3 rather than be discarded; the test
    proves a premise-killed decline leaves its two observations open and they
    regroup at N=3. *Risk:* the open observations re-nominate the same lesson
    every pass until it is admitted, deferred or its observations retire —
    churn that decision 84's grading and the retirement ratio, not a
    suppression, are meant to resolve.
86. **The store is readable from outside the loop, through its projections**
    (`hgi consult`, `hgi/consult.py`; the skill `consult-decisions`). The
    read is additive: a new module registered beside the pass commands, no
    change to boot, close or consolidate, and no write to the store — the
    test hashes the tree before and after. Stage one is built from the
    `summaries`, `hooks` and `lineage` projections and so passes the
    settlement test by construction; stage two opens the record for the
    payload. The two latches are the boot's own: exact terms through the
    hook-major index, and the lexical nominator at the same two-token floor.
    The shape follows the sibling projects' consultation reads (WorldVue's
    `rules:adoption-status --shapes`, the Gauntlet's `gauntlet decisions`
    with its `adr-read` skill): an activation-only scan that withholds the
    payload, a targeted read, an unknown token refused with the vocabulary
    listed, and the reader as the matcher. *Right:* an end user's agent
    gets the lessons the loop admitted without running a pass, and the
    loop's ledgers stay the loop's — a consultation from outside files no
    disposition, so the applied-over-considered ratios the retirement leg
    reads are not diluted by reads it cannot score. *Risk:* no guard runs,
    so the reader decides the exclusions alone, and the `excluded_by` flag
    is the stub guard's literal reading, which a paraphrased exclusion
    escapes; the lexical route nominates on two shared stems, a floor that
    over-reaches on common words (`tool`, `call`) and under-reaches on a
    hook written in vocabulary the problem does not share — the surface
    fallback and the reader's eye are the recovery, not a better matcher.
    What an outside reader learns has no channel back into the store; if
    the reads should count, a consultation session kind with its own
    dispositions is the addition, and it would need the retirement ratio to
    distinguish it from a pass.
87. **The blind coder shapes on the convention, not the tool — the deeper
    lever decision 77 exposed** (commits `fe7a303`, `29e6d95`, addressing
    item 40's unbuilt next lever and decision 81). Decision 81 made the
    `noticed` name the world-fact; this makes the coder *group* on it. The
    work-shape vocabulary gains a convention-major granularity beside the
    tool-major cues (`route-versioned`, `listing-paged`, `route-guarded`,
    `field-quoted`, `summary-row`, `line-unterminated`, `byte-order-mark`);
    `coder.md` and the coding reply shape now tell the coder to shape an
    observation on the finer of the two its noticing names, a tool-major
    term only for a way of working with no world-fact behind it (a budget, a
    retry, a wrap) and `other(<convention>)` for a convention the vocabulary
    lacks. The tool cues stay: the boot classify still keys a consultation
    hook on the coarse cue, where the convention is hidden from the task
    prompt, so the stub gives the coder a convention keyword map distinct
    from the classify's tool map and `_classify` is untouched. *Measured*
    (`hgi grouping-shaping`, tests `test_convention_shaping.py`,
    `test_coder_convention.py`): on a synthetic labeled set in the blind
    close's voice the τ=1.0 grouping the sweep left in place moves from
    impure to pure — homogeneity 0.37→1.0, cross-lesson clusters 2→0,
    `lessons_at_bar` 1→7 (all seven), four shapes for seven lessons becoming
    one convention shape per lesson; re-coding the recorded arms (118 obs)
    both ways corroborates on real noticings, 0.48→0.96 homogeneity and 1→5
    lessons at the bar. The grouping radius did not move; the coding did.
    *Right:* two misses of one convention now share a shape and two of
    different conventions differ even when both called the same tool, which
    is exactly what decision 77 measured the tool cue could not do; the
    coder stays blind by construction — the coding request carries each
    observation's name and noticing and the flat term list, never the task
    id, the lesson or a score, a leakage guard pins it. *Risk:* the
    convention terms align one-for-one with the curriculum's scoring lessons
    because both enumerate the same world-conventions — the mechanism's
    target, not a leak, since the coder infers the term from the noticing
    prose, but a vocabulary that *is* the answer key's partition is a soft
    leak of the label space, and the guarantee rests on the noticing being
    blind (decision 81) and the per-observation label never in context. The
    numbers are the stub, a lexical proxy for the model's convention
    inference; the pending confirmation is a live re-score of freshly coded
    observations on `openai/gpt-oss-120b` (needs `WANDB_ENTITY` and a weave
    project), not run here — no live curve was fabricated. The recorded
    re-score's residue (homogeneity short of 1.0, two clusters still
    crossing) is the pre-81 noticings' noise, the gap the live re-score over
    post-81 noticings would close. If the model does not normalize a
    convention onto the same registered term across clothes, exact-match
    grouping splits a lesson on near-shapes — the completeness failure the
    radius sweep was meant to catch, now guarded only by τ\*=1.0 standing;
    the escape-to-vocabulary-bar path is the doctrine's answer if a
    convention the seed lacks recurs.
