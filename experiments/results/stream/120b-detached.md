# stream/120b-detached — evolution

detached on `openai/gpt-oss-120b`; 10 batches × 8 tasks from curriculum, seed 0; revisit [1, 2].

## Passes

| pass | batch | first sight | symptoms | in context | mentions | filed | consolidation after |
|---|---|---|---|---|---|---|---|
| 1 | 1 | 0.62 | naive=3 pass=5 | none | — | 0 obs, 0 prop |  |
| 2 | 2 | 0.75 | error:model-call=1 naive=1 pass=6 | none | — | 0 obs, 0 prop |  |
| 3 | 3 | 0.38 | naive=4 pass=3 wrong=1 | none | — | 0 obs, 0 prop |  |
| 4 | 4 | 0.50 | naive=4 pass=4 | none | — | 0 obs, 0 prop |  |
| 5 | 5 | 0.38 | naive=4 pass=3 wrong=1 | none | — | 0 obs, 0 prop |  |
| 6 | 6 | 0.50 | error:model-call=1 error:not-json=1 naive=2 pass=4 | none | — | 0 obs, 0 prop |  |
| 7 | 7 | 0.38 | naive=5 pass=3 | none | — | 0 obs, 0 prop |  |
| 8 | 8 | 0.62 | naive=3 pass=5 | none | — | 0 obs, 0 prop |  |
| 9 | 9 | 0.50 | naive=4 pass=4 | none | — | 0 obs, 0 prop |  |
| 10 | 10 | 0.75 | naive=2 pass=6 | none | — | 0 obs, 0 prop |  |

## Lessons

Each cell is the lesson's rows in that pass: ✓ passed, N the naive first-contact outcome (a same-shape failure), W another wrong answer, E a harness or tool error. `mentioned` marks passes with a record in context whose text uses the lesson's words.

| lesson | tier | p1 | p2 | p3 | p4 | p5 | p6 | p7 | p8 | p9 | p10 | first sight | naive before / after first mention | first mention | revisit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| bom | loud | ✓ | ✓ | ✓ | ✓ | ✓ | ✓✓ | ✓ | ✓ | ✓ | ✓ | 1.00 (11/11) | 0.00 (0/11) / — | — | — |
| moved-v2 | loud | ✓✓ | ✓ | N | ✓ | N | N | N | ✓N | N | ✓ | 0.50 (6/12) | 0.50 (6/12) / — | — | — |
| token-route | loud | ✓ | ✓ | ✓ | ✓✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 1.00 (11/11) | 0.00 (0/11) / — | — | — |
| csv-quoted | visible | N | ✓ | N✓ | N | ✓ | E | ✓ | ✓ | N | ✓✓ | 0.58 (7/12) | 0.33 (4/12) / — | — | — |
| footer-row | visible | N | E | N | N | NN | E | N | N | N | N | 0.00 (0/11) | 0.82 (9/11) / — | — | — |
| paged-api | visible | ✓ | ✓✓ | W | N | W | ✓ | N | ✓ | ✓✓ | ✓ | 0.67 (8/12) | 0.17 (2/12) / — | — | — |
| trailing-newline | invisible | N | N | N | N | N | N | NN | N | N | N | 0.00 (0/11) | 1.00 (11/11) / — | — | — |

## What the passes noticed

Each observation as the close filed it, with the shape the blind coder gave it at the next consolidation (`open` until one has run); a group reaches the bar when its observations come from as many distinct sessions as the bar asks.

Nothing was filed.

## Records

No decision was admitted.
