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
ids it admitted, flipped or retired.
