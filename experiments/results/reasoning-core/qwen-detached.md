# reasoning-core/qwen-detached — evolution

detached on `Qwen/Qwen3.6-35B-A3B`; 6 batches × 4 tasks from reasoning-core, seed 0; revisit [1, 2].

## Passes

| pass | batch | first sight | economy / turns / transfer | symptoms | in context | mentions | filed | consolidation after |
|---|---|---|---|---|---|---|---|---|
| 1 | 1 | 0.75 | 0.25 / 0.37 / — | pass=3 wrong=1 | none | — | 0 obs, 0 prop |  |
| 2 | 2 | 1.00 | 0.25 / 0.40 / — | pass=4 | none | — | 0 obs, 0 prop |  |
| 3 | 3 | 1.00 | 0.52 / 0.64 / — | pass=4 | none | — | 0 obs, 0 prop |  |
| 4 | 4 | 0.75 | 0.21 / 0.33 / — | error:not-json=1 pass=3 | none | — | 0 obs, 0 prop |  |
| 5 | 5 | 0.75 | 0.25 / 0.37 / — | pass=3 wrong=1 | none | — | 0 obs, 0 prop |  |
| 6 | 6 | 1.00 | 0.36 / 0.52 / — | pass=4 | none | — | 0 obs, 0 prop |  |

## Lessons

Each cell is the lesson's rows in that pass: ✓ passed, N the naive first-contact outcome (a same-shape failure), W another wrong answer, E a harness or tool error. `mentioned` marks passes with a record in context whose text uses the lesson's words.

| lesson | tier | p1 | p2 | p3 | p4 | p5 | p6 | first sight | economy / turns / transfer | naive before / after first mention | first mention | revisit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| reasoning-core | — | ✓✓✓W | ✓✓✓✓ | ✓✓✓✓ | ✓✓E✓ | ✓W✓✓ | ✓✓✓✓ | 0.88 (21/24) | 0.31 / 0.44 / — | 0.00 (0/24) / — | — | — |

## What the passes noticed

Each observation as the close filed it, with the shape the blind coder gave it at the next consolidation (`open` until one has run); a group reaches the bar when its observations come from as many distinct sessions as the bar asks.

Nothing was filed.

## Records

No decision was admitted.
