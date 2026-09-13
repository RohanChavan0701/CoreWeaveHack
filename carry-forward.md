# Carry-forward

State of the build as of 2026-09-12, after the demonstration run, with the
work left for the full implementation and the decisions taken along the way
— each with why it may be right and why it may not.

## Where it stands

- Slices 0–3 of spec § 13 ship with their acceptance tests green
  (`uv run pytest`, 60 tests). Slice 4 ships the dashboard, the analyst
  mirror and the retirement leg; the rule tier and the grown floor do not
  exist because the roster is decisions only. Slice 5 (the demo) has run on
  the repository store and is recorded in the README's acceptance table.
- The demonstration ran on the deterministic stub (`hgi/stub.py`), because
  no CoreWeave inference endpoint credentials were available.
- `experiments/baseline.toml` has run twice on `openai/gpt-oss-120b` over
  W&B Inference (2026-09-12). The first run, before the role requests
  stated their reply shapes: attached 0.67 0.83 0.67 0.67 0.67 0.83,
  detached 0.67 0.67 0.83 0.67 0.67 0.83, no observation filed, nothing
  admitted — the model answered classify and every lens in JSON of its own
  shape, and double-wrapped `result` on two tasks. The second run, after the
  contract: 1.00 on every pass of both arms; eight observations filed, all
  recovered transient faults; nothing admitted. The README reports the
  second. The first run's arms are kept at `runs/baseline-precontract/` on
  this machine.
- State of the role contracts on the real model: `classify`, `lens`
  (L-0001, L-0004) verified; `dispose`, `guard`, `coding` ran inside the
  arm without refusal; `nominate` parses about half the time — the other
  half is a floor-rung or retirement latch in the work-shape key space,
  which the floor refuses, correctly; `attack`, `verdict`, `credit`,
  `currency` and `propose` have not yet received a parseable draft on the
  real model and are unverified. Each refusal now names every failing field
  on the nomination's outcome.
- `experiments/model-sweep.toml` and `cadence.toml` are written and have
  not been run; every model id they name is one `hgi experiment models`
  listed on 2026-09-12.
- Weave: traces, evaluations, attributes, feedback → steer, and the mirror
  are verified live in `slavazinevich-worldvue/hgi-dev` and used in
  `slavazinevich-worldvue/hgi`.

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
3. **A world the model cannot already handle.** The baseline is saturated:
   gpt-oss-120b scores 1.00 from pass 1 (README, *The baseline*). Two
   routes, both one arm each: a weaker pass model (`model-sweep.toml`'s
   `20b-attached` and the `split-roles` arm are the first to run), or
   harder faults — a 502 on the first two calls rather than one, a shell
   budget of one, a route that changes shape between passes. The suite is
   pinned by hash (spec § 14.1), so harder faults are a suite parameter
   the experiment file would have to carry (`FAULT_FRACTION` and the
   first-call rule in `suite/tools.py`), and a different suite hash per
   arm; the report already keys on the arm, not the hash.
4. **Finish the role contracts on the real model.** `nominate` still yields
   a refused draft about half the time; `attack`, `verdict`, `credit`,
   `currency` and `propose` are unverified (see *Where it stands*). The
   role prompt files still say `priced_for: stub` and nothing lints that
   header. Then `cadence.toml`; the report goes into the README by hand,
   because the arm stores live outside the code repository (decision 15).
5. **TypeSafe System1.** `hgi/coder.py` assumes an OpenAI-compatible surface
   behind `TYPESAFE_BASE_URL`; the real API shape is unverified (waitlist as
   of 2026-09-12). The role is the invariant; only the adapter changes.
6. **ARIA.** Interactive only. `hgi mirror` publishes the datasets it needs;
   the brief it drafts is recorded by URI with `hgi consolidate
   --analyst-report`. A programmatic surface would replace `build_brief`'s
   local derivation with the analyst's report as the primary input.
7. **Split and fold** (§ 10.6) as executed operators; today `lineage.split_from`
   and `folded_from` exist on the envelope and nothing writes them.
8. **The lens battery** (§ 9.2, slice 6a): decoy rejection scored in Weave;
   `LensTelemetry` fields are all `design-stage`.
