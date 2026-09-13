# Seed store: the `world` suite's transcribed families

What a mature store for `experiments/world.toml` holds *beyond* the conventions
seed — the decisions the three non-hand-written families need: `mbpp`
(write-and-run coding graded by the dataset's own asserts,
`suite/families/mbpp.py`), `tables` (TableBench through a CSV in the working
directory, `suite/families/tables.py`) and `api` (the same TableBench questions
through a paged HTTP API, `suite/families/api.py`). The `genesis` and
`conventions` families and the seven lessons of `suite/lessons.py` are the
conventions seed's; nothing here restates them (see *What this seed reuses*).

Seven decisions, `decisions/D-0001.json … D-0007.json`, no `vocabulary.json`:
every latch keys on terms a fresh `hgi genesis` registers.

## The families' presentations

The consultation latches key on the work-shape tuple each family presents
(`Task.shapes`), which is what the boot classifies:

| family | `Task.shapes` | budget | schema | hidden check |
|---|---|---|---|---|
| `mbpp` | `file-tool shell-tool test-failure-triage tool-budget` | 3 shell calls | `result: string` | `python3 tests.py` exits zero in the working directory |
| `tables` | `file-tool shell-tool tool-budget` | 3 shell calls | `result: number \| string` | `matches()` against the gold — numbers within 0.011 absolute or 1% relative, strings casefolded |
| `api` | `http-tool error-wrapping tool-budget` | pages + 2 http calls; shell unbudgeted | `result: number \| string` | the same `matches()` |

The boot classifies the whole suite's presentations in one step and every
record its terms reach enters every task's consultation plan, so all seven
records are in context on every row. Per-row selection is done by each
decision's opening clause ("on a task whose working directory holds
tests.py", "on a question over table.csv", "when a GET fails with a cause
marked transient") and by its `not_this`, which name the other two families
outright.

## The recurring failure shapes

Tiered as `suite/lessons.py` tiers a lesson: *loud* when a tool error names
it, *visible* when it is in tool output the pass already read, *invisible*
when nothing in the trace shows it.

### `mbpp` — write-and-run

- **Answered without a run** (invisible). The prose states the problem; the
  asserts fix the function's *name*, arity and return type
  (`sort_counter` returns a list of tuples, `add_pairwise` a tuple, not a
  list). A solution never run against `tests.py` fails the hidden rerun on a
  detail the prose did not state. → D-0001.
- **Budget spent writing** (visible). `solution.py` written through a shell
  heredoc costs one of three budgeted calls; the file tool is free
  (`suite/tools.py:101`). → D-0001.
- **Triage that changes nothing** (loud). A non-zero exit raises with the
  first 200 characters of stderr as the cause (`suite/tools.py:93`) — the
  traceback head naming the failing assert. Rerunning unchanged code shows
  the same assert and the third run is refused. `mbpp/430`
  (`parabola_directrix(5,3,2) == -198`) is the world run's flipping row: the
  assert *is* the formula's specification. → D-0002.
- **A recovered failure reported as the error** (invisible). Any non-null
  `error` on the envelope fails the row before the hidden check runs
  (`suite/scorers.py:44`); a pass that rewrote, saw exit zero, and still
  reported the earlier failure fails a task it solved. → D-0002.

### `tables` — TableBench through a file

- **Exploration by call** (visible). `head`, then `awk -F,`, then a sum: three
  calls of exploration, none left for the fix. The file tool is unbudgeted
  and the table is a few kilobytes: read it whole, then one script. → D-0003.
- **Split on commas** (visible; the conventions seed's `field-quoted`
  lesson in another coat). The CSV is written by Python's `csv` writer
  (`suite/families/tables.py:115`); a cell holding `1,234` is quoted and an
  `awk -F,` shifts every column after it. → D-0003 (read with the `csv`
  module), and the conventions seed's `field-quoted` record.
- **Cells are strings** (visible). Across the pinned file: 653 cells with a
  thousands comma, 166 with a percent sign, 189 dashes or blanks.
  `float('1,234')` raises and spends the call; a dash read as 0 pulls a mean
  down; `'6t'` and `'1990 - 91'` compared as text sort wrong. → D-0004.
