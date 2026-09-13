# Dataset and evaluation recommendation

## Recommendation

Use a **payments fee analyst** as the demo domain, built from **Adyen's DABstep** context and task format, with a small local held-out evaluator generated from the same public rules.

The demo question should be:

> Given a transaction, merchant, card scheme, and fee rules, calculate the applicable fee and explain which rule fields determined it.

The self-improvement claim should be a paired test:

1. The agent learns a rule from one fee case, such as how `null` fields act as wildcards or how a fee combines a fixed amount with a rate.
2. A look-alike case changes one condition, such as `is_credit`, `aci`, or domestic versus international routing.
3. The evaluator checks both the numeric fee and the selected rule IDs.
4. A broad learned rule that overcharges the counterexample is rejected; a scoped rule is admitted.

This gives the loop a concrete business domain, multi-step reasoning over tables and documentation, and an easy-to-explain failure story. DABstep's official context includes fee rules, merchant data, transaction data, and a manual defining fee semantics. Its manual states that null means “all possible values” and gives the fee equation `fixed_amount + rate * transaction_value / 10000` ([dataset context](https://huggingface.co/datasets/adyen/DABstep/tree/main/data/context)).

## What is available

| Candidate | Verified shape | Fit to this codebase | Decision |
|---|---|---|---|
| **DABstep** | Adyen payments domain; 450 main tasks; `dev` has 10 labeled tasks; CC-BY-4.0. Main task answers are blank in the public `all.jsonl`; the public dev file contains the answer field ([task files](https://huggingface.co/datasets/adyen/DABstep/tree/main/data/tasks), [dataset card](https://huggingface.co/datasets/adyen/DABstep/blob/main/README.md)). | Excellent story and world model. The local runner already supports file access, shell computation, tool budgets, hidden checks, and observations from failed rows. | **Use the context and dev questions, then add a small generated paired evaluator.** Do not claim that the public 450-task split is locally gradeable without access to the leaderboard's hidden answers. |
| **BIRD Mini-Dev, financial subset** | 500 text-to-SQL questions over 11 databases; the official card lists 32 questions for the Financial database and provides SQLite resources, evidence, SQL, and a gold SQL file. License is CC-BY-SA-4.0 ([dataset card](https://huggingface.co/datasets/birdsql/bird_mini_dev), [official repository](https://github.com/bird-bench/mini_dev)). | Very good mechanical fit: put a SQLite database in the task world, let the agent inspect schema and run SQL, then grade by executing the query. The 32 financial questions are enough for a small domain slice, but not enough for a statistically strong result by themselves. | **Best off-the-shelf evaluator.** Start with 8–12 financial questions and hold out a disjoint group by question template or database entity. |
| **LiveSQLBench Base-Lite SQLite** | 270 tasks across 18 end-user databases; its public release removes solution SQL, test cases, and external knowledge to reduce leakage. It ships evaluation scripts and uses SQLite ([official evaluation README](https://github.com/bird-bench/mini_dev/tree/main/live_sql_bench_sqlite)). | Strong evaluator design and better contamination story, but more adapter work and no obvious reason to prefer it for a payments-specific pitch. | Use later if the team wants a larger SQL benchmark after the demo works. |
| **TableBench (already wired)** | Scalar questions over compact tables; the local family currently pins 200 records and uses shell calculation with a tolerance-based hidden check. | Lowest integration cost, but it is broad table arithmetic and does not make the loop memorable as a domain product. | Keep as a smoke test or baseline, not the headline demo. |

## Why this matches the implementation

The task contract already separates the visible prompt and schema from the hidden world and check (`suite/tasks.py:Task.row`, `Task.world`, `Task.check`). A DABstep or BIRD task can therefore provide:

- documentation and a database or CSV in `Task.files`;
- a bounded `shell` or `read_file` tool path;
- a hidden checker that runs a reference calculation or SQLite query;
- task shapes that let a learned record match the domain convention instead of a filename.

The evaluator already writes one row per task and multiple scorer values. `hgi/evaluate.py:94-120` creates the dataset and captures the rows; `hgi/close.py:178-188` sends failed rows to the close lenses; and `hgi/consolidate.py:252-263` reconstructs evidence from the recorded rows and tool errors. This is enough to make a rejected fee rule visible in the trace.

The existing experiment runner evaluates the same suite on every pass (`hgi/experiment.py:279-286`). That is useful for measuring improvement over repeated tasks, but it is not a held-out generalization test. Add explicit `train` and `holdout` task groups to the experiment or run a second fixed suite after consolidation. The headline chart should report:

| Arm | Adaptation tasks | Held-out tasks | What it answers |
|---|---:|---:|---|
| Detached | same adaptation tasks | same held-out tasks | Does repeated exposure alone explain the result? |
| Attached | same adaptation tasks | same held-out tasks | Did the admitted record transfer? |

Keep the held-out prompts and hidden expected values out of the consolidation context. The held-out run should happen only after the final consolidation for that round.

## Minimal DABstep evaluator

Create a new family, for example `suite/families/payments.py`, with 10–16 tasks:

- 3–4 public DABstep dev questions for smoke tests;
- 3–4 hand-authored variants whose answers are calculated directly from the pinned DABstep fee rules;
- 3–4 counterexamples that differ in exactly one applicability field;
- 2–4 transfer tasks that rename the merchant or transaction fields while keeping the underlying fee convention.

Each task should carry a JSON answer containing `fee`, `fee_ids`, and `reason_fields`. The hidden check should recompute the fee from the pinned rules and compare the selected rule IDs, rather than compare a prose response. Keep the public DABstep answer strings out of the prompt and use them only in the test fixture.

Recommended first pair:

- **Source:** a credit transaction where the applicable rule has a fixed amount and a rate.
- **Counterexample:** the same merchant and amount with `is_credit=false` or a different ACI, where a different rule applies.

The pair tests whether the memory records the applicability condition, instead of memorizing a merchant or a fee number. Add an independent pair for the `null` wildcard rule because it is a particularly clear “successful repair that becomes dangerous” story.

## Required evaluator correction

`hgi/consolidate.py:96-119` currently computes credit with `not row.get("error")`. That treats a syntactically valid but semantically wrong answer as a success. Use the row's `scores["task_pass_rate"]` value (or a shared `row_passed` helper) for `before` and `after` credit. Otherwise a SQL query that executes and returns the wrong fee can receive positive learning credit.

## Leakage and validity rules

- Pin the exact DABstep or BIRD revision in the family source string and store a SHA-256 of downloaded context.
- Never include reference SQL, public answers, or generated expected values in the agent prompt.
- Split by template/entity, not by random rows only. A random split can put nearly identical merchant/date questions on both sides.
- Report exact fee accuracy, rule-ID accuracy, counterexample rejection, and held-out transfer separately. Do not collapse these into one mean.
- Keep the existing TableBench and MBPP families as regression smoke tests; they are useful for checking the harness but should not support the project claim.

## Sources

- [DABstep dataset card](https://huggingface.co/datasets/adyen/DABstep/blob/main/README.md)
- [DABstep task files](https://huggingface.co/datasets/adyen/DABstep/tree/main/data/tasks)
- [DABstep context files](https://huggingface.co/datasets/adyen/DABstep/tree/main/data/context)
- [BIRD Mini-Dev dataset card](https://huggingface.co/datasets/birdsql/bird_mini_dev)
- [BIRD Mini-Dev repository and evaluation code](https://github.com/bird-bench/mini_dev)
