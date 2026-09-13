# stream/120b-attached — evolution

attached on `openai/gpt-oss-120b`; 10 batches × 8 tasks from curriculum, seed 0; revisit [1, 2].

## Passes

| pass | batch | first sight | symptoms | in context | mentions | filed | consolidation after |
|---|---|---|---|---|---|---|---|
| 1 | 1 | 0.25 | naive=4 pass=2 wrong=2 | none | — | 5 obs, 1 prop |  |
| 2 | 2 | 0.50 | error:model-call=1 naive=2 pass=4 wrong=1 | none | — | 4 obs, 1 prop | K-0001: 4 groups, 3 at the bar; admitted nothing; 1 declined; draft dropped |
| 3 | 3 | 0.38 | naive=4 pass=3 wrong=1 | none | — | 5 obs, 1 prop |  |
| 4 | 4 | 0.38 | naive=4 pass=3 wrong=1 | none | — | 3 obs, 1 prop | K-0002: 8 groups, 3 at the bar; admitted nothing; 1 draft refused at parse: a counterfactual-edit supersedes exactly one record; got [], 1 draft refused at parse: a hook-edit supersedes exactly one record; got [], 1 draft refused at parse: not_this: List should have at least 1 item after validation, not 0 |
| 5 | 5 | 0.25 | naive=6 pass=2 | none | — | 6 obs, 1 prop |  |
| 6 | 6 | 0.62 | naive=3 pass=5 | none | — | 2 obs, 1 prop | K-0003: 10 groups, 4 at the bar; admitted D-0001; 1 admitted D-0001, 3 declined; draft dropped |
| 7 | 7 | 0.50 | naive=4 pass=4 | D-0001 | — | 3 obs, 1 prop |  |
| 8 | 8 | 0.62 | naive=3 pass=5 | none | — | 3 obs, 1 prop | K-0004: 9 groups, 5 at the bar; admitted nothing; 4 draft refused at parse: not_this: List should have at least 1 item after validation, not 0, 1 escalated to the human queue, 3 moot: retired through the genesis-deadline door; retired L-0001 L-0002 L-0003 |
| 9 | 9 | 0.50 | naive=4 pass=4 | D-0001 | — | 4 obs, 1 prop |  |
| 10 | 10 | 0.62 | naive=3 pass=5 | D-0001 | — | 3 obs, 1 prop | K-0005: 7 groups, 5 at the bar; admitted nothing; 1 declined; draft dropped, 1 draft refused at parse: a hook-edit supersedes exactly one record; got [], 3 draft refused at parse: not_this: List should have at least 1 item after validation, not 0 |
| 11 (revisit) | 1 | 0.62 | naive=3 pass=5 | D-0001 | — | 3 obs, 1 prop |  |
| 12 (revisit) | 2 | 0.62 | naive=3 pass=5 | D-0001 | — | 2 obs, 1 prop |  |

## Lessons

Each cell is the lesson's rows in that pass: ✓ passed, N the naive first-contact outcome (a same-shape failure), W another wrong answer, E a harness or tool error. `mentioned` marks passes with a record in context whose text uses the lesson's words.

