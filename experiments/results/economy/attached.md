# economy/attached — evolution

attached on `openai/gpt-oss-120b`; 10 batches × 8 tasks from curriculum, seed 2; revisit [1, 2].

## Passes

| pass | batch | first sight | economy / turns / transfer | symptoms | in context | mentions | filed | consolidation after |
|---|---|---|---|---|---|---|---|---|
| 1 | 1 | 0.50 | 0.26 / 0.27 / 0.00 | naive=4 pass=4 | none | — | 3 obs, 1 prop |  |
| 2 | 2 | 0.62 | 0.36 / 0.38 / — | naive=3 pass=5 | none | — | 2 obs, 1 prop | K-0001: 5 groups, 0 at the bar; admitted nothing; nothing nominated |
| 3 | 3 | 0.38 | 0.21 / 0.21 / — | naive=5 pass=3 | none | — | 4 obs, 1 prop |  |
| 4 | 4 | 0.38 | 0.14 / 0.17 / — | naive=4 pass=3 wrong=1 | none | — | 5 obs, 1 prop | K-0002: 5 groups, 2 at the bar; admitted D-0001; 1 admitted D-0001, 1 declined; draft dropped |
| 5 | 5 | 0.50 | 0.17 / 0.22 / 1.00 | naive=3 pass=4 wrong=1 | none | — | 3 obs, 1 prop |  |
| 6 | 6 | 0.50 | 0.21 / 0.24 / 1.00 | naive=4 pass=4 | none | — | 4 obs, 1 prop | K-0003: 8 groups, 4 at the bar; admitted nothing; 2 declined; draft dropped, 1 draft refused at parse: a hook-edit supersedes exactly one record; got [], 3 draft refused at parse: not_this: List should have at least 1 item after validation, not 0, 1 moot |
| 7 | 7 | 0.50 | 0.21 / 0.24 / 0.00 | naive=3 pass=4 wrong=1 | none | — | 2 obs, 1 prop |  |
| 8 | 8 | 0.38 | 0.12 / 0.13 / 0.00 | naive=5 pass=3 | none | — | 5 obs, 1 prop | K-0004: 8 groups, 6 at the bar; admitted D-0002; 1 admitted D-0002, 7 declined; draft dropped, 1 draft refused at parse: a hook-edit supersedes exactly one record; got [], 3 moot: retired through the genesis-deadline door; retired L-0001 L-0002 L-0003 |
| 9 | 9 | 0.62 | 0.36 / 0.38 / — | naive=3 pass=5 | none | — | 2 obs, 0 prop |  |
| 10 | 10 | 0.38 | 0.21 / 0.21 / — | naive=5 pass=3 | none | — | 4 obs, 1 prop | K-0005: 9 groups, 5 at the bar; admitted D-0003; 1 admitted D-0003, 3 declined; draft dropped, 1 draft refused at parse: a hook-edit supersedes exactly one record; got [] |
| 11 (revisit) | 1 | 0.50 | 0.29 / 0.29 / 1.00 | naive=3 pass=4 wrong=1 | D-0003 | moved-v2: D-0003 | 3 obs, 1 prop |  |
| 12 (revisit) | 2 | 0.62 | 0.36 / 0.38 / 1.00 | naive=3 pass=5 | D-0003 | moved-v2: D-0003 | 3 obs, 1 prop |  |

## Lessons

Each cell is the lesson's rows in that pass: ✓ passed, N the naive first-contact outcome (a same-shape failure), W another wrong answer, E a harness or tool error. `mentioned` marks passes with a record in context whose text uses the lesson's words.

