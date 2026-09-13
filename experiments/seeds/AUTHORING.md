# Seed stores: how a stub is authored

A seed is a hand-authored decision store injected into an arm before its first
pass — what a mature store for that world would hold after enough passes and
consolidations that every convention of the world has been observed, drafted,
attacked and admitted. It is the *target* the loop is meant to reach; an arm
run with the seed injected against the same arm run from an empty store shows
what the injected decisions buy.

Layout of `experiments/seeds/<world>/`:

- `README.md` — what a mature store for this world looks like: the
  conventions the store must carry, which are loud/visible/invisible in the
  trace, what each decision keys on (registered work-shape terms), what it
  excludes, and what the compare/contrast experiment expects the injection to
  change (which batches, which scorer, which budget).
- `decisions/D-0001.json …` — one file per decision, in the exact shape of
  `store/decisions/D-0001.json` and `runs/stream/120b-attached/store/decisions/D-0001.json`
  (the pydantic model is `hgi.types.Decision`). Status `accepted`.
- `vocabulary.json` (optional) — `{"work-shape": {"<term>": "<means>"}}` new
  terms the seed's latches key on beyond the registered nine; the injector
  registers them so the boot's classify step can name them.

Rules a seed decision must satisfy (`hgi lint` in a seeded scratch store is green):

- `admission.proposed_by` is `"seed"`, `admission.verdict` is `"admit"`,
  `admission.ledger_entry` is `null`, `admission.adjudicator` is
  `{"role": "adjudicator", "model_id": "seed", "call": null}`,
  `admission.rung` is `"new-decision"`.
- `status` is `"accepted"`; `priced_for.model_id` is `null` (the injector prices
  it for the arm's pass model).
- Every consultation latch keys on registered work-shape terms
  (`error-wrapping file-tool http-tool output-schema shell-tool task-planning
  test-failure-triage tool-budget tool-call-retry`) or on terms declared in
  `vocabulary.json`, and carries `not_this` exclusions.
- The counterfactual cites an anchor. A seed has no observations, so the
  anchor is a `path:line` into the family or data file that shows the
  overshoot (for example `suite/families/text2sql.py:97`), and
  `warrant.anchors` lists the same path anchors.
- Premises carry falsifiers; the retirement latch is present and live.
- Ids are `D-0001 …` per seed; the injector renumbers past the store's own.
