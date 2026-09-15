# reasoning-core-hard — evolution

6 batches × 4 tasks from reasoning-core-hard, seed 0; every arm meets the same batches in the same order. A pass's score is first sight — nothing in the store was learned on that batch — so the curve is performance on unseen tasks as the store grows.

## First sight, per batch

Pass rate, then economy / turns / transfer per arm.

| batch | qwen-detached | qwen-detached quality | in context (attached) | consolidation after |
|---|---|---|---|---|
| 1 | 0.75 | 0.46 / 0.54 / — | — |  |
| 2 | 1.00 | 0.50 / 0.67 / — | — |  |
| 3 | 0.75 | 0.40 / 0.47 / — | — |  |
| 4 | 0.75 | 0.33 / 0.46 / — | — |  |
| 5 | 0.75 | 0.46 / 0.42 / — | — |  |
| 6 | 1.00 | 0.46 / 0.62 / — | — |  |

Over the stream: qwen-detached 0.83 (20/24), quality 0.43 / 0.53 / —.

## First sight, per lesson

Pass rate per arm, then economy / turns / transfer per arm. The last columns are the attached arm: the naive-shape failures before and after the first pass a record fired on the lesson's rows, that pass, and how the rows a record fired on turned out — a record that fired on everything without helping shows a low ✓ here where keyword mention showed nothing.

| lesson | tier | qwen-detached | qwen-detached quality | naive-shape before / after first applied (attached) | first applied | applied → outcome |
|---|---|---|---|---|---|---|
| reasoning-core-hard | — | 0.83 (20/24) | 0.43 / 0.53 / — | — | — | — |

## Records admitted

None.

## Reading

A symptom is derived, not judged: `naive` means the row's result equals what the task's scripted first-contact policy returns (or its error is of the same class), so a naive-shape failure after a record **fired** on the lesson's rows is the same shape recurring with the memory applied. The series turns on firing (a record's id in a row's `applied`), not on keyword mention: `first applied` is the first stream pass a record fired on the lesson, the naive before / after split turns on it, and `applied → outcome` shows how the rows a record fired on then went — a record that fired on every row and made none of them pass reads as a low ✓ count there, which the old keyword `mentions` column could not show. Quality grades a passed solution: `economy` is the knowing policy's calls over the calls spent (zero on a failed row), `turns` the same over model turns, `transfer` whether the last shell command replayed in the task's twin world gives the twin's answer — a pass that knows a convention spends less and its method carries, where one that discovers it spends the discovery and may not. `mentions` is kept as a keyword heuristic over a record's text and is logged as one, not the driving signal. Every count is from one run and is a floor.