| lesson | tier | p1 | p2 | p3 | p4 | p5 | p6 | p7 | p8 | p9 | p10 | p11r | p12r | first sight | economy / turns / transfer | naive before / after first mention | first mention | revisit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| bom | loud | ✓ | ✓ | ✓ | ✓ | ✓✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 1.00 (11/11) | — / — / — | 0.00 (0/11) / — | — | batch 1: 1/1, batch 2: 1/1 |
| moved-v2 | loud | N | ✓ | N | ✓N | ✓ | ✓ | ✓ | N | ✓ | N | W* | N* | 0.55 (6/11) | 0.28 / 0.37 / — | 0.45 (5/11) / — | — | batch 1: 0/1, batch 2: 0/1 |
| token-route | loud | ✓ | ✓✓ | ✓ | ✓ | W | ✓ | ✓ | ✓ | ✓✓ | ✓ | ✓ | ✓✓ | 0.92 (11/12) | 0.45 / 0.45 / — | 0.00 (0/12) / — | — | batch 1: 1/1, batch 2: 2/2 |
| csv-quoted | visible | ✓ | N | N | N | ✓ | ✓ | N✓ | ✓ | N | N | ✓ | ✓ | 0.45 (5/11) | 0.19 / 0.22 / 0.40 | 0.55 (6/11) / — | — | batch 1: 1/1, batch 2: 1/1 |
| footer-row | visible | N | N | NN | N | N | N | N | N | N | NN | N | N | 0.00 (0/12) | 0.00 / 0.00 / — | 1.00 (12/12) / — | — | batch 1: 0/1, batch 2: 0/1 |
| paged-api | visible | ✓ | ✓ | ✓ | W | N | NN | W | N | ✓ | ✓ | ✓ | ✓ | 0.45 (5/11) | 0.50 / 0.50 / — | 0.36 (4/11) / — | — | batch 1: 1/1, batch 2: 1/1 |
| trailing-newline | invisible | NN | N | N | N | N | N | N | NN | N | N | NN | N | 0.00 (0/12) | 0.00 / 0.00 / — | 1.00 (12/12) / — | — | batch 1: 0/2, batch 2: 0/1 |

## What the passes noticed

Each observation as the close filed it, with the shape the blind coder gave it at the next consolidation (`open` until one has run); a group reaches the bar when its observations come from as many distinct sessions as the bar asks.

