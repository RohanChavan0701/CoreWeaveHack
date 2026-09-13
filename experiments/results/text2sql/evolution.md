# text2sql — evolution: first-sight text-to-SQL on unseen BIRD questions over one schema as the store grows, a strong teacher over the actor

8 batches × 2 tasks from text2sql+text2sql-holdout, seed 0; every arm meets the same batches in the same order. A pass's score is first sight — nothing in the store was learned on that batch — so the curve is performance on unseen tasks as the store grows.

## First sight, per batch

Pass rate, then economy / turns / transfer per arm.

| batch | 120b-attached | 120b-detached | 20b-attached | 120b-strict | 120b-strict-detached | 120b-attached quality | 120b-detached quality | 20b-attached quality | 120b-strict quality | 120b-strict-detached quality | in context (attached) | consolidation after |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.50 | 0.50 | 1.00 | 0.00 | 0.50 | 0.25 / 0.33 / — | 0.25 / 0.33 / — | 0.50 / 0.67 / — | 0.00 / 0.00 / — | 0.50 / 0.50 / — | none |  |
| 2 | 0.50 | 0.50 | 0.00 | 0.00 | 0.00 | 0.17 / 0.25 / — | 0.17 / 0.25 / — | 0.00 / 0.00 / — | 0.00 / 0.00 / — | 0.00 / 0.00 / — | none | admitted nothing |
| 3 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 / 0.00 / — | 0.00 / 0.00 / — | 0.00 / 0.00 / — | 0.00 / 0.00 / — | 0.00 / 0.00 / — | none |  |
| 4 | 0.00 | 0.00 | 0.50 | 0.00 | 0.00 | 0.00 / 0.00 / — | 0.00 / 0.00 / — | 0.50 / 0.50 / — | 0.00 / 0.00 / — | 0.00 / 0.00 / — | none | admitted D-0001 |
| 5 | 0.50 | 0.50 | 0.50 | 0.50 | 0.50 | 0.50 / 0.50 / — | 0.50 / 0.50 / — | 0.50 / 0.50 / — | 0.50 / 0.50 / — | 0.50 / 0.50 / — | none |  |
| 6 | 1.00 | 1.00 | 1.00 | — | — | 1.00 / 1.00 / — | 1.00 / 1.00 / — | 1.00 / 1.00 / — | — | — | none | admitted D-0002 D-0003 D-0004 |
| 7 | 0.00 | 0.00 | 0.00 | — | — | 0.00 / 0.00 / — | 0.00 / 0.00 / — | 0.00 / 0.00 / — | — | — | D-0002 |  |
| 8 | 0.50 | 0.00 | 0.00 | — | — | 0.17 / 0.25 / — | 0.00 / 0.00 / — | 0.00 / 0.00 / — | — | — | D-0002 | admitted D-0005 D-0006 D-0007 |

Over the stream: 120b-attached 0.38 (6/16), quality 0.26 / 0.29 / —; 120b-detached 0.31 (5/16), quality 0.24 / 0.26 / —; 20b-attached 0.38 (6/16), quality 0.31 / 0.33 / —; 120b-strict 0.10 (1/10), quality 0.10 / 0.10 / —; 120b-strict-detached 0.20 (2/10), quality 0.20 / 0.20 / —.

## First sight, per lesson

Pass rate per arm, then economy / turns / transfer per arm.

| lesson | tier | 120b-attached | 120b-detached | 20b-attached | 120b-strict | 120b-strict-detached | 120b-attached quality | 120b-detached quality | 20b-attached quality | 120b-strict quality | 120b-strict-detached quality | naive-shape before / after first mention (attached) | first mention |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| text2sql | — | 0.40 (4/10) | 0.30 (3/10) | 0.30 (3/10) | — | — | 0.31 / 0.34 / — | 0.29 / 0.31 / — | 0.31 / 0.33 / — | — | — | 0.00 (0/10) / — | — |
| text2sql-holdout | — | 0.33 (2/6) | 0.33 (2/6) | 0.50 (3/6) | — | — | 0.25 / 0.28 / — | 0.25 / 0.28 / — | 0.42 / 0.44 / — | — | — | 0.00 (0/6) / — | — |
| text2sql-strict | — | — | — | — | 0.10 (1/10) | 0.20 (2/10) | — | — | — | 0.10 / 0.10 / — | 0.20 / 0.20 / — | — | — |

