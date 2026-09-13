# stream — evolution: first-sight performance on unseen tasks as the store grows, attached against detached, per lesson

10 batches × 8 tasks from curriculum, seed 0; every arm meets the same batches in the same order. A pass's score is first sight — nothing in the store was learned on that batch — so the curve is performance on unseen tasks as the store grows.

## First sight, per batch

| batch | 120b-attached | 120b-detached | 20b-attached | 120b-strict | 120b-strict-detached | in context (attached) | consolidation after |
|---|---|---|---|---|---|---|---|
| 1 | 0.25 | 0.62 | 0.62 | 0.38 | 0.25 | none |  |
| 2 | 0.50 | 0.75 | 0.38 | 0.25 | 0.38 | none | admitted nothing |
| 3 | 0.38 | 0.38 | 0.62 | 0.50 | 0.25 | none |  |
| 4 | 0.38 | 0.50 | 0.75 | 0.25 | 0.25 | none | admitted nothing |
| 5 | 0.25 | 0.38 | 0.50 | 0.25 | 0.25 | none |  |
| 6 | 0.62 | 0.50 | 0.75 | 0.38 | 0.38 | none | admitted D-0001 |
| 7 | 0.50 | 0.38 | 0.50 | 0.38 | 0.25 | D-0001 |  |
| 8 | 0.62 | 0.62 | 0.50 | 0.38 | 0.25 | none | admitted nothing |
| 9 | 0.50 | 0.50 | 0.50 | 0.25 | 0.50 | D-0001 |  |
| 10 | 0.62 | 0.75 | 0.62 | 0.38 | 0.50 | D-0001 | admitted nothing |

Over the stream: 120b-attached 0.46 (37/80); 120b-detached 0.54 (43/80); 20b-attached 0.57 (46/80); 120b-strict 0.34 (27/80); 120b-strict-detached 0.33 (26/80).

## First sight, per lesson

| lesson | tier | 120b-attached | 120b-detached | 20b-attached | 120b-strict | 120b-strict-detached | naive-shape before / after first mention (attached) | first mention |
|---|---|---|---|---|---|---|---|---|
| bom | loud | 1.00 (11/11) | 1.00 (11/11) | 1.00 (11/11) | 1.00 (11/11) | 1.00 (11/11) | 0.00 (0/11) / — | — |
| moved-v2 | loud | 0.25 (3/12) | 0.50 (6/12) | 1.00 (12/12) | 0.58 (7/12) | 0.00 (0/12) | 0.67 (8/12) / — | — |
| token-route | loud | 0.82 (9/11) | 1.00 (11/11) | 1.00 (11/11) | 0.00 (0/11) | 0.00 (0/11) | 0.00 (0/11) / — | — |
| csv-quoted | visible | 0.67 (8/12) | 0.58 (7/12) | 0.67 (8/12) | 0.67 (8/12) | 0.50 (6/12) | 0.33 (4/12) / — | — |
| footer-row | visible | 0.00 (0/11) | 0.00 (0/11) | 0.00 (0/11) | 0.00 (0/11) | 0.00 (0/11) | 0.91 (10/11) / — | — |
| paged-api | visible | 0.50 (6/12) | 0.67 (8/12) | 0.25 (3/12) | 0.08 (1/12) | 0.75 (9/12) | 0.33 (4/12) / — | — |
| trailing-newline | invisible | 0.00 (0/11) | 0.00 (0/11) | 0.09 (1/11) | 0.00 (0/11) | 0.00 (0/11) | 1.00 (11/11) / — | — |

## Revisit

- 120b-attached: batch 1 scored 0.25 at first sight (pass 1) and 0.62 when met again at pass 11 with D-0001 in context.
- 120b-attached: batch 2 scored 0.50 at first sight (pass 2) and 0.62 when met again at pass 12 with D-0001 in context.
- 20b-attached: batch 1 scored 0.62 at first sight (pass 1) and 0.75 when met again at pass 11 with D-0002 in context.
- 20b-attached: batch 2 scored 0.38 at first sight (pass 2) and 0.50 when met again at pass 12 with D-0002 in context.
- 120b-strict: batch 1 scored 0.38 at first sight (pass 1) and 0.12 when met again at pass 11 with D-0004 D-0005 D-0006 in context.
- 120b-strict: batch 2 scored 0.25 at first sight (pass 2) and 0.25 when met again at pass 12 with D-0004 D-0005 D-0006 in context.

## Records admitted

- 120b-attached D-0001 (after pass 6; mentions no lesson): Require that file‑tool tasks validate the total line count across all shard files before marking the task successful.
- 20b-attached D-0001 (after pass 4; mentions no lesson): Introduce a decision to wrap None responses from model calls with a safe default to avoid TypeError.
- 20b-attached D-0002 (after pass 4; mentions csv-quoted): Introduce a decision to record shell tool usage and validate output against expected results.
- 20b-attached D-0003 (after pass 8; mentions no lesson): Introduce a decision to validate task outputs against expected results for all tasks.
- 120b-strict D-0001 (after pass 2; mentions moved-v2, token-route): Require all HTTP calls to use versioned /v2 endpoints and include a valid authentication token.
- 120b-strict D-0002 (after pass 6; mentions token-route): Require that an authentication token be present before any HTTP request is issued.
- 120b-strict D-0003 (after pass 8; mentions no lesson): Enforce that every task output is validated against its declared JSON schema before the result is accepted.
- 120b-strict D-0004 (after pass 10; mentions token-route): Require that an authentication token be present before any HTTP request is issued.
- 120b-strict D-0005 (after pass 10; mentions moved-v2, token-route): HTTP calls must use versioned /v2 endpoints and include a valid authentication token.
- 120b-strict D-0006 (after pass 10; mentions token-route): Require a valid authentication token before any HTTP GET tool call is issued.

## Reading

A symptom is derived, not judged: `naive` means the row's result equals what the task's scripted first-contact policy returns (or its error is of the same class), so a naive-shape failure after a record for the lesson was in context is the same shape recurring with the memory attached. `mentions` is a keyword heuristic over a record's text and is logged as one. Every count is from one run and is a floor.
