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
| the frozen model | **CoreWeave inference endpoint** | one OpenAI-compatible client; every call records its model id; every lens records the model it was priced for |
| the consolidation analyst | **W&B ARIA** | reads the disposition and session ledgers mirrored to Weave as datasets and drafts the consolidation brief; its report URI is recorded on the consolidation session; it nominates, never verdicts |
| projections and the escalation surface | **marimo** | `dashboard.py` renders the index, the lineage DAG, the detection matrix and the escalation queue live from the store, and writes only through `hgi` commands |
| the blind second coder, the guard evaluator | **TypeSafe AI System1** | classifies observations against the registry's shape terms without the consolidator's candidate labels; falls back to a second, separately prompted frozen-model context when the vendor is not configured |

## The demonstration and its acceptance bar

The run of spec § 14 is in the store and in the Weave project
[`slavazinevich-worldvue/hgi`](https://wandb.ai/slavazinevich-worldvue/hgi/weave):
six passes with the store attached, six detached (same agent, same suite
hash, no boot or close), consolidation every two passes. The frozen model
for this run is the deterministic stub (no inference endpoint was
configured), so the curve shows the loop's mechanics closing, not a model
learning; the stub applies a record only by keyword, exactly as documented
in `suite/agent.py`.

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

## Tests

```bash
uv run pytest
```

The tests are the slice acceptance bars of spec § 13: the floor's named
refusals and the committer (slice 0), facts, watches and fires (slice 1),
two passes chained through the store (slice 2), admit, decline, escalate,
the human queue, verdict authority and role separation on the ledger
(slice 3), and the retirement leg.
