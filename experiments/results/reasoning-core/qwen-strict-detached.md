# reasoning-core/qwen-strict-detached — evolution

detached on `Qwen/Qwen3.6-35B-A3B`; 6 batches × 4 tasks from reasoning-core-strict, seed 0; revisit [1, 2].

## Passes

| pass | batch | first sight | economy / turns / transfer | symptoms | in context | mentions | filed | consolidation after |
|---|---|---|---|---|---|---|---|---|
| 1 | 1 | 1.00 | 0.58 / 0.71 / — | pass=4 | none | — | 0 obs, 0 prop |  |
| 2 | 2 | 1.00 | 0.67 / 0.75 / — | pass=4 | none | — | 0 obs, 0 prop |  |
| 3 | 3 | 0.75 | 0.38 / 0.46 / — | pass=3 wrong=1 | none | — | 0 obs, 0 prop |  |
| 4 | 4 | 1.00 | 0.71 / 0.79 / — | pass=4 | none | — | 0 obs, 0 prop |  |
| 5 | 5 | 1.00 | 0.62 / 0.75 / — | pass=4 | none | — | 0 obs, 0 prop |  |
| 6 | 6 | 0.75 | 0.38 / 0.50 / — | error:not-json=1 pass=3 | none | — | 0 obs, 0 prop |  |

## Lessons

Each cell is the lesson's rows in that pass: ✓ passed, N the naive first-contact outcome (a same-shape failure), W another wrong answer, E a harness or tool error. `mentioned` marks passes with a record in context whose text uses the lesson's words.

| lesson | tier | p1 | p2 | p3 | p4 | p5 | p6 | first sight | economy / turns / transfer | naive before / after first mention | first mention | revisit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| reasoning-core-strict | — | ✓✓✓✓ | ✓✓✓✓ | ✓✓✓W | ✓✓✓✓ | ✓✓✓✓ | ✓✓✓E | 0.92 (22/24) | 0.56 / 0.66 / — | 0.00 (0/24) / — | — | — |

## What the passes noticed

Each observation as the close filed it, with the shape the blind coder gave it at the next consolidation (`open` until one has run); a group reaches the bar when its observations come from as many distinct sessions as the bar asks.

Nothing was filed.

## Records

No decision was admitted.
