# Carry-forward

State of the build as of 2026-09-12, after the world run and the review
pass, with the work left for the full implementation and the decisions
taken along the way — each with why it may be right and why it may not.

## Where it stands

- Slices 0–3 of spec § 13 ship with their acceptance tests green
  (`uv run pytest`, 237 tests). Slice 4 ships the dashboard, the analyst
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
   (`tests/test_lens_battery.py`). Left for a run: with `HGI_WEAVE_PROJECT`
   and the real model as the pass backend, confirm the `lens-battery-v1/*`
   scorer series appear in Weave with a non-null run URI, and commit the
   demonstration store's real-model telemetry — the committed
   `store/registry/lenses.json` is deliberately left at `design-stage`.
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
    `attack` (one angle per call) and the `lens`- and `finding`-bearing
    `currency` requests parse on the stub and have not been read back through
    `hgi roles try` on `openai/gpt-oss-120b`; `role-pricing` will not warn,
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
21. **The antichain is displayed as a list, not as a conflict.** Two
    decisions co-applying to one task with no specificity order enter
    context side by side (never tiebroken, which the doctrine requires), but
    nothing marks them as a conflict for the pass or the human; the leaf
    lattice that would give them regions is a split nomination only.
22. **Yield per steer is not instrumented.** The matrix counts steers and
    the credit table attributes them; nothing reads how much each steer
    moved — the quantity the doctrine says to maximize, against steer count,
    which it says never to target.
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
