# Seed store: the incidents stream

A mature store for the `incidents` and `incidents-strict` families
(`suite/families/incidents.py`, data `suite/data/incidents.jsonl`), hand-authored
to the rules in `../AUTHORING.md`. It is what the loop should hold after enough
passes over the stream that every convention of this world has been observed,
drafted, attacked and admitted: four decisions, one per decoy shape and one on
the walk itself.

## The world

Nine bundles, each worn four ways: a brief (Surface, Signal, Blast radius) and
a menu of readings served one per `GET /readings/<name>`. The budget is the
count of the bundle's cause readings plus the family's slack — one call on
`incidents`, none on `incidents-strict`. The check needs the class named, at
least one cause reading cited, and no decoy reading cited; citing the decoy
fails the task however right the class is. Every bundle presents as
`("http-tool", "tool-budget", "task-planning")`.

The convention of the world is *the loud reading is the wrong one*, and which
loud reading it is, is the bundle's lesson:

| lesson | bundles | what is loud | what is the cause |
|---|---|---|---|
| `decoy-dependency` | pool-exhaustion a/b/c | the datastore probe, log and metrics; the network probe; the outbound dependency probe (all healthy) | the service's own pool counters, pool/client settings, service log |
| `decoy-saturation` | bad-deploy-a, poison-message a/b, upstream-outage a/b | host, replica, traffic, gateway, connection, worker, broker and datastore metrics; pool counters and settings; queue depth history; producer log | the release ledger, build diff, known-good, service log (bad-deploy); the provider status page, outbound probe, service log (upstream-outage); the queue counters, queue head, worker log (poison-message) |
| `decoy-state` | bad-deploy-b | input samples, catalog audit, request samples, data change log (the data unchanged) | the release ledger, build diff, known-good, service log |

Dressings 1–3 rename every reading and every service, shift ports by a
thousand and the clock by three hours. What survives every clothing is the
brief's prose — the Signal's shape and whether the Surface names an external
provider — and the *shape* of each reading's name (a counter, a probe, a
ledger, a journal). So a record carries the shape of the decoy and the symptom
signature of the brief, never a reading name, a service name or a port.

## What the pass sees

At work time the pass is shown `id`, `terms`, `stakes` and the `decision`
sentence of every record that latched (`suite/agent.py:107`, `:151`). Nothing
else reaches it — not the latch, the context or the exclusions. Every decision
here is therefore self-contained: the symptom signature to recognise, the
readings to open (by shape), the readings never to open or cite, and the class
to name. The guard at boot is a model call over the whole batch's presentations
with the record's terms and `not_this`; a batch mixes the three shapes, and an
exclusion that covers one presentation but not all does not fail the guard
(`hgi/roles/__init__.py:37`), so each shape record fires on every batch and
applies to the bundle whose brief matches.

## The decisions

All four latch on `http-tool`, `tool-budget`, `task-planning` — the terms the
family registers (`SHAPES`, `suite/families/incidents.py:65`). Each carries a
consultation latch with the other shapes as `not_this`, a world-state revisit
latch on `suite-v1`, and the standard retirement latch (applied-over-considered
below 0.1 over 6 passes).

### D-0001 — plan the walk against the budget

*Payload.* Before the first fetch, read the brief's Signal and Surface for the
failure's shape, take the reading menu from the prompt (listing is free), and
rank the readings by how likely each shows the cause rather than the symptom.
The budget is the cause readings plus at most one; the answer needs the class
plus one cause reading; a decoy cited fails. Open the highest-ranked cause
reading first, stop as soon as one confirms the class, answer. Never open the
loud capacity reading first to rule it out, never walk the menu in listed
order, never open a reading only to corroborate, cite only what was opened and
the fewest that show the cause.

*Not implied by the shape decisions.* The three shape records say *which*
readings carry the cause; this one says how to spend the budget on any bundle:
the check needs one cause reading, not all of them, so the cheapest passing
walk is one call, and the knowing floor (one call per cause reading) is a
ceiling on what a knowing pass should spend, not a target.

*Excludes.* A task with no call budget; a brief with the evidence inline; a
first reading opened because it is the likeliest cause reading (the record
forbids the loud reading first, not a first reading).

*Stakes.* The naive walk dies on the budget before any answer
(`naive_for`, `suite/families/incidents.py:200`); a rule-out call spends the
one spare call on `incidents` and is over budget on `incidents-strict`; every
extra call lowers `solution_economy`.

*Watch.* `tool_budget_respected < 0.9` over 2.

### D-0002 — decoy-dependency: the pool is the cause, the dependency is the decoy

*Signature.* A gateway timeout storm on a datastore-backed service; the brief
says the service is *failing under load* and the storm *sets in as request
volume climbs*; the Surface names no external provider.

*Payload.* Open the pool counters/gauges reading first (the pool saturated,
`in_use` at max with requests waiting); a second reading, if wanted, is the
pool/client settings or the service log (pool wait climbing while each query's
own time stays flat). Name `pool-exhaustion`, cite the pool reading(s). Never
open or cite the datastore probe, log or metrics, the network probe or the
outbound dependency probe: they read healthy and any one cited fails.

*Direction.* This is precisely the shape where the saturated pool is the cause
and the dependency readings are the decoy. The look-alike control
(`upstream-outage-b`, `suite/families/incidents.py:39`) is the opposite: a
pool genuinely at max that is a consequence of provider latency, whose pool
readings are decoys. The brief separates them — volume climbing with no
provider (this record) versus volume unchanged with a provider named
(D-0003). D-0002's counterfactual is exactly "timeout storm, therefore the
pool" applied to the control.