- **The wrong scalar shape** (invisible). `'1,234 MW'`, `[1234]`, an average
  rounded per row, `'Jamaica'` where the gold spells `'Jamaica (JAM)'`: the
  normalizer (`suite/families/tables.py:89`) reads a number through a percent
  sign and separators, never through a unit or a list, and compares text as
  the cell spells it. → D-0005.
- **Computed in the head** (invisible). Forty rows of strings summed without
  a script; the instruction asks for the shell (`suite/families/tables.py:61`).
  → D-0003.

### `api` — TableBench through a paged API

- **Abandoning the route at the second 502** (loud). Under the world's
  profile (`http_fault_calls = 2`, `experiments/world.toml:30`) a faulted task
  fails its first *two* calls, whatever the path (`suite/tools.py:72`). A pass
  that retries once and then reports the route down fails a task whose third
  call answers. Half the tasks fault (`http_fault_fraction = 0.5`). → D-0006.
- **Retrying what is not transient** (loud). A 404 retried twice is two calls
  the pages needed. → D-0006 (`not_this`).
- **Stopping before `next` is null** (visible). The conventions seed's
  `listing-paged` lesson; D-0007 keys on the same term and folds the walk into
  the budget arithmetic rather than restating the lesson.
- **Refetching** (visible). The description fetched twice to reread the
  columns, or a page fetched again after a failure elsewhere: the budget is
  exactly pages + 2 (`suite/families/api.py:28`) and the last page is refused.
  → D-0007.
- **Answering from a partial walk** (invisible). A total over all but the
  last page is wrong by one page and the 1% tolerance does not forgive it;
  the row fails on `task_pass_rate` and on `tool_budget_respected` both.
  → D-0007.
- **Columns lost** (visible). Pages carry rows only (`suite/families/api.py:50`);
  the header is the description's `columns`, aligned by position. → D-0007.
- **Cells and scalar shape** — as `tables`. → D-0004, D-0005 (both scoped to
  both families and keyed on `http-tool` as well as `shell-tool`).

## The decisions

| id | decision (one line) | keys on | excludes | stakes |
|---|---|---|---|---|
| D-0001 | Read `tests.py` first; take name, arity and return type from the asserts; write `solution.py` through the file tool as a plain module; one shell call on `python3 tests.py`; answer on exit zero with a string result and `error: null` | `file-tool shell-tool test-failure-triage tool-budget` | table questions; tasks with no `tests.py` | the hidden rerun fails on what the prose did not state; a heredoc spends the budget |
| D-0002 | On a non-zero exit read the assert the cause names and treat the asserts as the specification; rewrite and rerun, fold any probe into the rerun's call; never rerun unchanged code; a passing rerun is not an error; only the budget's last failing run is, reported with the `exited …` cause verbatim | `test-failure-triage shell-tool error-wrapping` | shell failures unrelated to the tests; a table script that raised | one of three calls per rerun; a recovered failure reported fails a solved row |
| D-0003 | Read `table.csv` whole through the (unbudgeted) file tool; one shell call on a single `python3 - <<'EOF'` script using the `csv` module that prints only the answer on its last line, written so it cannot raise; two calls in reserve; never `head`/`awk` by call, never split on commas | `file-tool shell-tool tool-budget` | coding tasks; tables behind the API | three calls; a raise costs one; a quoted comma shifts `awk` |
| D-0004 | Coerce every cell through one helper (strip whitespace, currency, percent, thousands separators; `None` on failure), aggregate over non-`None` only, compare seasons/ranks by their leading number, match text casefolded — in the script, not the head | `shell-tool http-tool file-tool` | coding tasks; the text cell the question names | `float('1,234')` raises; a dash as 0 or a percent as text is a wrong scalar past 1% |
| D-0005 | `result` is exactly one scalar: a JSON number for a quantity (count as integer, percent as bare number, average/difference to 2 decimals, totals unrounded, rounded once at the end), else the cell's text as the table spells it, code and suffix included; no unit, list, object or prose | `shell-tool http-tool file-tool output-schema` | coding tasks; questions wanting a list or a sentence | the normalizer reads neither `'1,234 MW'` nor `[1234]`; `'Jamaica'` ≠ `'Jamaica (JAM)'` |
| D-0006 | A transient 502 is retried on the same path at once and once more if the retry fails the same way — the leading calls fault by count, so the third answers; never switch paths, never retry a 404/410/budget refusal; count failed calls against the budget; a recovered failure is not the task's error | `http-tool tool-call-retry error-wrapping` | 404/410; budget refusals; a later failure on a route that answered | half the tasks fault two calls; giving up at two fails a task with room for three |
| D-0007 | Walk in a fixed order — description once, each page once following `next` to null, keeping rows; after page one compare pages remaining with calls remaining (failed calls counted); finish and compute over complete rows with the description's columns (unbudgeted shell), or, if it cannot fit, stop within the budget and report the tool's cause; never refetch | `http-tool tool-budget listing-paged` | tables in a file; listings under no budget | pages + 2 exactly; a refetch or a partial walk fails on pass rate and budget both |

