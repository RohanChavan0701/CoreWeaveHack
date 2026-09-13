# stream-120b-attached — the retrofitted store beside the original, pass by pass

Source `stream/120b-attached` (store at `8eb9069`), retrofitted on 2026-09-13 from the code at `faabceb`: the rows are the source arm's, unchanged; the close runs on `openai/gpt-oss-120b`, the backward pass on `openai/gpt-oss-120b`; consolidation every 2 passes. The retrofit's decisions begin at D-0003; any lower decision id is the original's. Nothing was in context at any retrofitted pass: the stream is prequential, and a pass the original booted with a record in context produced its rows under that record.

## After each pass

`o` is the original store after the pass (its consolidation included where one ran), `r` the retrofitted one.

| pass | score | in context (o) | filed o / r | open obs o / r | accepted o / r | fires o / r | steers o / r | consolidation (o) | consolidation (r) |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.25 | none | 5 / 11 | 5 / 11 | 0 / 0 | 0 open of 0 / 0 open of 0 | 0 / 0 |  |  |
| 2 | 0.50 | none | 4 / 8 | 9 / 17 | 0 / 1 | 0 open of 0 / 0 open of 0 | 0 / 0 | K-0001: admitted nothing; 1 declined | K-0001: admitted D-0003; 1 admitted D-0003, 1 draft refused at parse: a hook-edit supersedes exactly one record |
| 3 | 0.38 | none | 5 / 11 | 14 / 28 | 0 / 1 | 0 open of 0 / 0 open of 0 | 0 / 0 |  |  |

## Decisions

**Original.** Nothing admitted.

**Retrofit.** 
- D-0003 [accepted] on route-guarded error-wrapping file-tool http-tool (displaced from hook-edit): Require the presence of a token query parameter for all secure‑route requests before proceeding. — after pass 2

## Observations by shape, pass by pass

Open observations under each shape after each pass, original / retrofit; a shape is the blind coder's at the next consolidation, so a pile is `uncoded` until one has run. The bar asks for observations from as many distinct sessions as `independent_observations`; the last column is each side's final pile with what was promoted or dismissed.

| shape | p1 | p2 | p3 | end o / r (open; promoted; dismissed) |
|---|---|---|---|---|
| http-tool | 0 / 0 | 4 / 0 | 4 / 0 | 4; 0; 0 / 0; 0; 0 |
| listing-paged | 0 / 0 | 0 / 1 | 0 / 1 | 0; 0; 0 / 1; 0; 0 |
| other(bad request error) | 0 / 0 | 0 / 1 | 0 / 1 | 0; 0; 0 / 1; 0; 0 |
| other(malformed JSON arguments) | 0 / 0 | 0 / 1 | 0 / 1 | 0; 0; 0 / 1; 0; 0 |
| other(missing result validation check) | 0 / 0 | 0 / 1 | 0 / 1 | 0; 0; 0 / 1; 0; 0 |
| other(no applicable rule) | 0 / 0 | 0 / 6 | 0 / 6 | 0; 0; 0 / 6; 0; 0 |
| other(no store rule) | 0 / 0 | 0 / 2 | 0 / 2 | 0; 0; 0 / 2; 0; 0 |
| output-schema | 0 / 0 | 2 / 1 | 2 / 1 | 2; 0; 0 / 1; 0; 0 |
| route-guarded | 0 / 0 | 0 / 0 | 0 / 0 | 0; 0; 0 / 0; 2; 0 |
| route-versioned | 0 / 0 | 0 / 3 | 0 / 3 | 0; 0; 0 / 3; 0; 0 |
| shell-tool | 0 / 0 | 1 / 1 | 1 / 1 | 1; 0; 0 / 1; 0; 0 |
| test-failure-triage | 0 / 0 | 2 / 0 | 2 / 0 | 2; 0; 0 / 0; 0; 0 |
| uncoded | 5 / 11 | 0 / 0 | 5 / 11 | 5; 0; 0 / 11; 0; 0 |

## Where they diverge, and why

- pass 1: the close filed 5 observations originally and 11 retrofitted — the close lenses are today's (L-0004 per failed row, L-0009 on recovered misses, L-0010 off-map) on the same rows
- pass 2: the close filed 4 observations originally and 8 retrofitted — the close lenses are today's (L-0004 per failed row, L-0009 on recovered misses, L-0010 off-map) on the same rows
- after pass 2: the original K-0001 admitted nothing; the retrofit K-0001 admitted D-0003
- after pass 2: nomination outcomes — original {'declined': 1}; retrofit {'admitted D-0003': 1, 'draft refused at parse: a hook-edit supersedes exactly one record': 1}
- pass 3: the close filed 5 observations originally and 11 retrofitted — the close lenses are today's (L-0004 per failed row, L-0009 on recovered misses, L-0010 off-map) on the same rows

## What the retrofit's passes stripped

No pass of the original consulted a record or saw a fire: every row was produced with nothing in context, and the retrofit is a clean counterfactual of the backward pass alone.

## Reading

The forward pass is the record and was not replayed: every score above is the original actor's, and a retrofitted consolidation that admits a record cannot change the rows that follow it. Where the original consulted a record, the rows after that point were produced under it and the retrofit reads them as if nothing had been in context — the divergence is then partly the actor's and not the backward pass's. Every count is from one run of each backward pass and is a floor.
