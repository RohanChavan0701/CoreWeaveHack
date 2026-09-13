# stream/20b-attached — evolution

attached on `openai/gpt-oss-20b`; 10 batches × 8 tasks from curriculum, seed 0; revisit [1, 2].

## Passes

| pass | batch | first sight | symptoms | in context | mentions | filed | consolidation after |
|---|---|---|---|---|---|---|---|
| 1 | 1 | 0.62 | error:model-call=1 naive=2 pass=5 | none | — | 1 obs, 0 prop |  |
| 2 | 2 | 0.38 | error:model-call=2 error:turn-limit=1 naive=2 pass=3 | none | — | 5 obs, 1 prop | K-0001: 3 groups, 1 at the bar; admitted nothing; 1 declined; draft dropped |
| 3 | 3 | 0.62 | naive=3 pass=5 | none | — | 2 obs, 1 prop |  |
| 4 | 4 | 0.75 | naive=2 pass=6 | none | — | 0 obs, 0 prop | K-0002: 3 groups, 2 at the bar; admitted D-0001 D-0002; 1 admitted D-0001, 1 admitted D-0002, 1 escalated to the human queue; dismissed 2 |
| 5 | 5 | 0.50 | error:turn-limit=1 naive=3 pass=4 | D-0002 | csv-quoted: D-0002 | 3 obs, 1 prop |  |
| 6 | 6 | 0.75 | naive=2 pass=6 | D-0002 | csv-quoted: D-0002 | 0 obs, 1 prop | K-0003: 0 groups, 0 at the bar; admitted nothing; 1 draft refused at parse: a counterfactual-edit supersedes exactly one record; got [], 1 draft refused at parse: a hook-edit supersedes exactly one record; got [], 1 moot; dismissed 4 |
| 7 | 7 | 0.50 | naive=4 pass=4 | D-0002 | csv-quoted: D-0002 | 4 obs, 1 prop |  |
| 8 | 8 | 0.50 | error:turn-limit=1 naive=1 pass=4 wrong=2 | D-0002 | csv-quoted: D-0002 | 4 obs, 0 prop | K-0004: 2 groups, 1 at the bar; admitted D-0003; 1 admitted D-0003, 4 moot: retired through the genesis-deadline door, 2 still-holds: kept; retired L-0001 L-0002 L-0003 L-0007 |
| 9 | 9 | 0.50 | error:model-call=1 naive=3 pass=4 | D-0002 | csv-quoted: D-0002 | 3 obs, 1 prop |  |
| 10 | 10 | 0.62 | error:model-call=1 naive=2 pass=5 | D-0002 | csv-quoted: D-0002 | 0 obs, 0 prop | K-0005: 3 groups, 0 at the bar; admitted nothing; 1 moot, 2 moot: retired through the genesis-deadline door; retired L-0005 L-0008 |
| 11 (revisit) | 1 | 0.75 | naive=2 pass=6 | D-0002 | csv-quoted: D-0002 | 1 obs, 1 prop |  |
| 12 (revisit) | 2 | 0.50 | error:model-call=2 naive=2 pass=4 | D-0002 | csv-quoted: D-0002 | 3 obs, 1 prop |  |

## Lessons

Each cell is the lesson's rows in that pass: ✓ passed, N the naive first-contact outcome (a same-shape failure), W another wrong answer, E a harness or tool error. `mentioned` marks passes with a record in context whose text uses the lesson's words.

| lesson | tier | p1 | p2 | p3 | p4 | p5 | p6 | p7 | p8 | p9 | p10 | p11r | p12r | first sight | naive before / after first mention | first mention | revisit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| bom | loud | ✓ | ✓ | ✓ | ✓ | ✓ | ✓✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 1.00 (11/11) | 0.00 (0/11) / — | — | batch 1: 1/1, batch 2: 1/1 |
| moved-v2 | loud | ✓✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓✓ | ✓ | ✓ | ✓✓ | N | 1.00 (12/12) | 0.00 (0/12) / — | — | batch 1: 2/2, batch 2: 0/1 |
| token-route | loud | ✓ | ✓ | ✓ | ✓✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 1.00 (11/11) | 0.00 (0/11) / — | — | batch 1: 1/1, batch 2: 1/1 |
| csv-quoted | visible | ✓ | E | ✓N | ✓ | E* | ✓* | ✓* | E* | ✓* | ✓✓* | ✓* | ✓* | 0.67 (8/12) | 0.20 (1/5) / 0.00 (0/7) | 5 | batch 1: 1/1, batch 2: 1/1 |
| footer-row | visible | N | N | N | N | NN | N | N | W | N | N | N | N | 0.00 (0/11) | 0.91 (10/11) / — | — | batch 1: 0/1, batch 2: 0/1 |
| paged-api | visible | E | EE | ✓ | ✓ | N | ✓ | N | W | NE | E | ✓ | EE | 0.25 (3/12) | 0.25 (3/12) / — | — | batch 1: 1/1, batch 2: 0/2 |
| trailing-newline | invisible | N | N | N | N | ✓ | N | NN | N | N | N | N | ✓ | 0.09 (1/11) | 0.91 (10/11) / — | — | batch 1: 0/1, batch 2: 1/1 |