- pass 1 O-0001 [file-tool]: The first attempt used a single `wc -l` on all files, which returned per‑file counts instead of the required total line count, causing the task to fail.
- pass 1 O-0002 [output-schema]: In task curriculum/footer_03 the initial attempt counted lines with awk but failed to verify the output schema, causing the task to be marked failed.
- pass 1 O-0003 [http-tool]: The task curriculum/moved_07 tried to GET /agents/14 and return 'ok', but the endpoint returned 410 Gone, so the attempt failed; the correct convention would have been to check for a successful response before extracting the ok field.
- pass 2 O-0004 [file-tool, tool-budget]: The task curriculum/newline_04 ran two wc -l commands separately, which violated the requirement to return the total line count within the budget, leading to failure.
- pass 2 O-0005 [output-schema]: In task curriculum/csv_02 the first awk command printed an empty string for zero matches instead of a numeric 0, violating the convention that a result must always be a number.
- K-0001 group [http-tool, test-failure-triage] ← O-0003 from S-0001 — below the bar
- K-0001 group [output-schema, shell-tool] ← O-0005 from S-0002 — below the bar
- K-0001 group [output-schema, test-failure-triage] ← O-0002 from S-0001 — below the bar
- K-0001 group [shell-tool, test-failure-triage] ← O-0001 from S-0001 — below the bar
- K-0001 group [shell-tool, tool-budget] ← O-0004 from S-0002 — below the bar
- pass 3 O-0006 [output-schema]: In task curriculum/footer_04 the first attempt used awk to compute the sum 3830 but returned a plain number rather than the expected formatted result, violating the output convention.
- pass 3 O-0007 [file-tool, output-schema]: In task curriculum/newline_11 the attempt ran `wc -l capture-1.dat capture-2.dat capture-3.dat` but did not isolate the total line count as a plain number, violating the expected output convention.
- pass 3 O-0008 [output-schema]: In task curriculum/footer_07, the attempt counted the CSV rows with awk and output the number 9, but the required JSON result format was missed.
- pass 3 O-0009 [http-tool]: Task curriculum/moved_01 attempted GET /devices/69 on the wrong API version, causing a 410 Gone error; it should have used the v2 endpoint.
- pass 4 O-0010 [test-failure-triage]: In task curriculum/csv_08 the awk command returned 1 but the task was marked failed, indicating the method_transfer check was missed.
- pass 4 O-0011 [test-failure-triage]: In task curriculum/newline_00 the initial attempt executed wc -l but did not fire a check record to verify the total line count, leading to the task being marked failed.
- pass 4 O-0012 [output-schema]: In task curriculum/footer_11 the first attempt ran `awk 'NR>1' shard-export.csv | wc -l` which counted only data rows (5) but the task expects the total record count including the header, so the attempt was wrong.
- pass 4 O-0013 [http-tool]: Task curriculum/moved_03 attempted GET /nodes/36 and got a 410 Gone error; using the correct /v2/nodes/36 endpoint would have passed.
- pass 4 O-0014 [output-schema]: In task curriculum/paged_10 the initial attempt summed the sensor values incorrectly, yielding 299, which violates the required output schema; a correct sum would have satisfied the schema.
- K-0002 group [http-tool] ← O-0003 O-0009 O-0013 from S-0001 S-0003 S-0004 — at the bar
- K-0002 group [output-schema] ← O-0002 O-0005 O-0006 O-0007 O-0008 O-0012 O-0014 from S-0001 S-0002 S-0003 S-0004 — at the bar
- K-0002 group [shell-tool] ← O-0001 from S-0001 — below the bar
- K-0002 group [task-planning] ← O-0010 O-0011 from S-0004 — below the bar
- K-0002 group [tool-budget] ← O-0004 from S-0002 — below the bar
- K-0002 nominated retry-http-410 at new-decision → admitted D-0001
- K-0002 nominated output-schema-validation at new-decision → declined; draft dropped
- pass 5 O-0015 [file-tool]: In task curriculum/newline_07 the attempt executed wc on each file but did not sum the counts, yielding an incorrect total.
- pass 5 O-0016 [test-failure-triage]: In task curriculum/paged_03 the attempt returned result 1 but task_pass_rate was 0.0, yet no observation was recorded.
- pass 5 O-0017 [http-tool]: Task curriculum/token_07 attempted GET /secure/keys without token, resulting in HTTP 401 Unauthorized.
- pass 6 O-0018 [test-failure-triage]: In task curriculum/paged_01 the attempt returned 2 orders without applying the active:true filter, causing the pass to fail.
- pass 6 O-0019 [output-schema]: In task curriculum/footer_10 the awk command summed the amount column but returned a plain number rather than the expected JSON object, which would have passed.
- pass 6 O-0020 [test-failure-triage]: In task curriculum/paged_11 the first attempt returned the total number of bids (2) without applying the required filter for active true, which should have produced the count of active bids only.
- pass 6 O-0021 [test-failure-triage]: In task curriculum/newline_01 the attempt used a single shell command to count lines but the task failed (task_pass_rate 0.0).
- K-0003 group [file-tool, output-schema] ← O-0002 O-0005 O-0006 O-0007 O-0008 O-0012 O-0019 from S-0001 S-0002 S-0003 S-0004 S-0006 — at the bar
- K-0003 group [file-tool, shell-tool] ← O-0001 from S-0001 — below the bar
- K-0003 group [file-tool, test-failure-triage] ← O-0010 O-0015 from S-0004 S-0005 — at the bar
- K-0003 group [file-tool, tool-budget] ← O-0004 from S-0002 — below the bar
- K-0003 group [http-tool] ← O-0017 from S-0005 — below the bar
- K-0003 group [output-schema] ← O-0014 from S-0004 — below the bar
- K-0003 group [shell-tool, test-failure-triage] ← O-0011 O-0021 from S-0004 S-0006 — at the bar
- K-0003 group [test-failure-triage] ← O-0016 O-0018 O-0020 from S-0005 S-0006 — at the bar
- K-0003 nominated output_schema_enforcement at new-decision → declined; draft dropped
- K-0003 nominated method_transfer_check at new-decision → draft refused at parse: not_this: List should have at least 1 item after validation, not 0
- K-0003 nominated shell_linecount_check at new-decision → draft refused at parse: not_this: List should have at least 1 item after validation, not 0
- K-0003 nominated paged_filter_enforcement at new-decision → draft refused at parse: not_this: List should have at least 1 item after validation, not 0
- K-0003 nominated http_410_retry_hook at hook-edit → declined; draft dropped
- K-0003 nominated bom_11_escape at hook-edit → draft refused at parse: a hook-edit supersedes exactly one record; got []
- K-0003 nominated D-0001 at counterfactual-edit → moot
- pass 7 O-0022 [shell-tool, test-failure-triage]: In task curriculum/footer_09 the first attempt only executed a shell command returning 4 and did not record an observation of the outcome.
- pass 7 O-0023 [test-failure-triage]: In task curriculum/paged_07 the initial attempt returned 4 jobs without applying the required active‑true filter, so the output did not meet the expected schema.
- pass 8 O-0024 [output-schema, shell-tool]: In task curriculum/footer_05 the shell command returned 6 as a raw number, not wrapped in the expected JSON format, causing the task to fail.
- pass 8 O-0025 [output-schema, shell-tool]: The attempt used `cat spool-*.lst | wc -l` and returned 24 but did not wrap it in the required JSON result format, violating the output schema.
- pass 8 O-0026 [test-failure-triage]: The first attempt returned the total parcel count (2) without filtering for active true, causing the task to fail.
- pass 8 O-0027 [http-tool]: Task curriculum/moved_04 tried to GET /plans/49 with the old endpoint, but using the correct /v2/plans/49 would have succeeded.
- pass 8 O-0028 [test-failure-triage]: In task curriculum/newline_08 the first attempt concatenated the three files and counted lines, but it failed to validate the result against the expected total, so a check record should have fired.
- K-0004 group [file-tool, output-schema] ← O-0001 O-0002 O-0005 O-0006 O-0007 O-0008 O-0012 O-0019 from S-0001 S-0002 S-0003 S-0004 S-0006 — at the bar
- K-0004 group [file-tool, test-failure-triage] ← O-0010 O-0028 from S-0004 S-0008 — at the bar
- K-0004 group [file-tool, tool-budget] ← O-0004 O-0015 from S-0002 S-0005 — at the bar
- K-0004 group [http-tool] ← O-0017 O-0027 from S-0005 S-0008 — at the bar
- K-0004 group [output-schema] ← O-0014 from S-0004 — below the bar
- K-0004 group [output-schema, shell-tool] ← O-0024 O-0025 from S-0008 — below the bar
- K-0004 group [shell-tool, test-failure-triage] ← O-0011 O-0022 from S-0004 S-0007 — at the bar
- K-0004 group [test-failure-triage] ← O-0016 O-0018 O-0020 O-0021 O-0023 O-0026 from S-0005 S-0006 S-0007 S-0008 — at the bar
- K-0004 nominated output_schema at new-decision → declined; draft dropped
- K-0004 nominated method_transfer at new-decision → declined; draft dropped
- K-0004 nominated tool_budget at new-decision → declined; draft dropped
- K-0004 nominated http_error at new-decision → declined; draft dropped
- K-0004 nominated numeric_sum at new-decision → declined; draft dropped
- K-0004 nominated json_wrap at new-decision → declined; draft dropped
- K-0004 nominated missing_check at new-decision → declined; draft dropped
- K-0004 nominated filter_active at new-decision → admitted D-0002
- K-0004 nominated boundary at hook-edit → draft refused at parse: a hook-edit supersedes exactly one record; got []
- K-0004 nominated L-0001 at counterfactual-edit → moot: retired through the genesis-deadline door
- K-0004 nominated L-0002 at counterfactual-edit → moot: retired through the genesis-deadline door
- K-0004 nominated L-0003 at counterfactual-edit → moot: retired through the genesis-deadline door
- pass 9 O-0029 [output-schema]: The awk command summed the amount column to 1906 but the task was marked failed due to incorrect output format.
- pass 9 O-0030 [output-schema]: In task curriculum/csv_00 the first awk command counted all rows including the header, whereas the convention requires skipping the header (NR>1).
- pass 10 O-0031 [shell-tool, test-failure-triage]: Task curriculum/footer_01 ran a shell command to count CSV rows but did not generate an observation to confirm the result, missing the required record.
- pass 10 O-0032 [test-failure-triage]: The awk command returned 1 but no verification was performed to confirm the count.
- pass 10 O-0033 [http-tool, test-failure-triage]: The task curriculum/moved_09 attempted GET /pools/18, received HTTP 410 Gone, so the attempt failed to verify the 'ok' field.
- pass 10 O-0034 [test-failure-triage]: Task curriculum/newline_02 attempted wc command but no observation was recorded, causing the pass to miss the error.
- K-0005 group [file-tool] ← O-0001 O-0015 from S-0001 S-0005 — at the bar
- K-0005 group [file-tool, output-schema] ← O-0007 from S-0003 — below the bar
- K-0005 group [file-tool, tool-budget] ← O-0004 from S-0002 — below the bar
- K-0005 group [http-tool] ← O-0017 O-0027 from S-0005 S-0008 — at the bar
- K-0005 group [http-tool, test-failure-triage] ← O-0033 from S-0010 — below the bar
- K-0005 group [output-schema] ← O-0002 O-0005 O-0006 O-0008 O-0012 O-0014 O-0019 O-0029 O-0030 from S-0001 S-0002 S-0003 S-0004 S-0006 S-0009 — at the bar
- K-0005 group [output-schema, shell-tool] ← O-0024 O-0025 from S-0008 — below the bar
- K-0005 group [shell-tool, test-failure-triage] ← O-0022 O-0031 from S-0007 S-0010 — at the bar
- K-0005 group [test-failure-triage] ← O-0010 O-0011 O-0028 O-0032 O-0034 from S-0004 S-0008 S-0010 — at the bar
- K-0005 nominated line-count at new-decision → declined; draft dropped
- K-0005 nominated output-format at new-decision → declined; draft dropped
- K-0005 nominated budget at new-decision → declined; draft dropped
- K-0005 nominated http-auth at hook-edit → draft refused at parse: a hook-edit supersedes exactly one record; got []
- K-0005 nominated http-410 at hook-edit → admitted D-0003
- pass 11 O-0035 [open]: In task curriculum/newline_09 the initial attempt executed wc -l on the five files but returned the raw wc output instead of isolating the total line count, causing the task to fail.
- pass 11 O-0036 [open]: The task curriculum/newline_03's first attempt did not verify that the shell output was a plain number, leading to a failed pass.
- pass 11 O-0037 [open]: Task curriculum/footer_03 tried to count CSV records with a shell command, but the consulted record D-0003 (an HTTP‑410 hook) was applied, which was inappropriate for this task.
- pass 12 O-0038 [open]: In task curriculum/newline_04 the first attempt consulted D-0003, which is unrelated to the shell‑tool line‑count, causing the failure.
- pass 12 O-0039 [open]: In task curriculum/footer_06 the first attempt summed the amount column with awk but did not verify the result, so it failed.
- pass 12 O-0040 [open]: In task curriculum/moved_05 the first attempt applied D-0003 after the GET /stores/24 returned 410, but the hook should have been checked before the call to abort on 410.

## Records

| record | admitted after pass | mentions | decision |
|---|---|---|---|
| D-0001 | 4 | moved-v2 | Enforce a retry policy for HTTP 410 Gone responses, allowing up to two attempts before declaring failure. |
| D-0002 | 8 | paged-api | Require that every paged query include an active:true filter before counting results. |
| D-0003 | 10 | moved-v2 | Introduce a hook that checks for HTTP 410 responses and aborts further tool calls for the affected task. |
