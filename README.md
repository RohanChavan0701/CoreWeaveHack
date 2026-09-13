# HGI — an attached associative memory for agent loops

HGI attaches to an agent loop and gives a frozen model a memory that learns
between passes. The loop's typed record corpus is its learning system: a
**forward pass** reads the store into context and acts; an **oracle** scores
what happened; a **backward pass** consolidates the signal into refined
records under separation of powers. No weights change. Everything the loop
knows lives in legible text under git.

The full design is in [spec.md](spec.md). This README states what the
repository implements, how to run it, and how each sponsor surface is bound.

## Store roster

The store space is cut by decay profile and by truth-maker (spec § 4). The
implemented roster is the **case leg plus its floor**: decisions are the one
live-question store; beliefs (the world leg) and rules (the duty leg) are
declared in the specification and not yet instantiated. Every other organ
that a full cycle needs is present.

| Store | Holds | Directory |
|---|---|---|
| constitution | the always-loaded articles, hard-capped | `store/constitution/` |
| decisions | settled point decisions constraining future forks | `store/decisions/` |
| observations | anchored noticings below every admission bar | `store/observations/` |
| ledger | hypothesis-ledger entries by species (attack, coding, reality, …) | `store/ledger/` |
| fires | latches whose guard passed, each owed a disposition | `store/fires/` |
| dispositions | use-time verdict per consulted record per pass | `store/dispositions/` |
| steers | corrections with credit assignment | `store/steers/` |
| sessions | one record per pass with its carry-forward | `store/sessions/` |
| proposals | the pre-admission tier: drafts with a `uid` and a recyclable `name` | `store/proposals/` |
| queue | proposals whose verdict is `escalate(<why>)`, awaiting a human | `store/queue/` |
| registry | closed vocabularies, ports, bars, the constitution cap, lenses, id counters | `store/registry/` |
| index | regenerated projections; never hand-edited | `store/index/` |

Traces and facts are not directories. They live in the oracle and are
referenced by anchor.

## Sponsor stack

Each binding names the role as the invariant and the vendor as the
coordinate (spec § 9).

| Role | Sponsor surface | Binding |
|---|---|---|
| trace store, the world, the steer channel | **W&B Weave** | `@weave.op` on every model and tool call with `hgi.session`, `hgi.pass`, `hgi.role` and `hgi.records_in_context` attributes; the task suite is a `weave.Dataset`, each scorer a `weave.Scorer`, each pass a `weave.Evaluation` run; feedback on calls becomes steer records |
| the frozen model | **CoreWeave inference endpoint**, or **W&B Inference** | one OpenAI-compatible client per model, installed per role; every call records its model id; every lens records the model it was priced for |
| the consolidation analyst | **W&B ARIA** | reads the disposition and session ledgers mirrored to Weave as datasets and drafts the consolidation brief; its report URI is recorded on the consolidation session; it nominates, never verdicts |
| projections and the escalation surface | **marimo** | `dashboard.py` renders the index, the lineage DAG, the detection matrix and the escalation queue live from the demonstration store or any experiment arm's, overlays every arm of an experiment on one chart, and writes only through `hgi` commands |
| the blind second coder, the guard evaluator | **TypeSafe AI System1** | classifies observations against the registry's shape terms without the consolidator's candidate labels; falls back to a second, separately prompted frozen-model context when the vendor is not configured |

## The demonstration and its acceptance bar