## What the passes noticed

Each observation as the close filed it, with the shape the blind coder gave it at the next consolidation (`open` until one has run); a group reaches the bar when its observations come from as many distinct sessions as the bar asks.

- pass 1 O-0001 [error-wrapping]: Task curriculum/paged_02 failed on first attempt due to a NoneType model call causing a TypeError; the correct behavior would have been to handle the None response.
- pass 2 O-0002 [test-failure-triage]: Task curriculum/footer_04 failed: the first attempt returned 4030 but the expected sum was different; the convention of this world was missed by not verifying the result against the expected value.
- pass 2 O-0003 [shell-tool]: In task curriculum/newline_00, the first attempt used the shell command wc -l batch-1.txt batch-2.txt | awk 'END{print $1}' but did not record the tool usage, so the record that should have fired is the tool usage record.
- pass 2 O-0004 [error-wrapping]: Task curriculum/paged_06 failed on first attempt because the model call returned None, causing a TypeError; the task would have passed if the model call returned a valid response.
- pass 2 O-0005 [error-wrapping]: The first attempt failed because the model call returned None, causing a TypeError when trying to subscript it.
- pass 2 O-0006 [file-tool]: Task curriculum/csv_01: first attempt used awk without handling quoted customer field, causing the record with customer "Initech, LLC" to be ignored; the correct approach would strip quotes before comparison.
- K-0001 group [file-tool] ← O-0006 from S-0002 — below the bar
- K-0001 group [shell-tool] ← O-0003 from S-0002 — below the bar
- K-0001 group [test-failure-triage] ← O-0001 O-0002 O-0004 O-0005 from S-0001 S-0002 — at the bar
- K-0001 nominated null-check at new-decision → declined; draft dropped
- pass 3 O-0007 [shell-tool]: task curriculum/newline_03: first attempt used wc -l on all three files but the result was incorrect; the correct total lines should be 15.
- pass 3 O-0008 [file-tool]: Task curriculum/csv_04: first attempt used awk to count Oslo rows but returned 0, missing the row where city is Oslo; the correct result would be 1.
- K-0002 group [error-wrapping] ← O-0001 O-0004 O-0005 from S-0001 S-0002 — at the bar
- K-0002 group [shell-tool] ← O-0003 O-0007 from S-0002 S-0003 — at the bar
- K-0002 group [test-failure-triage] ← O-0002 from S-0002 — below the bar
- K-0002 nominated error-wrapping at new-decision → admitted D-0001
- K-0002 nominated shell-tool at new-decision → admitted D-0002
- K-0002 nominated file-tool at new-decision → escalated to the human queue
- pass 5 O-0009 [test-failure-triage]: Task curriculum/footer_02: the first attempt did not trigger validation of shell output, causing a wrong result.
- pass 5 O-0010 [test-failure-triage]: Task curriculum/paged_01 returned 1 order but did not filter for active orders; D-0002 should have fired to validate the output against expected results.
- pass 5 O-0011 [test-failure-triage]: The task curriculum/csv_10 failed because the shell command was executed but the output was not validated; record D-0002 should have fired to record shell tool usage and validate output.
- K-0003 nominated Non-shell at counterfactual-edit → draft refused at parse: a counterfactual-edit supersedes exactly one record; got []
- K-0003 nominated MissingTerms at hook-edit → draft refused at parse: a hook-edit supersedes exactly one record; got []
- K-0003 nominated D-0001 at counterfactual-edit → moot
- pass 7 O-0012 [test-failure-triage]: Task curriculum/footer_10 produced result 2392 but did not validate against expected, missing record D-0002.
- pass 7 O-0013 [test-failure-triage]: The task curriculum/newline_08 failed because the first attempt did not record task_pass_rate as 1.0, missing the convention that a successful task must set task_pass_rate to 1.0.
- pass 7 O-0014 [test-failure-triage]: Task curriculum/paged_07 returned 2 jobs but did not satisfy the pass criteria; the first attempt did not verify the result against expected output.
- pass 7 O-0015 [test-failure-triage]: Task curriculum/newline_11 failed because the first attempt returned 18 lines, but the expected total was different; the record that should have validated the output did not fire.
- pass 8 O-0016 [test-failure-triage]: Task curriculum/footer_07: first attempt used wc -l which counted the header, resulting in 5 instead of the expected 4; should have validated output against expected results.
- pass 8 O-0017 [shell-tool, test-failure-triage]: Task curriculum/newline_09 failed because the first attempt did not produce an observation for the shell tool usage, which would have validated the output.
- pass 8 O-0018 [shell-tool, test-failure-triage]: Task curriculum/paged_03 failed on first attempt because it did not use a shell tool, missing the convention to record shell tool usage.
- pass 8 O-0019 [shell-tool, test-failure-triage]: Task curriculum/csv_07 failed to use the shell tool to compute the sum of the total column for Initech, LLC, missing the required shell call.
- K-0004 group [shell-tool, test-failure-triage] ← O-0017 O-0018 O-0019 from S-0008 — below the bar
- K-0004 group [test-failure-triage] ← O-0012 O-0013 O-0014 O-0015 O-0016 from S-0007 S-0008 — at the bar
- K-0004 nominated validation at new-decision → admitted D-0003
- K-0004 nominated L-0001 at counterfactual-edit → moot: retired through the genesis-deadline door
- K-0004 nominated L-0002 at counterfactual-edit → moot: retired through the genesis-deadline door
- K-0004 nominated L-0003 at counterfactual-edit → moot: retired through the genesis-deadline door
- K-0004 nominated L-0005 at counterfactual-edit → still-holds: kept
- K-0004 nominated L-0007 at counterfactual-edit → moot: retired through the genesis-deadline door
- K-0004 nominated L-0008 at counterfactual-edit → still-holds: kept
- pass 9 O-0020 [output-schema, test-failure-triage]: Task curriculum/footer_00: first attempt produced incorrect sum 5198; record D-0002 should have fired to flag the mismatch.
- pass 9 O-0021 [output-schema, test-failure-triage]: Task curriculum/newline_05: the first attempt used wc -l on all files in one call, but the result 13 was incorrect; the record D-0002 should have validated the output against the expected total and flagged the mismatch.
- pass 9 O-0022 [http-tool, test-failure-triage]: Task curriculum/paged_10 failed because the first attempt did not make the required GET /sensors API call; it should have fired a decision record enforcing API usage.
- K-0005 group [http-tool, test-failure-triage] ← O-0022 from S-0009 — below the bar
- K-0005 group [output-schema, test-failure-triage] ← O-0020 O-0021 from S-0009 — below the bar
- K-0005 group [shell-tool, test-failure-triage] ← O-0017 O-0018 O-0019 from S-0008 — below the bar
- K-0005 nominated D-0003 at counterfactual-edit → moot
- K-0005 nominated L-0005 at counterfactual-edit → moot: retired through the genesis-deadline door
- K-0005 nominated L-0008 at counterfactual-edit → moot: retired through the genesis-deadline door
- pass 11 O-0023 [open]: Task curriculum/newline_02: first attempt used wc -l but did not validate output; the expected total lines were not verified, so the result may be incorrect.
- pass 12 O-0024 [open]: Task curriculum/footer_04 failed because the shell command returned a raw number instead of JSON, violating the expected output schema.
- pass 12 O-0025 [open]: Task curriculum/moved_00 failed to retrieve project name due to HTTP 410 errors on GET /projects/82.
- pass 12 O-0026 [open]: Task curriculum/paged_00 failed on its first attempt due to a TypeError from the API call returning None; the convention of this world missed the expected error handling for a None response.

## Records

| record | admitted after pass | mentions | decision |
|---|---|---|---|
| D-0001 | 4 | — | Introduce a decision to wrap None responses from model calls with a safe default to avoid TypeError. |
| D-0002 | 4 | csv-quoted | Introduce a decision to record shell tool usage and validate output against expected results. |
| D-0003 | 8 | — | Introduce a decision to validate task outputs against expected results for all tasks. |
