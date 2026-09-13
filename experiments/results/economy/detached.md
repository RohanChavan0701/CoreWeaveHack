# economy/detached — evolution

detached on `openai/gpt-oss-120b`; 10 batches × 8 tasks from curriculum, seed 2; revisit [1, 2].

## Passes

| pass | batch | first sight | economy / turns / transfer | symptoms | in context | mentions | filed | consolidation after |
|---|---|---|---|---|---|---|---|---|
| 1 | 1 | 0.50 | 0.29 / 0.29 / 0.00 | naive=4 pass=4 | none | — | 0 obs, 0 prop |  |
| 2 | 2 | 0.50 | 0.26 / 0.27 / 0.00 | naive=3 pass=4 wrong=1 | none | — | 0 obs, 0 prop |  |
| 3 | 3 | 0.38 | 0.21 / 0.21 / — | naive=5 pass=3 | none | — | 0 obs, 0 prop |  |
| 4 | 4 | 0.62 | 0.36 / 0.40 / — | naive=3 pass=5 | none | — | 0 obs, 0 prop |  |
| 5 | 5 | 0.75 | 0.42 / 0.44 / 0.00 | naive=2 pass=6 | none | — | 0 obs, 0 prop |  |
| 6 | 6 | 0.50 | 0.19 / 0.22 / 1.00 | naive=4 pass=4 | none | — | 0 obs, 0 prop |  |
| 7 | 7 | 0.62 | 0.43 / 0.40 / 0.00 | naive=3 pass=5 | none | — | 0 obs, 0 prop |  |
| 8 | 8 | 0.25 | 0.07 / 0.07 / — | error:budget=1 naive=5 pass=2 | none | — | 0 obs, 0 prop |  |
| 9 | 9 | 0.62 | 0.36 / 0.38 / — | naive=3 pass=5 | none | — | 0 obs, 0 prop |  |
| 10 | 10 | 0.50 | 0.29 / 0.31 / — | error:model-call=1 naive=3 pass=4 | none | — | 0 obs, 0 prop |  |

## Lessons

Each cell is the lesson's rows in that pass: ✓ passed, N the naive first-contact outcome (a same-shape failure), W another wrong answer, E a harness or tool error. `mentioned` marks passes with a record in context whose text uses the lesson's words.

| lesson | tier | p1 | p2 | p3 | p4 | p5 | p6 | p7 | p8 | p9 | p10 | first sight | economy / turns / transfer | naive before / after first mention | first mention | revisit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| bom | loud | ✓ | ✓ | ✓ | ✓ | ✓✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 1.00 (11/11) | — / — / — | 0.00 (0/11) / — | — | — |
| moved-v2 | loud | N | N | N | ✓✓ | ✓ | ✓ | ✓ | N | ✓ | ✓ | 0.64 (7/11) | 0.30 / 0.40 / — | 0.36 (4/11) / — | — | — |
| token-route | loud | ✓ | ✓W | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓✓ | ✓ | 0.92 (11/12) | 0.47 / 0.47 / — | 0.00 (0/12) / — | — | — |
| csv-quoted | visible | ✓ | ✓ | N | N | ✓ | ✓ | N✓ | E | N | N | 0.45 (5/11) | 0.22 / 0.21 / 0.20 | 0.45 (5/11) / — | — | — |
| footer-row | visible | N | N | NN | N | N | N | N | N | N | EN | 0.00 (0/12) | 0.00 / 0.00 / — | 0.92 (11/12) / — | — | — |
| paged-api | visible | ✓ | ✓ | ✓ | ✓ | ✓ | NN | ✓ | N | ✓ | ✓ | 0.73 (8/11) | 0.80 / 0.80 / — | 0.27 (3/11) / — | — | — |
| trailing-newline | invisible | NN | N | N | N | N | N | N | NN | N | N | 0.00 (0/12) | 0.00 / 0.00 / — | 1.00 (12/12) / — | — | — |

## What the passes noticed

Each observation as the close filed it, with the shape the blind coder gave it at the next consolidation (`open` until one has run); a group reaches the bar when its observations come from as many distinct sessions as the bar asks.

Nothing was filed.

## Records

No decision was admitted.