Every decision carries a `revisit` latch on a scorer the oracle runs
(`task_pass_rate` below 0.6, `tool_budget_respected` below 0.8, or
`output_schema_valid` below 0.9, persistence 2) and the standard retirement
latch (applied-over-considered below 0.1 across 6 passes). Counterfactuals
and warrants anchor into `suite/families/*.py`, `suite/tools.py`,
`suite/faults.py` and `suite/scorers.py` by `path:line`, since a seed has no
observations.

## What this seed reuses from the conventions seed

Not duplicated here, because the `conventions`/`genesis` seed carries them
and a session-wide boot puts both seeds' records in context together:

- **`listing-paged`** ("page until `next` is null"): `api`'s walk is that
  lesson; D-0007 keys on the same registered term and adds only the budget
  arithmetic and the positional header. The conventions seed's paging record
  (its D-0002) describes a listing of `items` + `next`; the `api` pages carry
  `rows` + `next` with no header, so D-0007 is needed beside it, and its text
  states the walk in full if the conventions record is absent.
- **The transient retry** (the conventions seed's D-0008: retry the same
  path up to twice, never a 401/404/410/budget refusal): D-0006 is the `api`
  form of the same convention and co-applies with it — what it adds is the
  budget consequence (count the failed calls into the walk plan) and the
  exclusion of a later failure on a route that already answered. Injected
  together they are two records the pass disposes side by side, not a
  conflict.