9. **Genesis anchoring.** All seven articles are past the three-consolidation
   deadline without an anchor (the lint warns). The consolidator needs a
   nomination that anchors an article to an instance, or evicts it.
10. **The `defer` verdict** is accepted by the vocabulary but nothing turns its
   condition into a latch; the draft simply stays in `store/proposals/`.
11. **Wiring latches** are written on supersedure but nothing consumes them:
    propagation (`re-derive` / `check` on a neighbour's status change) is not
    run at consolidation.
12. **Structural-zero audit and escape recurrence** are projected but not
    nominated on; vocabulary growth by the route-before-mint ladder is
    `Registry.add_term` with no caller.
13. **The pass's own proposals** (close step 6) parse and file but the stub
    never drafts any; the real model may.
14. **Re-authoring on a re-price.** `hgi price --restamp` moves the stamp and
    records that the text did not move with it (decision 22); replacing the
    text against the new model is authoring work and is not mechanized. A
    role that re-authors a lens's angle or an article would close this, and
    would meet the same unverified drafting contracts as item 4.
15. **`hgi experiment`'s genesis message names no article ids** (`Genesis for
    <exp>/<arm>: priced for …`), so `hgi lineage C-0003` finds no admitting
    commit in an arm's store, where `hgi genesis`'s message would. One line
    in `hgi/experiment.py`, left to whoever owns that file next.

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
   lineage` (decision 21). *Risk:* the spec puts the field on the envelope;
   a consumer expecting it there finds nothing.
5. **Facts are mirrored on the session record** (`evaluation.scores` and
   `evaluation.rows`) with the Weave run URI as `source`, and the watch
   evaluator reads them from the session ledger, not from Weave. *Right:*
   offline runs, reproducible tests, one read path. *Risk:* the spec keeps
   facts in the oracle; a fact edited on a session file is not the oracle's.
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
   tasks' pass fraction before and after. *Right:* two records applied in the
   same passes are not confounded (D-0001 and D-0002 in the demo). *Risk:*
   `before` is the same tasks' earliest history, which conflates "the record
   didn't help" with "the tasks were always hard".
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
    tries to average the heterogeneous task outputs and raises. *Risk:* the
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
    wrapper; both are now read defensively, and the test on `REPLIES`
    forbids a string beside an object in any list.
20. **Every role receives the whole JSON schema of Observation, Draft and
    LedgerEntry**, definitions included (about three thousand tokens a
    call), and the drafting requests carry every closed vocabulary. *Right:*
    the body's typed fields stopped carrying invented terms. *Risk:* cost
    per call, and the vocabularies are validated at runtime only — the
    schema still says `string`.

21. **The admitting commit is the oldest commit naming the id**, rather than
    a commit parsed for the verb that names it. History is append-only and
    no message names a record before the commit that wrote it, so the oldest
    naming is the admission, and no vocabulary of message verbs has to be
    kept in step with the messages. A range such as the genesis message's
    `C-0001..C-0007` names each id it spans. *Risk:* a message that names an
    id it did not write — a revert, a plan, a message quoting another —
    reads as an admission; nothing enforces the convention the messages
    follow.
22. **A re-price that does not re-author says so on the record**
    (`priced_for.authored_for`). *Right:* the stamp cannot launder the swap
    into a green floor; the warning stands until the text follows, and
    swapping back clears the field because stamp and authoring agree again.
    *Wrong if* the two halves are really one act — then a store sits
    indefinitely priced for a model nothing was authored for, behind a
    warning nobody reads, which is exactly what `hgi genesis --force`
    avoided by making a price a fresh seed.

## Housekeeping

- `smoke_test.py` is the original W&B/Weave connectivity check and is not
  part of the package.
- The store's genesis articles and lenses are priced for `stub`. Before a
  hand-run on a real model, either `uv run hgi price --model <model>
  --restamp`, which keeps the store and leaves `model-pricing` warning that
  the text is still authored for `stub`, or `HGI_MODEL_ID=<model> uv run hgi
  genesis --force`, which prices a seed by writing it fresh and resets the
  store with it. An experiment arm seeds its own store priced for its pass
  model and needs neither.
- `runs/smoke/`, `runs/baseline/` and `runs/baseline-precontract/` on this
  machine are the 2026-09-12 runs; they are ignored by git. The first two
  are regenerable; the third is the only record of the pre-contract run.
