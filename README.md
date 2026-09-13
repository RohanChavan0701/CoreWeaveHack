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
| registry | closed vocabularies, ports, bars, the constitution cap, the lens register, id counters | `store/registry/` |
| index | regenerated projections; never hand-edited | `store/index/` |

Traces and facts are not directories. They live in the oracle and are
referenced by anchor.

The lens register is the composition surface: each lens is a typed question
with its counterfactual, priced per model, hosted at boot, at close, or in the
examiner's dispatch. Its warrant is effect evidence derived at consolidation
from the products that reached a consumer — an observation promoted, a
contradiction settled, a claim upheld, a steer citing it — and its lifecycle
is the crystallization law: a lens whose product stops varying, or a seed no
consumer ever took from, is nominated to the adjudicator and retired on
`moot`. The examiner's four attack angles are lenses too, walked one context
per angle.

### The hypothesis ledger, by species

Every entry carries a proposer, a contradiction source and an adjudicator,
three distinct parties; the lint proves the separation on every line.

| Species | Written by | Contradicted by | Consumed by |
|---|---|---|---|
| attack | the consolidator's nomination, through the examiner fan | the examiner, one lens per context | the committer, on the adjudicator's verdict |
| reality | every observation group at the bar, before nomination | the oracle's rows the observations anchor | the noise filter: an irreducible group is dismissed, a reducible one nominated |
| currency | a revisit fire, a rotted anchor, the retirement ratio, a genesis anchor, a lens at a door, a port's miss stream, a pass's close-time contradiction | the oracle: the fire, the ratio, the instance, the pass's reading | the backward pass: a status or premise flip, a lens retired, a port widened |
| coding | an escape recurring across independent occasions | the blind coder, the candidate withheld | the vocabulary review: a term minted or declined |
| collision, forecast | nothing yet: the species are declared with their verdict vocabularies and no writer — the collision species needs an independent deriver, the forecast species the belief store | — | — |

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
| 6. Floor green; projections equal regeneration | yes | `hgi lint` is green with fifteen warnings, all `genesis-anchor`: the seven genesis articles and the eight genesis lenses passed three consolidation passes without earning an anchor and are due for eviction, retirement or anchoring; every counterfactual's anchor resolves |
| 7. Matrix populated: a steer cell and a system-catches cell | yes | `store/index/matrix.json`: one event in `system-misses/oracle-catches` (T-0001), six in `system-catches/none-catches` (applied dispositions on passing tasks); the true-miss cell is empty because passes 1 and 2 filed an observation from every failed row — a floor, not a clean bill |
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
hgi price       --model <id>                # the size of a model swap over the conditioning records
hgi lens-battery                            # the lens battery and the seeded controls; lens telemetry and index/controls.json
hgi lineage     D-0007                      # the admitting commit, and the path query over the lineage DAG
hgi suite       show | tasks | fetch <fam>  # the task suite in scope; transcribe a dataset family
hgi experiment  evolution experiments/x.toml # a stream experiment's evolution log, per arm and paired
hgi roles       try <request> --store <arm> # one role request against a copy of a store; how the reply parsed
```

Every command that writes ends in a commit whose message names the record
ids it admitted, flipped or retired, which is what makes the admitting
commit derivable: a record carries no hash of the commit that admitted it,
so `hgi lineage` reads it back as the oldest commit naming the id.
`./demo.sh` runs the whole demonstration; `uv run marimo run dashboard.py`
opens the projection surface and the escalation queue; `uv run hgi mirror`
publishes the ledgers to Weave for the analyst.

Every lens, article and accepted decision records the frozen model its text
was authored against, and a model swap re-prices all of them in both
directions. `hgi price` names what a swap costs; `hgi price --restamp` moves
the stamp without claiming the text moved with it, keeping
`priced_for.authored_for` at the model that authored it, so the
`model-pricing` check goes on warning until the text is re-authored.

## The backward pass

`hgi consolidate` runs every *k* passes and on any fire owed to it. Each leg
is a nominator; every verdict is the adjudicator's, in its own context, and
the committer alone writes. In order:

| Leg | Nominates on | Executes as |
|---|---|---|
| triage | every observation group at the independence bar, with the rows its anchors name | the adjudicator classifies the recurrence `reducible` (a duty the loop missed) or `irreducible` (nothing a record could have prevented) on a `reality` entry; an irreducible group is dismissed with a pointer to the entry and leaves the brief before any slot can update on it |
| nominations | the brief: observations grouped by the blind coder's shapes under the independence bar; `precision` (fired-but-not-applicable dominating a record's considered count at the bar `precision.not_applicable_over_considered_above`, with the dispositions' notes from independent passes → counterfactual-edit growing `not_this` by the presentations they name); `fusion` (dispositions bimodal across matched sub-shapes → split); `convergence` (identical hooks applied together → fold); `structural_zero` (a record no registered hook reaches → hook-edit); `recall` (a record the boot lens probed for unconsulted, or a steer indicting activation → hook-edit re-keying on what was presented) | a draft per nomination through attack and verdict; a `hook-edit` or `counterfactual-edit` is a successor derived from the one record it supersedes; a leaf names `split_from`, a fold `folded_from`, and admission writes the DAG move with reciprocal pointers; a nomination at a rung this roster has no operator for (`adoption-row`, `rule-enrollment`, `floor`, `article`) is carried as a decision — the cheapest available home — with the rung it meant recorded on the nomination and stamped on the admitted record as `admission.displaced_from`, so a later tier can re-home it |
| attack | the draft, verbatim, after the code's two readings: the distinct-session count of its evidence against the bar (`warrant:independence`, the lint's `independence` floor check, which the committer refuses on) and the direction of its revisit watch (`warrant:watch-direction`: a watch that fires on success is dropped from the draft, which is admitted unwatched, the drop recorded on the claim) — both join the attack first, with no lens and no call | the examiner fan: one call per live examiner-hosted lens (premise kill, abstraction; L-0005 and L-0008 are seeded retired, their questions crystallized into the code's readings), each contributing only the claims of its own class, an examiner claim on a mechanical class that contradicts the code's reading discarded; a landed `payload:abstraction` with no premise kill beside it sends the draft back to the consolidator once to promote the payload to the transferable shape with the instances kept as anchors, and the abstraction angle is walked again over the promoted draft; the adjudicator, never an angle, joins them |
| verdict | the draft the attack was walked over, the attack, the oracle's evidence, the bars | one token from the closed vocabulary: `admit`; `admit-amended(<amendment>)`, the committer admitting the amended payload; `decline(<why>)` on an upheld premise kill only — a decline with no landed `premise:` claim is overridden to an admit, amended where an amendment was offered, the attack still named on the entry (`survived-with-attack-named`) and the override on its outcome; `defer(<until>)`; `escalate(<why>)`. The floor runs before any admission |
| deferrals | a `defer(<until>)` verdict | the condition becomes a latch on the draft — a watch predicate the oracle's next runs fire, or passes to wait — and the fire, owed to the backward pass, re-adjudicates the draft in fresh contexts |
| fires owed | revisit latches whose predicate held; deferral latches | a decision's by a currency verdict on its warrant; a draft's by re-adjudication; the disposition and any flip land in one commit. A fire owed to the working pass instead is discharged by that pass at close, or the close is refused |
| pending contradictions | a `currency` entry a pass filed at close (the close lens named a premise or hook the pass made false), still pending | the adjudicator re-checks the warrant against the finding; the verdict lands on a new entry citing the pending one, and a `reversed` flips the premise |
| credit | the task-level credit table, each fraction with the counts it is computed from | oracle-attributed steers, credit assigned by the adjudicator |
| retirement | applied ÷ considered under the record's retirement guard over the window; or a record accepted before the window opened that no pass considered across the whole of it — the domain no longer entered | mootness by the adjudicator's killer-item check, through the same `currency` request with the window's evidence; a never-considered record is kept unless its `moot_when` condition is met, and nothing retires by count alone |
| genesis anchoring | a seed article with no anchor | the consolidator names an instance from the ledgers, the adjudicator says whether it exemplifies the article, the committer appends the anchor; past the deadline in the bars an article still unanchored is evicted |
| lenses | a lens's products that reached a consumer; a seed lens unanchored past the deadline; a product that stopped varying over the review window | anchors are derived and appended to the lens's warrant; a lens at a door — genesis-deadline or variance-collapse — goes to the adjudicator, and `moot` retires it (kept in the register as evidence, walked by nothing) |
| vocabulary | the same `other(<what>)` from independent occasions — a pass's work-shape, a latch's key-space, a species' verdict | revision routing first reads the pile against the axis's members: a missing peer or a partition of one member is horizontal and proceeds; a distinction that cross-cuts several members is vertical — the axis conflated two questions — and is surfaced, never minted. Then the blind coder recodes the presentations with the candidate withheld, the adjudicator admits or declines, the registry grows in place |
| ports | a latch type admitted off its port declaration on a warrant by independent records | the adjudicator admits or declines widening the mark from `forbidden` to `optional`; the port table is corrected in place |
| propagation | a wiring latch whose neighbour left the status it last saw — a tombstone's successor, a warrant's cited record | a mechanical check in the same commit; a rotted anchor goes to the adjudicator as a currency question |

The projections under `store/index/` show each leg's live state: `hooks`,
`summaries` (each record's watch, or `unwatched` when no world-state latch
can send its warrant back), `triggers`, `deferred`, `wiring`, `fires`,
`competence` (applied, not-applicable, guard-failed and off-map counts per
record over the window, and the ratio), `fusion`, `convergence`,
`structural_zero`, `recall` (the should-have-fired stream: boot-lens probes
and activation steers per record), `attacker` (attacker precision per
angle, the landings the adjudicator upheld or overruled, and the
should-have-been-caught-by stream — every count a floor), `lineage`,
`matrix` (steers, fires and applied dispositions by cell, and in the
`system-misses/none-catches` cell the rows nothing caught: a task failed in
a closed attached pass that consulted no record and filed no observation
from the row, keyed `session/task` — a floor, since the store cannot see a
miss the world has not yet voted on). One more file sits beside them and is
not a projection: `controls.json`, the blind coder's seeded-control
telemetry, written by `hgi lens-battery` and regenerated by nothing.

### Telemetry

Every instrument reports a floor, never a rate. `hgi lens-battery` runs the
three that are scored as traced Weave evaluations, each item walked in its
own context, and writes what they find:

| Instrument | Plants | Scores | Written to |
|---|---|---|---|
| the lens battery | two decoys and two genuine signals per close lens (L-0003, L-0004) | `decoy_rejection` (filed nothing for the plant) and `signal_caught`; `answer_variance` across the battery | `telemetry` on each close lens in `store/registry/lenses.json` |
| the examiner control | per live examiner-hosted lens (L-0006, L-0007), a draft carrying a fault of that lens's class and a plausible draft with none, attacked through the fan one angle at a time under a fixed evidence pack | the landing on the fault as `signal_caught`, the non-landing on the clean draft as `decoy_rejection` | `telemetry` on each examiner lens in the same register |
| the coder control | an observation of a known work-shape, and one that fits no term | whether the blind coder returns the term, and whether it escapes with `other(<what>)` on the misfit | `store/index/controls.json` |

The rest are projections: the detection matrix (with the true-miss floor),
`competence` (with the not-applicable count), `attacker`, `recall` and
`structural_zero` above. The committed demonstration store carries the
battery and the controls at `design-stage` and no `controls.json`: on the
stub every control passes by the stub's own keyword rules, which measures
the mechanism and not a model, so the run that records telemetry is left to
a traced one on a real endpoint.

## The world

The suite the loop is judged on is composed from task families under one
fault profile, and pinned by a hash over every task's presentation, its
world (the files and routes it runs in) and the profile (spec § 14.1). A
family is hand-written or transcribed once from a public dataset into
`suite/data/`, so a run needs no network:

| Family | Tasks | Source | What it grades |
|---|---|---|---|
| `genesis` | 6 | hand-written | the § 14 demonstration: HTTP faults, a shell budget, a file report, a schema |
| `conventions` | 10 | hand-written | facts of this world a model meets on first contact: files with no trailing newline (`wc -l` undercounts), a paging API, an API moved under `/v2`, quoted CSV commas, a byte order mark — each proven to fail naively and pass when known |
| `mbpp` | 257 | [google-research-datasets/mbpp](https://huggingface.co/datasets/google-research-datasets/mbpp), sanitized test split, CC-BY-4.0 | write `solution.py`, run `tests.py` under three shell calls; the dataset's own asserts are the hidden check |
| `tables` | 100 | [TableBench](https://huggingface.co/datasets/Multilingual-Multimodal-NLP/TableBench), Apache-2.0, the scalar-answer rows | one question over `table.csv`, graded by a normalizer with tolerance |
| `api` | 100 | the same TableBench rows, odd positions | the same questions through a paged JSON API under a budget of pages plus two |
| `transfer` | 6 | hand-written | the `conventions` conventions re-dressed — the same no-trailing-newline files, paging API and `/v2` move worn as different file names, a different API surface and different endpoints — so a record whose hook reads the convention scores here and one that memorised a path or a filename does not |
| `curriculum` | 84 | generated (`suite/families/curriculum.py`) | seven lessons of the world in twelve clothes each — the five `conventions` lessons, an export that ends with a `TOTAL` row, a route under `/secure` that answers 401 until the token in `token.txt` is passed — each clothing a different instance from a seeded generator, disjoint from the hand-written families' names and routes, budgeted with one call to spare for discovering the convention; the pool a stream experiment deals from |
| `curriculum-strict` | 84 | generated, the same clothes | the same tasks budgeted at exactly the knowing policy's calls, so the convention costs a call the budget does not hold: only a pass that already knows it — from the store, or from the model — stays within budget |

### Lessons

A task that turns on a convention names it as its **lesson**
(`suite/lessons.py`), and every lesson is tiered by how its failure shows
in the trace: *loud* (the tool error names the convention — the 410 naming
`/v2`, the 401 naming the token file, the parse error on the byte order
mark), *visible* (the failure is silent but the convention is in the tool
output the pass read — a `next` field on the page it stopped at, a quoted
comma or a footer row in the file it counted), *invisible* (nothing in the
trace shows it — a file with no trailing newline reads the same as one
with). Every task in a lesson family carries its naive first-contact policy
as its scripted policy, so the **naive outcome** — the answer or the error
a policy that does not know the lesson produces — is derived by running it
against a fault-free world. A failed row whose result equals the naive
outcome, or whose error (or any tool error in its trace) is of the naive
error's class, is a **naive-shape** failure: the lesson missed the way first
contact misses it, decided by the task's own construction and no judge.

### Quality

Correctness saturates where a model passes a lesson at first contact, and
the memory's value is then the cost, not the pass: a pass that knows a
convention spends the knowing policy's calls, and its method carries; one
that discovers it spends the discovery, and its method may fit the
instance. Every curriculum task declares the knowing policy's calls
(`Task.knowing`) and carries a **metamorphic twin** (`Task.twin`) — the
same names, columns and routes over different data, from a second seed,
with its own gold — and every row records its shell commands and model
turns. Three scorers grade a solution's quality beside its correctness,
each a success rate in `[0, 1]` like the rest:

| Series | Grades | Evaluable on |
|---|---|---|
| `solution_economy` | the knowing policy's calls over the calls the pass spent on budgeted tools; zero on a failed row | a task with a knowing floor |
| `turn_economy` | the same over model turns, the floor being one turn per knowing call and one to answer | a task with a knowing floor and a row that records turns |
| `method_transfer` | the pass's last shell command replayed in the twin world: its last line of output names the twin's gold, or not | a passed row of a task with a twin whose pass issued a shell command |

A method that transfers reads the convention; one that fits the instance —
or a pass that read the file and computed in its head, leaving no
replayable command — does not.

The fault profile says how many leading HTTP calls of a faulted task fail,
whether HTTP calls are budgeted, and whether shell output truncates. An
experiment file carries the suite as `[suite]` (families, a seeded sample
size, the profile), deep-merged per arm; a hand-run names a TOML with the
same table in `$HGI_SUITE`. `hgi suite show` prints the resolved suite and
its hash. The deterministic stub runs only the families that carry scripted
policies (`genesis`, and `conventions` and `transfer` naively); every other
family fails on it honestly.

## Experiments

An experiment file fixes every per-run decision outside the run: the models
it may use, which role runs on which, how many rounds and how many passes a
round holds (the consolidation cadence, written into the arm's bars),
whether the memory is attached or detached, any bar overridden, which suite
it runs on, and how many tasks the oracle evaluates at once. `hgi experiment run` gives each arm a
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
| `experiments/probe.toml` | `gpt-oss-120b` attached, 2 × 2, the hand-written families | every role request on a real model end to end; the reply log is the evidence |
| `experiments/world.toml` | `gpt-oss-120b` and `gpt-oss-20b` attached, `gpt-oss-120b` detached, the split roles; 52 tasks from five families, first two HTTP calls faulted | a world with conventions the model cannot already know: does the attached curve separate |
| `experiments/transfer.toml` | `gpt-oss-120b` attached and detached, `gpt-oss-20b` attached; `genesis`, `conventions`, `api` and `transfer`, first two HTTP calls faulted | a convention held twice in different clothes: does a record admitted on one family score on the same convention re-dressed as another |
| `experiments/stream.toml` | `gpt-oss-120b` attached and detached, `gpt-oss-20b` attached, on the `curriculum` pool; `gpt-oss-120b` attached and detached on `curriculum-strict`; ten batches of eight, consolidation every two, batches 1 and 2 revisited | the stream: first-sight performance on unseen tasks as the store grows, paired per batch and per lesson, with the same-shape recurrence per lesson; on the strict pool, whether the memory saves the discovery call |
| `experiments/economy.toml` | `gpt-oss-120b` attached and detached on the `curriculum` pool, ten batches of eight, a different deal | the stream graded on quality: economy of calls and turns, and method transfer to the twin world, where correctness saturates |
| `experiments/stream-probe.toml` | `gpt-oss-120b` attached and detached, two batches of five | a stream arm end to end on the endpoint |
| `experiments/stream-smoke.toml` | stub, attached and detached, four batches of four | the stream runner end to end offline; the tests run it |

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

### The stream

A suite experiment runs the same tasks every pass, so its curve measures
whether the store learned *those* tasks. A **stream** experiment
(`suite/stream.py`, the `[stream]` table of an arm) deals a pool into
batches balanced over lessons and meets a new batch every pass: pass *k*
boots with what the store holds, evaluates batch *k* **at first sight** —
nothing in the store was learned on those tasks — closes on it, and
consolidates at each round's end. Every batch is a validation set once and
a training set afterwards, and the curve is first-sight performance on
unseen tasks as the store grows: the shape a knowledge base is asked to
improve, where the work that arrives is always new and the conventions
recur. A detached arm draws the same batches with no store, so the
comparison is paired per batch and per lesson; `revisit` names batches the
attached arm meets again after the stream, which measures retention on
seen tasks against transfer to unseen ones.

The **evolution log** (`hgi/evolution.py`) is derived from the arm's store
after the run and written beside it as `evolution.json` and `evolution.md`,
with the experiment's paired report at `runs/<experiment>/evolution.md`
(`hgi experiment evolution`): per pass, each row's symptom (`pass`,
`naive`, `wrong`, `error:<class>`), the records in context and which
lessons their text mentions (a keyword heuristic, logged as one), the
observations filed and what the consolidation after the pass admitted,
declined, retired or dismissed; per lesson, the first-sight series as a
grid of symbols, and the naive-shape failures before and after the first
pass that had a record mentioning the lesson in context — the same-shape
recurrence the memory exists to stop; and beside every pass rate the
quality means, `economy / turns / transfer` (economy derived from the
row's call counts and the task's floor, so it reads on runs scored before
the series existed). Every count is a floor from one run.

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

### The world on `openai/gpt-oss-120b`

`experiments/world.toml`, run on 2026-09-12 over W&B Inference: 52 tasks
(twelve of each transcribed family, all of `genesis` and `conventions`),
the first two HTTP calls of a faulted task failing, six passes attached,
consolidation every two passes, traced to
[`slavazinevich-worldvue/hgi-experiments`](https://wandb.ai/slavazinevich-worldvue/hgi-experiments/weave):

| pass | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| memory attached | 0.81 | 0.73 | 0.75 | 0.90 | 0.83 | 0.83 |
| records in context | none | none | D-0002 | D-0002 | D-0002, D-0003 | D-0002, D-0003 |

The detached arm was not run to completion: a detached pass has no boot,
no close and no store, so its passes are draws of one evaluation, and pass
1 of the attached arm — an empty store, nothing consulted, the constitution
the only conditioning — is that draw. The runner now draws a detached
arm's passes concurrently for the same reason.

What the attached arm did: every failed row filed one anchored observation
(60 over six passes); the first consolidation grouped them into twelve
shapes, nominated four, declined two on the examiner's premise attacks and
admitted D-0001 (*tool outputs conform to the schema*) and D-0002 (*calls
stop at the HTTP budget*); the second admitted D-0003, D-0005 and D-0004 —
the last by adopting the pass's own close-time proposal of a retry
decision, the pre-admission tier working end to end — and expired one
unadopted proposal; the third admitted D-0006 and retired D-0001, D-0004 and
D-0005 as moot on their own telemetry, discharging three fires. Passes 3–6
consulted D-0002 and D-0003 and applied them; the lint is green with the
seven genesis-anchor warnings.

The honest reading: the curve moved within the run's own noise. Passes 3
and 4 ran with the same record in context and scored 0.75 and 0.90; the
same task flips between passes with nothing in context changed
(`api/21f6f753` passes, fails twice, passes twice; `mbpp/430` fails, fails,
passes three times, fails), and the decisions admitted were the loop's
tautologies —
schema, budget, argument validation — not the world's conventions. The two
conventions that failed every pass (`log_lines`, a budget of one shell call
over files with no trailing newline; `versioned_status`, an API moved under
`/v2` behind two faulted calls) never earned a record: their observations
were coded into shapes the consolidator did not nominate on, or nominated
and declined. The record that would have taught them is one the ladder's
`hook-edit` and `counterfactual-edit` rungs would carry, and those rungs
have no operator yet (carry-forward, decision 21). What the run does show
is the mechanism at breadth on a real model: observations from every
failure, grouping, four-role adjudication with declines, adoption, expiry,
fires discharged and retirement — each of which the six-task baseline
could not exercise.

## Tests

```bash
uv run pytest
```

The tests are the slice acceptance bars of spec § 13: the floor's named
refusals and the committer (slice 0), facts, watches and fires (slice 1),
two passes chained through the store (slice 2), admit, decline, escalate,
the human queue, verdict authority and role separation on the ledger
(slice 3), the retirement leg, and the backward pass's other legs: split
and fold on the lineage DAG, the structural-zero audit and the edit rungs,
deferral latches and propagation, genesis anchoring, and vocabulary growth;
and the doctrine's disciplines over them: the noise filter, the examiner fan,
the code's readings of independence and watch direction, the amend-only
abstraction claim and the decline override, attacker precision, the recall stream, the lens lifecycle, revision routing,
the port miss stream, the key-space floor, the refusal of a rung with no
operator, the true-miss floor, the precision slot, the second retirement
key, anchor resolution, the late steer sweep, the antichain flag, and the
seeded controls.
