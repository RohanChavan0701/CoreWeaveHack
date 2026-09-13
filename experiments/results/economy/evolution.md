# economy — evolution: the stream graded on solution quality: economy of calls and turns, and method transfer to a twin world

10 batches × 8 tasks from curriculum, seed 2; every arm meets the same batches in the same order. A pass's score is first sight — nothing in the store was learned on that batch — so the curve is performance on unseen tasks as the store grows.

## First sight, per batch

Pass rate, then economy / turns / transfer per arm.

| batch | attached | detached | attached quality | detached quality | in context (attached) | consolidation after |
|---|---|---|---|---|---|---|
| 1 | 0.50 | 0.50 | 0.26 / 0.27 / 0.00 | 0.29 / 0.29 / 0.00 | none |  |
| 2 | 0.62 | 0.50 | 0.36 / 0.38 / — | 0.26 / 0.27 / 0.00 | none | admitted nothing |
| 3 | 0.38 | 0.38 | 0.21 / 0.21 / — | 0.21 / 0.21 / — | none |  |
| 4 | 0.38 | 0.62 | 0.14 / 0.17 / — | 0.36 / 0.40 / — | none | admitted D-0001 |
| 5 | 0.50 | 0.75 | 0.17 / 0.22 / 1.00 | 0.42 / 0.44 / 0.00 | none |  |
| 6 | 0.50 | 0.50 | 0.21 / 0.24 / 1.00 | 0.19 / 0.22 / 1.00 | none | admitted nothing |
| 7 | 0.50 | 0.62 | 0.21 / 0.24 / 0.00 | 0.43 / 0.40 / 0.00 | none |  |
| 8 | 0.38 | 0.25 | 0.12 / 0.13 / 0.00 | 0.07 / 0.07 / — | none | admitted D-0002 |
| 9 | 0.62 | 0.62 | 0.36 / 0.38 / — | 0.36 / 0.38 / — | none |  |
| 10 | 0.38 | 0.50 | 0.21 / 0.21 / — | 0.29 / 0.31 / — | none | admitted D-0003 |

Over the stream: attached 0.47 (38/80), quality 0.23 / 0.25 / 0.40; detached 0.53 (42/80), quality 0.29 / 0.30 / 0.20.

## First sight, per lesson

Pass rate per arm, then economy / turns / transfer per arm.

| lesson | tier | attached | detached | attached quality | detached quality | naive-shape before / after first mention (attached) | first mention |
|---|---|---|---|---|---|---|---|
| bom | loud | 1.00 (11/11) | 1.00 (11/11) | — / — / — | — / — / — | 0.00 (0/11) / — | — |
| moved-v2 | loud | 0.55 (6/11) | 0.64 (7/11) | 0.28 / 0.37 / — | 0.30 / 0.40 / — | 0.45 (5/11) / — | — |
| token-route | loud | 0.92 (11/12) | 0.92 (11/12) | 0.45 / 0.45 / — | 0.47 / 0.47 / — | 0.00 (0/12) / — | — |
| csv-quoted | visible | 0.45 (5/11) | 0.45 (5/11) | 0.19 / 0.22 / 0.40 | 0.22 / 0.21 / 0.20 | 0.55 (6/11) / — | — |
| footer-row | visible | 0.00 (0/12) | 0.00 (0/12) | 0.00 / 0.00 / — | 0.00 / 0.00 / — | 1.00 (12/12) / — | — |
| paged-api | visible | 0.45 (5/11) | 0.73 (8/11) | 0.50 / 0.50 / — | 0.80 / 0.80 / — | 0.36 (4/11) / — | — |
| trailing-newline | invisible | 0.00 (0/12) | 0.00 (0/12) | 0.00 / 0.00 / — | 0.00 / 0.00 / — | 1.00 (12/12) / — | — |

## Revisit

- attached: batch 1 scored 0.50 at first sight (pass 1) and 0.50 when met again at pass 11 with D-0003 in context.
- attached: batch 2 scored 0.62 at first sight (pass 2) and 0.62 when met again at pass 12 with D-0003 in context.

## Records admitted

- attached D-0001 (after pass 4; mentions moved-v2): Enforce a retry policy for HTTP 410 Gone responses, allowing up to two attempts before declaring failure.
- attached D-0002 (after pass 8; mentions paged-api): Require that every paged query include an active:true filter before counting results.
- attached D-0003 (after pass 10; mentions moved-v2): Introduce a hook that checks for HTTP 410 responses and aborts further tool calls for the affected task.

## Reading

A symptom is derived, not judged: `naive` means the row's result equals what the task's scripted first-contact policy returns (or its error is of the same class), so a naive-shape failure after a record for the lesson was in context is the same shape recurring with the memory attached. Quality grades a passed solution: `economy` is the knowing policy's calls over the calls spent (zero on a failed row), `turns` the same over model turns, `transfer` whether the last shell command replayed in the task's twin world gives the twin's answer — a pass that knows a convention spends less and its method carries, where one that discovers it spends the discovery and may not. `mentions` is a keyword heuristic over a record's text and is logged as one. Every count is from one run and is a floor.