The run of spec § 14 is in the store and in the Weave project
[`slavazinevich-worldvue/hgi`](https://wandb.ai/slavazinevich-worldvue/hgi/weave):
six passes with the store attached, six detached (same agent, same suite
hash, no boot or close), consolidation every two passes. The frozen model
for this run is the deterministic stub (no inference endpoint was
configured), so the curve shows the loop's mechanics closing, not a model
learning; the stub applies a record only by keyword, exactly as documented
in `suite/agent.py`. The same run on a real model is
`experiments/baseline.toml` (see [Experiments](#experiments)).

### The curve — `task_pass_rate` over the same suite hash

| pass | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| memory attached | 0.50 | 0.50 | 0.67 | 0.67 | 1.00 | 1.00 |
| detached (ablation) | 0.50 | 0.50 | 0.50 | 0.50 | 0.50 | 0.50 |

What moved it: the first consolidation (after pass 2) admitted D-0001
(*errors that wrap a failed tool call carry the underlying cause*) and
D-0002 (*under a call budget, independent calls are issued as one batched
call*) from two independent observations each. Passes 3–4 applied both;
the budget task passed, the faulted HTTP tasks named their cause and still
failed. The second consolidation read that as a payload fault — D-0001
recalled, applied, and the oracle still flat — and admitted D-0003 (*a
transient tool failure is retried once before it is reported, and the report
carries the cause*), superseding D-0001. Passes 5–6 pass every task.

### Acceptance, row by row

| Row | Holds | Evidence |
|---|---|---|
| 1. Curve, both runs, same suite hash | yes | the table above; `store/sessions/S-0001…S-0012.json`, each with its Weave evaluation URI |
| 2. One full chain observation → decision → rule | partly | observation → decision → successor decision exists (`hgi lineage D-0003`: `O-0001 → D-0001 → D-0003`), each admission's ledger entry, attack and verdict joinable to Weave call URIs; the rule tier is not instantiated in this roster |
| 3. One retirement on telemetry | yes | D-0001 superseded by D-0003; the nominating evidence is the credit table on K-0002 (applied ÷ considered 1.0, `task_pass_rate` on its applied tasks 0.0 → 0.0) and steer T-0001 |
| 4. Dispositions complete; no fire owed to the working pass undischarged | yes | every consulted record in every attached pass has a `U-` record; `store/index/fires.json` is empty |
| 5. Calibration over four settled beliefs | no | the belief store is not instantiated in this roster |
| 6. Floor green; projections equal regeneration | yes | `hgi lint` is green with seven warnings, all `genesis-anchor`: the seven genesis articles passed three consolidation passes without earning an anchor and are due for eviction or anchoring |
| 7. Matrix populated: a steer cell and a system-catches cell | yes | `store/index/matrix.json`: one event in `system-misses/oracle-catches` (T-0001), six in `system-catches/none-catches` (applied dispositions on passing tasks) |
| 8. Roles separate on every ledger entry | yes | H-0001…H-0003 carry a consolidator, an examiner and an adjudicator call, three distinct Weave calls with distinct `hgi.role` attributes |

### What the demonstration does not show

Transfer to a second task family; behaviour under a model swap; the lens
telemetry; a rule enrolling or a floor growing; a belief settling; anything
about rates — every count is a floor from one run. And, because the frozen
model was the stub, nothing about whether a model conditioned on these
records would apply them.

## Running

```bash
uv sync
cp .env.example .env   # fill in the inference endpoint; leave HGI_WEAVE_PROJECT empty to run untraced
uv run hgi --help
```

Every `hgi` command reads `./.env` into its environment before it runs, and
so does the dashboard; `$HGI_ENV_FILE` names another file. A variable
already exported wins over the file, and a variable left blank in the file
reads as unset — which is how a surface is turned off: no inference endpoint
is the stub model, no `HGI_WEAVE_PROJECT` is an untraced run.

Without an inference endpoint the frozen model is replaced by a
deterministic stub, so the whole loop — boot, evaluate, close, consolidate —
runs offline and the acceptance tests run under `uv run pytest`.

## Commands

```
hgi boot        --session S-nnnn --pass n   # assemble context; print the consultation plan
hgi evaluate    --session S-nnnn            # run the oracle; write facts; emit fires
hgi close       --session S-nnnn            # dispositions, observations, steers, proposals, session record
hgi consolidate                             # the backward pass over the ledgers
hgi lint                                    # the floor
hgi index                                   # regenerate projections
hgi lineage     D-0007                      # the path query over the lineage DAG
```

Every command that writes ends in a commit whose message names the record
ids it admitted, flipped or retired. `./demo.sh` runs the whole
demonstration; `uv run marimo run dashboard.py` opens the projection surface
and the escalation queue; `uv run hgi mirror` publishes the ledgers to Weave
for the analyst.

## Experiments

An experiment file fixes every per-run decision outside the run: the models
it may use, which role runs on which, how many rounds and how many passes a
round holds (the consolidation cadence, written into the arm's bars),
whether the memory is attached or detached, any bar overridden, and how many
tasks the oracle evaluates at once. `hgi experiment run` gives each arm a
fresh store under `runs/<experiment>/<arm>/`, in a git repository of its own,
seeds it priced for the arm's pass model, and drives the same commands
`demo.sh` drives through the command surface; `arm.json` beside the store
records what the arm resolved to and its curve. The format is documented in
`hgi/experiment.py`.

```
hgi experiment show   experiments/baseline.toml     # every arm's resolved plan; nothing touched
hgi experiment run    experiments/baseline.toml     # every arm, or --arm <name> (repeatable); --force reruns
hgi experiment report experiments/baseline.toml     # the curves, read back from the arm stores
hgi experiment models                                # the ids the endpoint serves (W&B Inference by default)
```

| File | Arms | Question |
|---|---|---|
| `experiments/smoke.toml` | stub, attached and detached, 1 round × 2 | does the runner close the loop; the tests run it |
| `experiments/baseline.toml` | `openai/gpt-oss-120b`, attached and detached, 3 × 2 | the § 14 run on a real frozen model |
| `experiments/model-sweep.toml` | `gpt-oss-20b`, `gpt-oss-120b`, `Qwen3.6-35B-A3B`, each attached and detached, plus the roles split: the small model acts, the large one consolidates, examines and adjudicates | behaviour under a model swap (§ 14.4); whether separation of powers lets a weak actor learn from a strong judge |
| `experiments/cadence.toml` | `gpt-oss-120b` attached, consolidating every 1, 2 and 3 passes over six | how often to consolidate |

The shipped files run on W&B Inference (`https://api.inference.wandb.ai/v1`):
the key is `$WANDB_API_KEY` or the netrc entry `wandb login` wrote, and the
endpoint refuses a request with no `entity/project` to attribute usage to, so
`WANDB_ENTITY` must be set and the experiment names its Weave project. A
CoreWeave endpoint is a model entry with its own `base_url` and
`api_key_env`. Arms of one experiment trace into one Weave project, each call
carrying `hgi.experiment` and `hgi.arm`, each evaluation named by its arm.
The dashboard's store picker lists every arm; choosing one shows its
projections, its escalation queue and every arm of its experiment on one
chart, refreshing while the arm runs.

### The baseline on `openai/gpt-oss-120b`

Run on 2026-09-12 over W&B Inference, six passes attached and six detached,
consolidation every two passes, traced to
[`slavazinevich-worldvue/hgi-experiments`](https://wandb.ai/slavazinevich-worldvue/hgi-experiments/weave):

| pass | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| memory attached | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| detached (ablation) | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |

The honest reading: this suite is saturated for this model. gpt-oss-120b
retries a transient 502 unprompted, batches the budgeted shell calls and
names causes, so every lesson the stub demonstration learned is behaviour
the model already has, and the store has nothing to teach it. The attached
run filed eight observations (every one a recovered transient fault) and
admitted nothing: the consolidator's drafts were refused at the floor. A
separation needs either a world with faults the model does not already
handle or a model that does not already handle them; both are one arm in
an experiment file. An earlier run of the same arms, before the role
requests stated their reply shapes, scored 0.67–0.83 on both curves with two
tasks failing on a double-wrapped result and no observation filed; that run
is recorded in `carry-forward.md`, not here, because its numbers measured
the contract and not the model.

## Tests

```bash
uv run pytest
```

The tests are the slice acceptance bars of spec § 13: the floor's named
refusals and the committer (slice 0), facts, watches and fires (slice 1),
two passes chained through the store (slice 2), admit, decline, escalate,
the human queue, verdict authority and role separation on the ledger
(slice 3), and the retirement leg.
