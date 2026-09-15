# reasoning-core-hard — evolution

6 batches × 4 tasks from reasoning-core-hard, seed 0; every arm meets the same batches in the same order. A pass's score is first sight — nothing in the store was learned on that batch — so the curve is performance on unseen tasks as the store grows.

## First sight, per batch

Pass rate, then economy / turns / transfer per arm.

| batch | qwen-attached | qwen-attached quality | in context (attached) | consolidation after |
|---|---|---|---|---|
| 1 | 1.00 | 0.71 / 0.75 / — | none |  |
| 2 | 1.00 | 0.40 / 0.56 / — | none | admitted nothing |
| 3 | 0.75 | 0.38 / 0.45 / — | none |  |
| 4 | 0.75 | 0.42 / 0.50 / — | none | admitted D-0001 |
| 5 | 1.00 | 0.71 / 0.75 / — | D-0001 |  |
| 6 | 1.00 | 0.52 / 0.64 / — | D-0001 | admitted D-0002 |

Over the stream: qwen-attached 0.92 (22/24), quality 0.52 / 0.61 / —.

## First sight, per lesson

Pass rate per arm, then economy / turns / transfer per arm. The last columns are the attached arm: the naive-shape failures before and after the first pass a record fired on the lesson's rows, that pass, and how the rows a record fired on turned out — a record that fired on everything without helping shows a low ✓ here where keyword mention showed nothing.

| lesson | tier | qwen-attached | qwen-attached quality | naive-shape before / after first applied (attached) | first applied | applied → outcome |
|---|---|---|---|---|---|---|
| reasoning-core-hard | — | 0.92 (22/24) | 0.52 / 0.61 / — | 0.00 (0/16) / 0.00 (0/8) | 5 | 1/1 (1✓ 0N 0W) |

## Revisit

- qwen-attached: batch 1 scored 1.00 at first sight (pass 1) and 0.75 when met again at pass 7 with D-0001 D-0002 in context.
- qwen-attached: batch 2 scored 1.00 at first sight (pass 2) and 0.75 when met again at pass 8 with D-0001 D-0002 in context.

## Records admitted

- qwen-attached D-0001 (after pass 4; fired 1/1 on reasoning-core-hard): The shell call budget stated in the prompt is a hard limit; exceeding it causes a non-transient tool error and task failure.
- qwen-attached D-0002 (after pass 6; fired never): When a tool call is refused because a budget is exhausted, the refusal is non-transient for that task: further calls to the same tool will also be refused. Stop calling the tool and complete the task with the information already gathered.

## Reading

A symptom is derived, not judged: `naive` means the row's result equals what the task's scripted first-contact policy returns (or its error is of the same class), so a naive-shape failure after a record **fired** on the lesson's rows is the same shape recurring with the memory applied. The series turns on firing (a record's id in a row's `applied`), not on keyword mention: `first applied` is the first stream pass a record fired on the lesson, the naive before / after split turns on it, and `applied → outcome` shows how the rows a record fired on then went — a record that fired on every row and made none of them pass reads as a low ✓ count there, which the old keyword `mentions` column could not show. Quality grades a passed solution: `economy` is the knowing policy's calls over the calls spent (zero on a failed row), `turns` the same over model turns, `transfer` whether the last shell command replayed in the task's twin world gives the twin's answer — a pass that knows a convention spends less and its method carries, where one that discovers it spends the discovery and may not. `mentions` is kept as a keyword heuristic over a record's text and is logged as one, not the driving signal. Every count is from one run and is a floor.

