# Carry-forward

State of the build as of 2026-09-12, after the demonstration run, with the
work left for the full implementation and the decisions taken along the way
— each with why it may be right and why it may not.

## Where it stands

- Slices 0–3 of spec § 13 ship with their acceptance tests green
  (`uv run pytest`, 26 tests). Slice 4 ships the dashboard, the analyst
  mirror and the retirement leg; the rule tier and the grown floor do not
  exist because the roster is decisions only. Slice 5 (the demo) has run on
  the repository store and is recorded in the README's acceptance table.
- The demonstration ran on the deterministic stub (`hgi/stub.py`), because
  no CoreWeave inference endpoint credentials were available. The model
  path (`hgi/model.py` OpenAICompatible; `suite/agent.py` tool loop; every
  role prompt) is written and untested against a real endpoint.
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
3. **Run the loop on a real frozen model.** Set `HGI_INFERENCE_BASE_URL`,
   `HGI_INFERENCE_API_KEY`, `HGI_MODEL_ID`. Expect to iterate on the JSON
   contracts of each role request (`classify`, `guard`, `lens`, `dispose`,
   `propose`, `coding`, `nominate`, `attack`, `verdict`, `credit`,
   `currency`) — the stub defines them by example; the role prompts state
   them in prose only. Re-price the lenses and articles for that model.
4. **TypeSafe System1.** `hgi/coder.py` assumes an OpenAI-compatible surface
   behind `TYPESAFE_BASE_URL`; the real API shape is unverified (waitlist as
   of 2026-09-12). The role is the invariant; only the adapter changes.
5. **ARIA.** Interactive only. `hgi mirror` publishes the datasets it needs;
   the brief it drafts is recorded by URI with `hgi consolidate
   --analyst-report`. A programmatic surface would replace `build_brief`'s
   local derivation with the analyst's report as the primary input.
6. **Split and fold** (§ 10.6) as executed operators; today `lineage.split_from`
   and `folded_from` exist on the envelope and nothing writes them.
7. **The lens battery** (§ 9.2, slice 6a): decoy rejection scored in Weave;
   `LensTelemetry` fields are all `design-stage`.
8. **Genesis anchoring.** All seven articles are past the three-consolidation
   deadline without an anchor (the lint warns). The consolidator needs a
   nomination that anchors an article to an instance, or evicts it.
9. **The `defer` verdict** is accepted by the vocabulary but nothing turns its
   condition into a latch; the draft simply stays in `store/proposals/`.
10. **Wiring latches** are written on supersedure but nothing consumes them:
    propagation (`re-derive` / `check` on a neighbour's status change) is not
    run at consolidation.
11. **Structural-zero audit and escape recurrence** are projected but not
    nominated on; vocabulary growth by the route-before-mint ladder is
    `Registry.add_term` with no caller.
12. **The pass's own proposals** (close step 6) parse and file but the stub
    never drafts any; the real model may.
13. **`admission.commit`** is not stored (see decision 4 below); `hgi lineage`
    does not yet read the admitting commit from git history.
14. **Model-pricing** warns only; nothing re-prices.

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

## Housekeeping

- `smoke_test.py` is the original W&B/Weave connectivity check and is not
  part of the package.
- The store's genesis articles and lenses are priced for `stub`; reseed with
  `HGI_MODEL_ID=<model> uv run hgi genesis --force` before a real-model run
  (this resets the store).