*Excludes.* The saturation signature (D-0003); the state signature (D-0004); a
storm on a service whose Surface names a provider and whose Signal says volume
did not change; backlogs; fractional error spikes.

*Knowing floor saved.* 3 cause readings; the seeded walk spends 1–2 calls.

### D-0003 — decoy-saturation: the loud capacity reading is a consequence

*Signature.* The Signal describes an *abrupt step* rather than a gradual
climb, or says *request volume did not change*, or a *backlog growing
linearly with throughput near zero* on a single in-order worker.

*Payload.* Never open or cite host/node metrics, replica/instance status,
traffic/load metrics, gateway/edge status, socket/connection stats,
worker/consumer metrics, broker or datastore health and metrics, pool counters
or pool/client settings, queue depth history or the producer log. Route on the
brief before the first fetch: (1) an abrupt step with no provider in the
Surface → the release ledger, build diff, known-good or service log;
`bad-deploy`. (2) a Surface naming an external provider, with the step in
latency or per-request errors after a fixed delay → the provider status page,
the outbound probe or the service log; `upstream-outage`, a saturated pool
being the consequence of provider latency. (3) a growing backlog on one
in-order worker → the queue counters, the queue head or the worker log;
`poison-message`. One cause reading confirms; stop.

*Excludes.* The dependency signature (D-0002) — a storm that sets in as volume
climbs, where the pool *is* the cause and this record must not turn the pass
away from it; the state signature (D-0004).

*Knowing floor saved.* 3–4 cause readings per bundle; the seeded walk spends
1–2 calls.

### D-0004 — decoy-state: it is the release, not the data

*Signature.* An error spike where a *steady fraction* of requests fail with a
server error while the rest succeed, stepped up abruptly, on a surface with no
timeout storm.

*Payload.* The data-shaped readings — payload/input samples,
catalog/inventory audit, request/call samples, record/row change log — are the
decoy; the data is unchanged. Open the release ledger first (a new build
started at the onset); a second reading, if wanted, is the build diff, the
known-good baseline or the service log (the build id flips at the onset and
the failing status begins). Name `bad-deploy`, cite the release reading(s).
Never open or cite a data-shaped reading, not even as corroboration beside the
ledger.

*Excludes.* The dependency and saturation signatures (D-0002, D-0003); a
failure of essentially every request; an error spike whose change log shows
the data changed at the onset.

*Knowing floor saved.* 4 cause readings; the seeded walk spends 1–2 calls.

## Where the lessons show

All three lessons are tiered *visible*: nothing errors, and the convention is
in the reading the pass already opened — a pool at max whose dependency probe
reads healthy, a build id flipping at the onset, one head id redelivered with
the same error. The evolution log's mention heuristic (`suite/lessons.py`,
`LESSONS[...]["keywords"]`) reads a record's decision, latch and context; the
seed's prose uses those words where they are true (pool, saturated, in_use,
waiting, dependency; consequence, provider, deploy, queue head, not the cause;
deploy, release, regressed, not the data), so a seeded arm's log attributes
each lesson to the record that carries it.

## What the compare/contrast expects

`experiments/incidents.toml` deals the 36 tasks into twelve batches of three,
balanced over the three decoy shapes, consolidating every two, revisiting
batches 1 and 2. The world faults nothing, so the budget means one thing: one
wrong turn or none.

- **`120b-attached` seeded versus unseeded, on `incidents`.** From batch 1 the
  seeded arm names the class and cites a cause reading within budget on every
  bundle: `task_pass_rate` near 1 from the first pass, `tool_budget_respected`
  at 1, `solution_economy` at or above 1 (the knowing floor over calls spent,
  and the seeded walk spends fewer calls than the floor). The unseeded arm
  opens the loud reading first — the datastore probe on the pool bundles, host
  or pool metrics on the abrupt-step bundles, the input samples on the
  fractional spike — and either spends the slack and lands (a pass at
  `solution_economy` below 1) or cites the decoy and fails with the class
  right; its curve climbs only as the store admits the convention over
  consolidations, and a record that memorised a reading name transfers to no
  re-dressed clothing.
- **`120b-strict` seeded versus `120b-strict-detached`, on
  `incidents-strict`.** With zero slack, the one rule-out call is over budget.
  The seeded arm stays in budget from batch 1 — the record names which
  readings carry the cause before the first fetch, which is exactly what the
  strict pool asks. The unseeded arm's first wrong turn is a `budget`
  naive-shape failure, the same class the deterministic stub produces
  (`experiments/incidents-smoke.toml`).
- **The look-alike control.** `upstream-outage-b` in every clothing is where a
  generic "saturated pool ⇒ pool exhaustion" record fails; the seed's D-0002
  excludes it by the brief's signature and D-0003 routes it to the provider.
  A seeded arm that fails the control in any clothing has a record whose
  direction is wrong, not a record that is missing.
- **Retention.** The revisited batches 1 and 2 should score the same as their
  first sight in the seeded arm; the seed carries no per-bundle memory, so
  there is nothing to retain and nothing to forget.

## Validation

Seeded into a fresh `hgi genesis` store, `registry/ids.json` "D" bumped to 4,
`hgi index` then `hgi lint`: `lint: green — 0 failures, 0 warnings`.
`hgi consult --terms http-tool,tool-budget,task-planning` latches all four
through the index; a dressed pool-exhaustion brief passed as `--problem`
nominates D-0002 with the strongest lexical overlap.

Anchors are `path:line` into `suite/families/incidents.py` only: the anchor
pattern (`hgi/types.py`, `ANCHOR_PATTERN`) recognises `*.py:<line>` and
nothing else, so a line in `suite/data/incidents.jsonl` would not count as an
anchor and the priming warning would fire.
