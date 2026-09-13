# text2sql/120b-strict-detached — evolution

detached on `openai/gpt-oss-120b`; 5 batches × 2 tasks from text2sql-strict, seed 0; revisit [1, 2].

## Passes

| pass | batch | first sight | economy / turns / transfer | symptoms | in context | mentions | filed | consolidation after |
|---|---|---|---|---|---|---|---|---|
| 1 | 1 | 0.50 | 0.50 / 0.50 / — | pass=1 wrong=1 | none | — | 0 obs, 0 prop |  |
| 2 | 2 | 0.00 | 0.00 / 0.00 / — | wrong=2 | none | — | 0 obs, 0 prop |  |
| 3 | 3 | 0.00 | 0.00 / 0.00 / — | error:not-json=1 wrong=1 | none | — | 0 obs, 0 prop |  |
| 4 | 4 | 0.00 | 0.00 / 0.00 / — | wrong=2 | none | — | 0 obs, 0 prop |  |
| 5 | 5 | 0.50 | 0.50 / 0.50 / — | error:not-json=1 pass=1 | none | — | 0 obs, 0 prop |  |

## Lessons

Each cell is the lesson's rows in that pass: ✓ passed, N the naive first-contact outcome (a same-shape failure), W another wrong answer, E a harness or tool error. `mentioned` marks passes with a record in context whose text uses the lesson's words.

| lesson | tier | p1 | p2 | p3 | p4 | p5 | first sight | economy / turns / transfer | naive before / after first mention | first mention | revisit |
|---|---|---|---|---|---|---|---|---|---|---|---|
| text2sql-strict | — | ✓W | WW | EW | WW | ✓E | 0.20 (2/10) | 0.20 / 0.20 / — | 0.00 (0/10) / — | — | — |

## What the passes noticed

Each observation as the close filed it, with the shape the blind coder gave it at the next consolidation (`open` until one has run); a group reaches the bar when its observations come from as many distinct sessions as the bar asks.

Nothing was filed.

## Records

No decision was admitted.