- **Plan calls before the first one; spend none looking** (the conventions
  seed's D-0009): D-0003 is consistent with it — the look at `table.csv` goes
  through the unbudgeted file tool, never a shell `head`.
- **Error cause carried on a failed task** (the demonstration store's
  D-0001 shape): D-0002 and D-0007 *use* it — "report the cause the tool gave
  verbatim" — rather than restate it.
- **Output conforms to the declared schema** and **calls stop at the
  budget** — the two tautologies the world run admitted as its D-0001/D-0002.
  D-0005 and D-0007 are the family-specific forms with content the generic
  records lack (what "one scalar" means to `matches()`; what "the budget"
  buys on a paged walk).

## The `api` ceiling under the world's fault profile

A fact of the harness the seed does not paper over. `BUDGET_SLACK = 2` is
documented as "the description, and one transient failure recovered from"
(`suite/families/api.py:28`); the world profile faults **two** leading calls.
A faulted task's honest walk is therefore 2 failed calls + the description +
N pages = N + 3 calls against a budget of N + 2. In the world sample (twelve
`api` tasks, seed 0) five are faulted — `api/1c199a20` (5 pages),
`api/29227378` (2), `api/73cc123c` (3), `api/9294abdf` (1), `api/a5de47ae` (3)
— and none can be walked to the last page within budget by any policy that
fetches the description. The only way through is to skip the description and
start from the page route the family always uses; that is a memorised route
plus a header guessed from the question, and the seed deliberately does not
carry it (the authoring rule: generic across instances, no memorised routes).

So D-0007's guidance on those five rows is: after page one, see that the
calls left are one short, stop *within* the budget, and report the transient
failures and the budget as the cause. Expected series on those rows:
`task_pass_rate` 0, `tool_budget_respected` 1, `error_cause_present` 1 —
against the naive shape, which exceeds the budget, answers from partial rows,
and scores 0 on the first two with the third unevaluable-or-zero. The seeded
arm's ceiling on `api` is therefore 7/12, and the family's contribution to
the suite mean is capped at about 0.58 regardless of the store. (This is the
same shape as the world run's `versioned_status` in `conventions`: two
faulted calls under a budget that allowed one; carry-forward decision 64.)

## The compare/contrast expectation on `world`

`experiments/world.toml`: 52 tasks — all of `genesis` (6) and `conventions`
(10), twelve each of `mbpp`, `tables`, `api` (seed 0) — `http_fault_calls =
2`, three rounds of two passes, consolidation every two passes, scored on
`suite-v1`. The reference is the attached `gpt-oss-120b` arm of 2026-09-12
(README, *The world on gpt-oss-120b*):

| pass | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| `120b-attached`, `task_pass_rate` | 0.81 | 0.73 | 0.75 | 0.90 | 0.83 | 0.83 |
| records in context | none | none | D-0002 | D-0002 | D-0002, D-0003 | D-0002, D-0003 |

- **Detached** is the no-store draw: pass 1 of the attached arm (0.81) is
  that draw, and the runner now draws detached passes concurrently. Its
  per-family pattern is what the failure shapes above describe.
- **Attached from empty** reached its late-pass level (0.83–0.90) only by
  pass 4, and with the loop's tautologies in context rather than these
  conventions; the same task flips between passes with nothing in context
  changed (`api/21f6f753`, `mbpp/430`), so single passes are one draw each
  and the comparison is over the six-pass mean.
- **Seeded** (this store plus the conventions seed, injected before pass 1)
  should *start* near the attached arm's late-pass level and hold it flat:
  on `mbpp` and `tables` the seed removes the invisible failures (unrun
  solutions, unshaped scalars, unparsed cells) that a store learns slowly or
  never; on `api` it fixes the seven clean rows and converts the five faulted
  rows from budget-exceeded partial answers into within-budget caused errors.
  The series to read: `task_pass_rate` on `mbpp` and `tables` (expected at or
  above the attached arm's pass-4 level from pass 1), `tool_budget_respected`
  and `error_cause_present` on `api` (expected 1.0 on the faulted rows),
  `output_schema_valid` on `tables`/`api` (expected 1.0). `solution_economy`,
  `turn_economy` and `method_transfer` are unevaluable on these families (no
  knowing floor, no twin) and say nothing here.
- **What would falsify the seed**: a seeded pass 1 no better than 0.81 on
  `mbpp`+`tables` says the failures were not the shapes above but the
  model's arithmetic or reasoning, which no record fixes; a seeded `api`
  below 7/12 on the clean rows says D-0006/D-0007's walk is mis-specified.

## Validation

The store was validated in a scratch genesis store:

```
uv run hgi genesis --store <scratch>/store --no-commit
cp experiments/seeds/world/decisions/D-000*.json <scratch>/store/decisions/
# registry/ids.json: "D": 7
uv run hgi index --store <scratch>/store --no-commit
uv run hgi lint  --store <scratch>/store
```

Result: `lint: green — 0 failures, 0 warnings`. `hgi consult --terms` with
each family's shape tuple reaches that family's records first (most terms
matched), then the shared ones.

The injector path was run as the `120b-seeded` arm would run it —
`hgi.seeds.inject` with `conventions` then `world` into a fresh genesis
store, priced for `openai/gpt-oss-120b`: the world seed lands as
D-0010..D-0016 past the conventions seed's D-0001..D-0009, no terms added,
no warnings, and the combined store lints `green — 0 failures, 0 warnings`.