| lesson | tier | p1 | p2 | p3 | p4 | p5 | p6 | p7 | p8 | p9 | p10 | p11r | p12r | first sight | naive before / after first mention | first mention | revisit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| bom | loud | ✓ | ✓ | ✓ | ✓ | ✓ | ✓✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 1.00 (11/11) | 0.00 (0/11) / — | — | batch 1: 1/1, batch 2: 1/1 |
| moved-v2 | loud | WN | N | N | ✓ | N | N | ✓ | ✓N | N | N | ✓✓ | N | 0.25 (3/12) | 0.67 (8/12) / — | — | batch 1: 2/2, batch 2: 0/1 |
| token-route | loud | W | ✓ | ✓ | W✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 0.82 (9/11) | 0.00 (0/11) / — | — | batch 1: 1/1, batch 2: 1/1 |
| csv-quoted | visible | N | ✓ | N✓ | N | N | ✓ | ✓ | ✓ | ✓ | ✓✓ | N | ✓ | 0.67 (8/12) | 0.33 (4/12) / — | — | batch 1: 0/1, batch 2: 1/1 |
| footer-row | visible | N | E | N | N | NN | N | N | N | N | N | N | N | 0.00 (0/11) | 0.91 (10/11) / — | — | batch 1: 0/1, batch 2: 0/1 |
| paged-api | visible | ✓ | W✓ | W | N | N | ✓ | N | ✓ | N✓ | ✓ | ✓ | ✓✓ | 0.50 (6/12) | 0.33 (4/12) / — | — | batch 1: 1/1, batch 2: 2/2 |
| trailing-newline | invisible | N | N | N | N | N | N | NN | N | N | N | N | N | 0.00 (0/11) | 1.00 (11/11) / — | — | batch 1: 0/1, batch 2: 0/1 |

## What the passes noticed

Each observation as the close filed it, with the shape the blind coder gave it at the next consolidation (`open` until one has run); a group reaches the bar when its observations come from as many distinct sessions as the bar asks.