## Revisit

- 120b-attached: batch 1 scored 0.50 at first sight (pass 1) and 0.50 when met again at pass 9 with D-0002 D-0005 D-0006 D-0007 in context.
- 120b-attached: batch 2 scored 0.50 at first sight (pass 2) and 0.00 when met again at pass 10 with D-0002 D-0005 D-0006 D-0007 in context.
- 20b-attached: batch 1 scored 1.00 at first sight (pass 1) and 1.00 when met again at pass 9 with D-0003 in context.
- 20b-attached: batch 2 scored 0.00 at first sight (pass 2) and 0.00 when met again at pass 10 with D-0003 in context.
- 120b-strict: batch 1 scored 0.00 at first sight (pass 1) and 1.00 when met again at pass 6 with D-0001 D-0002 in context.
- 120b-strict: batch 2 scored 0.00 at first sight (pass 2) and 0.00 when met again at pass 7 with D-0001 D-0002 in context.

## Records admitted

- 120b-attached D-0001 (after pass 4; mentions no lesson): A solution must produce output that conforms to the task's specified schema, not a diagnostic or intermediate artifact.
- 120b-attached D-0002 (after pass 6; mentions no lesson): A solution must produce output that conforms to the task's specified schema, not a diagnostic or intermediate artifact.
- 120b-attached D-0003 (after pass 6; mentions no lesson): A SQL solution must correctly translate the task's logical requirements into the query, not a superficially similar but semantically different condition.
- 120b-attached D-0004 (after pass 6; mentions no lesson): A solution must consult the store's rules before execution; a failure with no applicable rule is a process failure, not a task failure.
- 120b-attached D-0005 (after pass 8; mentions no lesson): A solution's final output must be a valid JSON object conforming to the task's declared response schema, not a diagnostic, intermediate artifact, or incorrectly formatted string.
- 120b-attached D-0006 (after pass 8; mentions no lesson): A SQL solution must correctly translate the task's logical requirements into the query, not a superficially similar but semantically different condition.
- 120b-attached D-0007 (after pass 8; mentions no lesson): A solution must consult the store's rules before execution; a failure with no applicable rule is a process failure, not a task failure.
- 20b-attached D-0001 (after pass 4; mentions no lesson): When generating SQL, the query must precisely match the requested aggregation target and filtering conditions as stated in the natural language prompt, without substituting similar but incorrect entities or omitting required clauses.
- 20b-attached D-0002 (after pass 6; mentions no lesson): When generating SQL from a natural language prompt, the query must precisely match the requested aggregation target and filtering conditions, and all column references must be fully qualified with their table alias to prevent ambiguity.
- 20b-attached D-0003 (after pass 8; mentions no lesson): When generating SQL from a natural language prompt, the query must precisely match the requested aggregation target and filtering conditions, and all column references must be fully qualified with their table alias to prevent ambiguity.
- 120b-strict D-0001 (after pass 3; mentions no lesson): Every pass must respect the tool-call budget. If a pass makes more tool calls than the budget allows, the system must abort the pass and report the budget violation.
- 120b-strict D-0002 (after pass 4; mentions csv-quoted): When generating SQL, the final answer must be a SELECT statement that returns rows, not an aggregate function, a schema inspection command, or any other non-SELECT output.

## Reading

A symptom is derived, not judged: `naive` means the row's result equals what the task's scripted first-contact policy returns (or its error is of the same class), so a naive-shape failure after a record for the lesson was in context is the same shape recurring with the memory attached. Quality grades a passed solution: `economy` is the knowing policy's calls over the calls spent (zero on a failed row), `turns` the same over model turns, `transfer` whether the last shell command replayed in the task's twin world gives the twin's answer — a pass that knows a convention spends less and its method carries, where one that discovers it spends the discovery and may not. `mentions` is a keyword heuristic over a record's text and is logged as one. Every count is from one run and is a floor.