- pass 1 O-0001 [http-tool]: In task curriculum/moved_06 the first attempt called GET /zones/90 on the wrong endpoint, received HTTP 410 Gone, and would have passed by calling /v2/zones/90 to obtain the zone name.
- pass 1 O-0002 [file-tool]: In task curriculum/newline_02 the first attempt counted 14 lines, but the correct total should include all lines from the five shard files, so the line-count convention was missed.
- pass 1 O-0003 [http-tool, test-failure-triage]: Task curriculum/moved_04 attempted GET /plans/49 but received 410 Gone, so it should have recorded an observation of the missing plan.
- pass 1 O-0004 [output-schema]: The first attempt returned a plain number instead of the required JSON result, violating the output schema.
- pass 1 O-0005 [http-tool]: GET /secure/ledger returned HTTP 401 Unauthorized because the required token was missing.
- pass 2 O-0006 [shell-tool]: In task curriculum/footer_04 the model attempted a shell call with invalid JSON arguments, causing a BadRequestError; a correctly formatted JSON call would have succeeded.
- pass 2 O-0007 [http-tool]: Task curriculum/moved_00 attempted GET /projects/82 on a deprecated endpoint, but the correct call should target /v2/projects/82 to retrieve the project name.
- pass 2 O-0008 [file-tool]: In task curriculum/newline_00 the first attempt returned 12 lines, which was incorrect, missing the correct total and thus violating the convention of accurately summing lines across both files.
- pass 2 O-0009 [http-tool, output-schema]: Task curriculum/paged_00 attempted GET /entries but received HTTP 406, violating the expected summed result output schema.
- K-0001 group [http-tool] ← O-0001 O-0003 O-0005 O-0007 from S-0001 S-0002 — at the bar
- K-0001 group [output-schema] ← O-0004 O-0009 from S-0001 S-0002 — at the bar
- K-0001 group [shell-tool] ← O-0006 from S-0002 — below the bar
- K-0001 group [test-failure-triage] ← O-0002 O-0008 from S-0001 S-0002 — at the bar
- K-0001 nominated endpoint-versioning at new-decision → declined; draft dropped
- pass 3 O-0010 [test-failure-triage]: In task curriculum/footer_11 the shell call returned 6 but no observation of the failure was filed, so the task was marked failed.
- pass 3 O-0011 [file-tool]: In task curriculum/newline_03 the first attempt reported 15 lines total, which is incorrect and thus failed the task.
- pass 3 O-0012 [http-tool]: The GET /nodes/36 returned HTTP 410 Gone, preventing verification of the ok field for task curriculum/moved_03.
- pass 3 O-0013 [file-tool]: In task curriculum/csv_04 the first attempt returned 0 Oslo people, which is incorrect, so an observation of the wrong result should have fired.
- pass 3 O-0014 [test-failure-triage]: The first attempt returned 6 parcels, failing the task's pass criteria.
- pass 4 O-0015 [test-failure-triage]: In task curriculum/footer_08 the first attempt summed the amount column to 2312 but did not verify the expected total, missing the required validation observation.
- pass 4 O-0016 [shell-tool]: In task curriculum/newline_10 the single-shell-call attempt returned 13 lines, which is incorrect for the five files.
- pass 4 O-0017 [http-tool]: Task curriculum/token_08 attempted GET /secure/budget without the required token, resulting in HTTP 401 Unauthorized.
- K-0002 group [file-tool] ← O-0002 O-0008 O-0011 O-0013 from S-0001 S-0002 S-0003 — at the bar
- K-0002 group [file-tool, shell-tool] ← O-0016 from S-0004 — below the bar
- K-0002 group [http-tool] ← O-0001 O-0003 O-0005 O-0007 O-0012 from S-0001 S-0002 S-0003 — at the bar
- K-0002 group [http-tool, output-schema] ← O-0009 from S-0002 — below the bar
- K-0002 group [http-tool, tool-budget] ← O-0017 from S-0004 — below the bar
- K-0002 group [output-schema] ← O-0004 from S-0001 — below the bar
- K-0002 group [shell-tool] ← O-0006 from S-0002 — below the bar
- K-0002 group [test-failure-triage] ← O-0010 O-0014 O-0015 from S-0003 S-0004 — at the bar
- K-0002 nominated precision at counterfactual-edit → draft refused at parse: a counterfactual-edit supersedes exactly one record; got []
- K-0002 nominated payload at new-decision → draft refused at parse: not_this: List should have at least 1 item after validation, not 0
- K-0002 nominated recall at hook-edit → draft refused at parse: a hook-edit supersedes exactly one record; got []
- pass 5 O-0018 [output-schema]: In task curriculum/footer_02 the first attempt summed the amount column to 3050 but failed the task due to incorrect output formatting.
- pass 5 O-0019 [file-tool]: In task curriculum/newline_04 the first attempt returned 6 lines, but the task failed because the total line count was incorrect.
- pass 5 O-0020 [output-schema]: The task curriculum/footer_05 attempted to count records but returned 8 as an internal result rather than outputting the plain number, which caused the failure.
- pass 5 O-0021 [test-failure-triage]: The attempt returned 1 but task_pass_rate is 0.0, indicating the active filter was applied incorrectly.
- pass 5 O-0022 [http-tool]: Task curriculum/moved_11 attempted GET /fleets/75, but the API requires the /v2/fleets/75 endpoint; using the correct endpoint would have satisfied the task.
- pass 5 O-0023 [file-tool]: In task curriculum/csv_10 the initial attempt returned 0 because it did not apply a filter for rows where city equals Riga; a correct shell command would have counted those rows.
- pass 6 O-0024 [file-tool]: In task curriculum/newline_06 the first attempt counted lines but got an incorrect total of 21.
- pass 6 O-0025 [file-tool]: In task curriculum/footer_06 the first attempt summed the amount column but returned 3282, which was incorrect, causing the task to fail.
- K-0003 group [file-tool] ← O-0002 O-0008 O-0011 O-0013 O-0019 O-0023 O-0024 O-0025 from S-0001 S-0002 S-0003 S-0005 S-0006 — at the bar
- K-0003 group [file-tool, output-schema] ← O-0018 from S-0005 — below the bar
- K-0003 group [file-tool, shell-tool] ← O-0016 from S-0004 — below the bar
- K-0003 group [file-tool, test-failure-triage] ← O-0015 from S-0004 — below the bar
- K-0003 group [http-tool] ← O-0001 O-0003 O-0005 O-0007 O-0012 O-0022 from S-0001 S-0002 S-0003 S-0005 — at the bar
- K-0003 group [http-tool, output-schema] ← O-0009 from S-0002 — below the bar
- K-0003 group [http-tool, tool-budget] ← O-0017 from S-0004 — below the bar
- K-0003 group [output-schema] ← O-0004 O-0020 from S-0001 S-0005 — at the bar
- K-0003 group [shell-tool] ← O-0006 from S-0002 — below the bar
- K-0003 group [test-failure-triage] ← O-0010 O-0014 O-0021 from S-0003 S-0005 — at the bar
- K-0003 nominated file-tool at new-decision → admitted D-0001
- K-0003 nominated http-tool at new-decision → declined; draft dropped
- K-0003 nominated output-schema at new-decision → declined; draft dropped
- K-0003 nominated test-failure-triage at new-decision → declined; draft dropped
- pass 7 O-0026 [file-tool]: In task curriculum/newline_11 the first attempt did not apply record D-0001, so it did not validate the total line count across all shard files; applying it would have passed.
- pass 7 O-0027 [file-tool]: In task curriculum/newline_08 the attempt counted only some of the shard files, yielding an incorrect total.
- pass 7 O-0028 [test-failure-triage]: In task curriculum/footer_10 the first attempt summed the amount column but did not verify the correct total, causing the task to fail.
- pass 8 O-0029 [http-tool]: Task curriculum/moved_05 attempted GET /stores/24 but got HTTP 410 Gone, missing the required ok field check and thus did not pass.
- pass 8 O-0030 [shell-tool]: Task curriculum/newline_09 attempted to count lines with a single shell call, producing 17 lines, but the correct total requires aggregating all five files, which would need an additional shell call.
- pass 8 O-0031 [test-failure-triage]: In task curriculum/footer_07 the row returned 4 but the evaluation marked the task as failed because no observation was recorded.
- K-0004 group [file-tool, shell-tool] ← O-0016 O-0030 from S-0004 S-0008 — at the bar
- K-0004 group [file-tool, test-failure-triage] ← O-0026 O-0027 from S-0007 — below the bar
- K-0004 group [http-tool] ← O-0001 O-0005 O-0007 O-0012 O-0017 O-0022 from S-0001 S-0002 S-0003 S-0004 S-0005 — at the bar
- K-0004 group [http-tool, output-schema] ← O-0009 from S-0002 — below the bar
- K-0004 group [http-tool, test-failure-triage] ← O-0003 O-0029 from S-0001 S-0008 — at the bar
- K-0004 group [output-schema] ← O-0004 O-0018 O-0020 from S-0001 S-0005 — at the bar
- K-0004 group [shell-tool] ← O-0006 from S-0002 — below the bar
- K-0004 group [shell-tool, test-failure-triage] ← O-0010 from S-0003 — below the bar
- K-0004 group [test-failure-triage] ← O-0014 O-0015 O-0021 O-0028 O-0031 from S-0003 S-0004 S-0005 S-0007 S-0008 — at the bar
- K-0004 nominated precision at counterfactual-edit → escalated to the human queue
- K-0004 nominated http-endpoint-correction at new-decision → draft refused at parse: not_this: List should have at least 1 item after validation, not 0
- K-0004 nominated http-retry-410 at new-decision → draft refused at parse: not_this: List should have at least 1 item after validation, not 0
- K-0004 nominated output-formatting at new-decision → draft refused at parse: not_this: List should have at least 1 item after validation, not 0
- K-0004 nominated test-failure-observation at new-decision → draft refused at parse: not_this: List should have at least 1 item after validation, not 0
- K-0004 nominated L-0001 at counterfactual-edit → moot: retired through the genesis-deadline door
- K-0004 nominated L-0002 at counterfactual-edit → moot: retired through the genesis-deadline door
- K-0004 nominated L-0003 at counterfactual-edit → moot: retired through the genesis-deadline door
- pass 9 O-0032 [test-failure-triage]: In task curriculum/paged_05 the attempt returned 1 without filtering for active invoices, which should have been filtered to count only active ones.
- pass 9 O-0033 [output-schema]: In task curriculum/footer_00 the initial attempt returned a plain numeric sum instead of the required formatted output, causing the task to fail.
- pass 9 O-0034 [file-tool]: In task curriculum/newline_05 the initial attempt counted lines from only one file, yielding 13, but failed to sum all three files as required.
- pass 9 O-0035 [http-tool]: In task curriculum/moved_07 the initial GET request used /agents/14 and got HTTP 410 Gone; the task would have succeeded with a GET to /v2/agents/14 as required by the API versioning convention.
- pass 10 O-0036 [shell-tool]: Task curriculum/newline_07 attempted to count lines with a single shell call but omitted the required validation that both shard files were summed, which violated the convention of confirming the total line count across all shards.
- pass 10 O-0037 [http-tool]: Task curriculum/moved_09 attempted GET /pools/18 on a deprecated endpoint, causing HTTP 410 Gone.
- pass 10 O-0038 [file-tool]: In task curriculum/footer_03 the attempt counted records but omitted the required validation of total line count across all shard files as mandated by decision D-0001.
- K-0005 group [file-tool] ← O-0026 O-0027 O-0034 O-0038 from S-0007 S-0009 S-0010 — at the bar
- K-0005 group [http-tool] ← O-0001 O-0005 O-0007 O-0012 O-0017 O-0022 O-0029 O-0035 O-0037 from S-0001 S-0002 S-0003 S-0004 S-0005 S-0008 S-0009 S-0010 — at the bar
- K-0005 group [http-tool, output-schema] ← O-0009 from S-0002 — below the bar
- K-0005 group [http-tool, test-failure-triage] ← O-0003 from S-0001 — below the bar
- K-0005 group [output-schema] ← O-0004 O-0018 O-0020 O-0033 from S-0001 S-0005 S-0009 — at the bar
- K-0005 group [shell-tool] ← O-0006 O-0016 O-0030 O-0036 from S-0002 S-0004 S-0008 S-0010 — at the bar
- K-0005 group [test-failure-triage] ← O-0010 O-0014 O-0015 O-0021 O-0028 O-0031 O-0032 from S-0003 S-0004 S-0005 S-0007 S-0008 S-0009 — at the bar
- K-0005 nominated precision_file_tool at counterfactual-edit → declined; draft dropped
- K-0005 nominated http_boundary at hook-edit → draft refused at parse: a hook-edit supersedes exactly one record; got []
- K-0005 nominated output_schema_format at new-decision → draft refused at parse: not_this: List should have at least 1 item after validation, not 0
- K-0005 nominated shell_tool_aggregation at new-decision → draft refused at parse: not_this: List should have at least 1 item after validation, not 0
- K-0005 nominated test_failure_reporting at new-decision → draft refused at parse: not_this: List should have at least 1 item after validation, not 0
- pass 11 O-0039 [open]: Task curriculum/newline_02's first attempt counted lines from only part of the shard files; it would have passed by counting all five files.
- pass 11 O-0040 [open]: Task curriculum/footer_09 counted records with a single shell call but omitted the required validation of total line counts across all shard files.
- pass 11 O-0041 [open]: Task curriculum/csv_02 exceeded its shell call budget by making three shell calls instead of the permitted two.
- pass 12 O-0042 [open]: In task curriculum/newline_00 the initial attempt counted lines with a single shell call but omitted the required validation that both shard files be included, which the convention mandates.
- pass 12 O-0043 [open]: In task curriculum/footer_04 the first attempt summed the amount column but did not validate that all shard files were included, missing the required total line‑count check.

## Records

| record | admitted after pass | mentions | decision |
|---|---|---|---|
| D-0001 | 6 | — | Require that file‑tool tasks validate the total line count across all shard files before marking the task successful. |
