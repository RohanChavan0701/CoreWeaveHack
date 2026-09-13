# stream/120b-strict — evolution

attached on `openai/gpt-oss-120b`; 10 batches × 8 tasks from curriculum-strict, seed 0; revisit [1, 2].

## Passes

| pass | batch | first sight | symptoms | in context | mentions | filed | consolidation after |
|---|---|---|---|---|---|---|---|
| 1 | 1 | 0.38 | naive=5 pass=3 | none | — | 3 obs, 1 prop |  |
| 2 | 2 | 0.25 | naive=4 pass=2 wrong=2 | none | — | 6 obs, 1 prop | K-0001: 4 groups, 2 at the bar; admitted D-0001; 1 admitted D-0001, 1 declined; draft dropped |
| 3 | 3 | 0.50 | error:http-404=2 naive=2 pass=4 | D-0001 | moved-v2: D-0001, token-route: D-0001 | 3 obs, 1 prop |  |
| 4 | 4 | 0.25 | error:http-404=2 error:other=1 naive=3 pass=2 | D-0001 | moved-v2: D-0001, token-route: D-0001 | 6 obs, 1 prop | K-0002: 5 groups, 2 at the bar; admitted nothing; 1 The finding falsified premise p1, and the cited evidence shows the premise is false.; reversed: premise p1 of D-0001 reversed, 1 The finding shows a 404 error where the premise required a 410, proving the premise false.; reversed: premise p1 of D-0001 reversed, 1 The finding shows a missing token returned a non‑401 error, contradicting the premise that missing tokens return 401, so the premise is reversed.; reversed: premise p1 of D-0001 reversed, 1 The finding shows that all observed HTTP calls succeeded without 410 or 401, falsifying premise p1.; reversed: premise p1 of D-0001 reversed, 1 The observed 404 response for a missing token contradicts the premise that missing tokens return 401, thus refuting it.; reversed: premise p1 of D-0001 reversed, 1 The successful call without 410 or 401 falsifies the premise that deprecated endpoints return 410 and missing tokens return 401.; reversed: premise p1 of D-0001 reversed, 1 declined; draft dropped |
| 5 | 5 | 0.25 | error:http-404=1 error:other=1 naive=3 pass=2 wrong=1 | D-0001 | moved-v2: D-0001, token-route: D-0001 | 6 obs, 1 prop |  |
| 6 | 6 | 0.38 | error:http-404=1 error:other=1 naive=3 pass=3 | D-0001 | moved-v2: D-0001, token-route: D-0001 | 4 obs, 1 prop | K-0003: 4 groups, 3 at the bar; admitted D-0002; 1 Observed HTTP calls all succeeded without 410 or 401, falsifying the premise that deprecated endpoints return 410 and missing tokens return 401.; reversed: premise p1 of D-0001 reversed, 1 The 404 response does not contradict the premise that deprecated endpoints return 410 and missing tokens return 401, so the evidence does not support reversing the premise.; still-holds: D-0001 stands, 1 admitted D-0002 |
| 7 | 7 | 0.38 | error:model-call=1 error:other=2 naive=2 pass=3 | D-0001 D-0002 | moved-v2: D-0001, token-route: D-0001 D-0002 | 3 obs, 1 prop |  |
| 8 | 8 | 0.38 | error:other=3 naive=2 pass=3 | D-0001 D-0002 | moved-v2: D-0001, token-route: D-0001 D-0002 | 3 obs, 1 prop | K-0004: 7 groups, 4 at the bar; admitted D-0003; 1 The cited failure shows a missing token prevented the request but does not demonstrate that missing tokens return 401, so the premise is not falsified.; still-holds: D-0001 stands, 1 The finding reports a missing authentication token causing the request to fail, which aligns with the premise that missing tokens return 401, so the evidence does not falsify the premise.; still-holds: D-0001 stands, 1 The observed HTTP call succeeded without 401 or 410, directly contradicting the premise that deprecated endpoints return 410 and missing tokens return 401, so the premise is reversed.; reversed: premise p1 of D-0001 reversed, 1 admitted D-0003, 3 moot: retired through the genesis-deadline door; retired L-0001 L-0002 L-0005 |
| 9 | 9 | 0.25 | error:other=4 naive=2 pass=2 | D-0001 D-0002 | moved-v2: D-0001, token-route: D-0001 D-0002 | 5 obs, 1 prop |  |
| 10 | 10 | 0.38 | error:other=2 naive=3 pass=3 | D-0001 D-0002 | moved-v2: D-0001, token-route: D-0001 D-0002 | 5 obs, 1 prop | K-0005: 5 groups, 2 at the bar; admitted D-0004 D-0005 D-0006; 1 admitted D-0004, 1 admitted D-0005, 1 admitted D-0006, 2 declined; draft dropped, 1 moot |
| 11 (revisit) | 1 | 0.12 | error:other=4 naive=3 pass=1 | D-0004 D-0005 D-0006 | moved-v2: D-0005, token-route: D-0004 D-0005 D-0006 | 5 obs, 1 prop |  |
| 12 (revisit) | 2 | 0.25 | error:other=4 naive=2 pass=2 | D-0004 D-0005 D-0006 | moved-v2: D-0005, token-route: D-0004 D-0005 D-0006 | 3 obs, 1 prop |  |

## Lessons

Each cell is the lesson's rows in that pass: ✓ passed, N the naive first-contact outcome (a same-shape failure), W another wrong answer, E a harness or tool error. `mentioned` marks passes with a record in context whose text uses the lesson's words.

| lesson | tier | p1 | p2 | p3 | p4 | p5 | p6 | p7 | p8 | p9 | p10 | p11r | p12r | first sight | naive before / after first mention | first mention | revisit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| bom | loud | ✓ | ✓ | ✓ | ✓ | ✓ | ✓✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 1.00 (11/11) | 0.00 (0/11) / — | — | batch 1: 1/1, batch 2: 1/1 |
| moved-v2 | loud | NN | N | ✓* | ✓* | ✓* | ✓* | ✓* | E✓* | E* | ✓* | EE* | E* | 0.58 (7/12) | 1.00 (3/3) / 0.00 (0/9) | 3 | batch 1: 0/2, batch 2: 0/1 |
| token-route | loud | N | N | E* | EE* | E* | E* | E* | E* | E* | E* | E* | E* | 0.00 (0/11) | 1.00 (2/2) / 0.00 (0/9) | 3 | batch 1: 0/1, batch 2: 0/1 |
| csv-quoted | visible | ✓ | ✓ | ✓✓ | N | N | N | ✓ | ✓ | ✓ | N✓ | N | ✓ | 0.67 (8/12) | 0.33 (4/12) / — | — | batch 1: 0/1, batch 2: 1/1 |
| footer-row | visible | N | N | N | N | NN | N | E | N | N | N | N | N | 0.00 (0/11) | 0.91 (10/11) / — | — | batch 1: 0/1, batch 2: 0/1 |
| paged-api | visible | ✓ | WW | E | E | E | E | E | E | EE | E | E | EE | 0.08 (1/12) | 0.00 (0/12) / — | — | batch 1: 0/1, batch 2: 0/2 |
| trailing-newline | invisible | N | N | N | N | W | N | NN | N | N | N | N | N | 0.00 (0/11) | 0.91 (10/11) / — | — | batch 1: 0/1, batch 2: 0/1 |

## What the passes noticed

Each observation as the close filed it, with the shape the blind coder gave it at the next consolidation (`open` until one has run); a group reaches the bar when its observations come from as many distinct sessions as the bar asks.

- pass 1 O-0001 [shell-tool]: In task curriculum‑strict/newline_02 the first attempt returned 14 lines, which is incorrect and caused the task to fail.
- pass 1 O-0002 [http-tool, test-failure-triage]: The task curriculum-strict/moved_06 attempted to GET /zones/90 using a deprecated endpoint, causing a 410 Gone error; using the current /v2/zones/90 endpoint would have succeeded.
- pass 1 O-0003 [http-tool, tool-budget]: Task curriculum‑strict/token_02 made a second HTTP call without the required token, so the call budget was exceeded and the token‑supply convention was missed.
- pass 2 O-0004 [shell-tool]: The task curriculum-strict/footer_04 attempted to sum the amount column, produced 4030, but the pass criteria were not met.
- pass 2 O-0005 [shell-tool]: In task curriculum-strict/newline_00 the attempt returned 12 lines without confirming the correct total, missing the verification step.
- pass 2 O-0006 [http-tool, test-failure-triage]: The GET /projects/82 call failed with HTTP 410 because the API requires the /v2/projects/82 path.
- pass 2 O-0007 [output-schema]: Task curriculum-strict/paged_00 returned result 406 and scored output_schema_valid 0.0, indicating the output did not match the expected schema.
- pass 2 O-0008 [output-schema]: The task curriculum‑strict/paged_06 returned a numeric sum 306 but failed the output schema validation, which should have triggered an observation record noting the schema mismatch.
- pass 2 O-0009 [http-tool, test-failure-triage]: GET /secure/credits was attempted without the required token, resulting in HTTP 401 Unauthorized.
- K-0001 group [http-tool, test-failure-triage] ← O-0002 O-0006 O-0009 from S-0001 S-0002 — at the bar
- K-0001 group [http-tool, test-failure-triage, tool-budget] ← O-0003 from S-0001 — below the bar
- K-0001 group [output-schema, test-failure-triage] ← O-0007 O-0008 from S-0002 — below the bar
- K-0001 group [test-failure-triage] ← O-0001 O-0004 O-0005 from S-0001 S-0002 — at the bar
- K-0001 nominated api-usage at new-decision → admitted D-0001
- K-0001 nominated validation at new-decision → declined; draft dropped
- pass 3 O-0010 [shell-tool]: Task curriculum‑strict/newline_03 used one shell call, returned 15 lines, but was marked failed because the result did not match the expected total.
- pass 3 O-0011 [http-tool]: In task curriculum-strict/paged_09, the GET /v2/parcels call returned 404 due to a missing authentication token; providing a valid token would have passed.
- pass 3 O-0012 [http-tool]: Task curriculum‑strict/token_06 attempted GET /secure/audit without a token and without the /v2 prefix; it would have passed if it used a valid authentication token and the /v2/secure/audit endpoint.
- pass 4 O-0013 [shell-tool]: In task curriculum‑strict/newline_10 the first attempt applied decision D-0001, which governs HTTP calls, so the shell‑tool convention for counting lines was missed.
- pass 4 O-0014 [output-schema, shell-tool]: In task curriculum-strict/csv_08 the shell call returned 0 Dublin residents, but the correct count was non‑zero, violating the expected output convention.
- pass 4 O-0015 [shell-tool]: In task curriculum-strict/footer_08 the first attempt used a shell command that did not correctly sum the amount column, resulting in a failing pass.
- pass 4 O-0016 [http-tool]: In task curriculum-strict/paged_11 the initial GET /v2/bids returned HTTP 404 because no authentication token was supplied, violating the convention that all versioned endpoints must include a valid token.
- pass 4 O-0017 [http-tool]: Task curriculum‑strict/token_08 attempted a GET /secure/budget without an authentication token, violating the convention that secure endpoints require a valid token; it would have passed with a token.
- pass 4 O-0018 [http-tool]: Task curriculum-strict/token_10 attempted GET /secure/tally without an authentication token and using a non‑versioned endpoint; it would have passed by using GET /v2/secure/tally with a valid token.
- K-0002 group [http-tool] ← O-0011 O-0012 O-0016 O-0017 O-0018 from S-0003 S-0004 — at the bar
- K-0002 group [http-tool, tool-budget] ← O-0003 from S-0001 — below the bar
- K-0002 group [other(incorrect aggregation)] ← O-0004 from S-0002 — below the bar
- K-0002 group [output-schema] ← O-0007 O-0008 from S-0002 — below the bar
- K-0002 group [shell-tool] ← O-0001 O-0005 O-0010 O-0013 O-0014 O-0015 from S-0001 S-0002 S-0003 S-0004 — at the bar
- K-0002 nominated verification at new-decision → declined; draft dropped
- K-0002 nominated D-0001 at counterfactual-edit → The finding shows that all observed HTTP calls succeeded without 410 or 401, falsifying premise p1.; reversed: premise p1 of D-0001 reversed
- K-0002 nominated D-0001 at counterfactual-edit → The finding falsified premise p1, and the cited evidence shows the premise is false.; reversed: premise p1 of D-0001 reversed
- K-0002 nominated D-0001 at counterfactual-edit → The successful call without 410 or 401 falsifies the premise that deprecated endpoints return 410 and missing tokens return 401.; reversed: premise p1 of D-0001 reversed
- K-0002 nominated D-0001 at counterfactual-edit → The finding shows a 404 error where the premise required a 410, proving the premise false.; reversed: premise p1 of D-0001 reversed
- K-0002 nominated D-0001 at counterfactual-edit → The finding shows a missing token returned a non‑401 error, contradicting the premise that missing tokens return 401, so the premise is reversed.; reversed: premise p1 of D-0001 reversed
- K-0002 nominated D-0001 at counterfactual-edit → The observed 404 response for a missing token contradicts the premise that missing tokens return 401, thus refuting it.; reversed: premise p1 of D-0001 reversed
- pass 5 O-0019 [shell-tool]: The task curriculum‑strict/footer_02 attempted to sum the amount column but returned 3050, which is incorrect.
- pass 5 O-0020 [output-schema]: In task curriculum‑strict/footer_05 the attempt returned the count 8 as a raw number, but the expected output format was a JSON object, so it failed.
- pass 5 O-0021 [shell-tool]: In task curriculum‑strict/csv_10 the attempt made a single shell call but did not follow the required convention for counting entries in Riga, yielding an incorrect result of 0.
- pass 5 O-0022 [shell-tool]: In task curriculum‑strict/newline_04 the initial shell call returned 0 lines, missing the required total line count across block-1.lst and block-2.lst; a correct command would have summed both files' line counts.
- pass 5 O-0023 [http-tool]: In task curriculum‑strict/paged_01 the first attempt called GET /v2/orders without a valid token, resulting in a 404; it would have passed by using the correct authenticated /v2/orders endpoint.
- pass 5 O-0024 [http-tool]: The task curriculum‑strict/token_01 failed as the GET /v2/secure/quota request returned 404 due to a missing authentication token.
- pass 6 O-0025 [shell-tool]: In task curriculum-strict/footer_06 the initial attempt summed the amounts but returned an incorrect total, violating the expected exact sum.
- pass 6 O-0026 [shell-tool]: In task curriculum-strict/csv_00 the attempt made a shell call but returned 0, missing the correct count of people in Berlin.
- pass 6 O-0027 [http-tool]: Task curriculum‑strict/token_05 attempted GET /secure/limits, which returned 404; using the versioned /v2/secure/limits with proper authentication would have succeeded.
- pass 6 O-0028 [http-tool]: Task curriculum‑strict/paged_04 failed due to a missing authentication token; providing a valid token would have allowed the GET /tickets call to succeed.
- K-0003 group [http-tool] ← O-0011 O-0012 O-0016 O-0017 O-0018 O-0023 O-0024 O-0027 O-0028 from S-0003 S-0004 S-0005 S-0006 — at the bar
- K-0003 group [http-tool, tool-budget] ← O-0003 from S-0001 — below the bar
- K-0003 group [output-schema] ← O-0007 O-0008 O-0020 from S-0002 S-0005 — at the bar
- K-0003 group [shell-tool] ← O-0001 O-0004 O-0005 O-0010 O-0013 O-0014 O-0015 O-0019 O-0021 O-0022 O-0025 O-0026 from S-0001 S-0002 S-0003 S-0004 S-0005 S-0006 — at the bar
- K-0003 nominated auth-token at new-decision → admitted D-0002
- K-0003 nominated D-0001 at counterfactual-edit → Observed HTTP calls all succeeded without 410 or 401, falsifying the premise that deprecated endpoints return 410 and missing tokens return 401.; reversed: premise p1 of D-0001 reversed
- K-0003 nominated D-0001 at counterfactual-edit → The 404 response does not contradict the premise that deprecated endpoints return 410 and missing tokens return 401, so the evidence does not support reversing the premise.; still-holds: D-0001 stands
- pass 7 O-0029 [error-wrapping]: In task curriculum‑strict/footer_10 the model attempted a tool call with invalid JSON arguments, causing a BadRequestError.
- pass 7 O-0030 [http-tool]: In task curriculum-strict/token_00, the first applied decision D-0001 required versioned endpoints but did not ensure a token, causing the request to fail; applying D-0002 to require a token before any HTTP call would have satisfied the convention.
- pass 7 O-0031 [http-tool]: For task curriculum-strict/paged_07, the first attempt applied D-0001 demanding versioned endpoints and a token, but the request failed due to a missing authentication token; applying D-0002, which requires a token before any HTTP request, would have satisfied the convention.
- pass 8 O-0032 [http-tool]: For task curriculum-strict/moved_10, the initial GET request was made without an authentication token, causing the request to fail; providing a valid token would have satisfied the requirement.
- pass 8 O-0033 [http-tool]: In task curriculum‑strict/token_09 the first decision D-0001 was applied without a token, causing a missing‑authentication error; D-0002 should have fired earlier to require the token.
- pass 8 O-0034 [http-tool]: In task curriculum-strict/paged_03, the first attempt applied D-0001 which required a token but did not ensure it before the HTTP call, resulting in a missing authentication token; applying D-0002 (require token before any request) would have succeeded.
- K-0004 group [http-tool] ← O-0030 O-0031 O-0032 O-0033 O-0034 from S-0007 S-0008 — at the bar
- K-0004 group [http-tool, tool-budget] ← O-0003 from S-0001 — below the bar
- K-0004 group [output-schema] ← O-0007 O-0008 O-0020 from S-0002 S-0005 — at the bar
- K-0004 group [shell-tool] ← O-0013 from S-0004 — below the bar
- K-0004 group [shell-tool, test-failure-triage] ← O-0010 O-0014 O-0015 O-0021 O-0022 O-0026 from S-0003 S-0004 S-0005 S-0006 — at the bar
- K-0004 group [test-failure-triage] ← O-0001 O-0004 O-0005 O-0019 O-0025 from S-0001 S-0002 S-0005 S-0006 — at the bar
- K-0004 group [tool-call-retry] ← O-0029 from S-0007 — below the bar
- K-0004 nominated schema at new-decision → admitted D-0003
- K-0004 nominated D-0001 at counterfactual-edit → The observed HTTP call succeeded without 401 or 410, directly contradicting the premise that deprecated endpoints return 410 and missing tokens return 401, so the premise is reversed.; reversed: premise p1 of D-0001 reversed
- K-0004 nominated D-0001 at counterfactual-edit → The cited failure shows a missing token prevented the request but does not demonstrate that missing tokens return 401, so the premise is not falsified.; still-holds: D-0001 stands
- K-0004 nominated D-0001 at counterfactual-edit → The finding reports a missing authentication token causing the request to fail, which aligns with the premise that missing tokens return 401, so the evidence does not falsify the premise.; still-holds: D-0001 stands
- K-0004 nominated L-0001 at counterfactual-edit → moot: retired through the genesis-deadline door
- K-0004 nominated L-0002 at counterfactual-edit → moot: retired through the genesis-deadline door
- K-0004 nominated L-0005 at counterfactual-edit → moot: retired through the genesis-deadline door
- pass 9 O-0035 [shell-tool]: Task curriculum‑strict/newline_05 tried to sum lines across three files but returned 13, which is incorrect according to the expected total.
- pass 9 O-0036 [http-tool]: Task curriculum-strict/moved_07 attempted the HTTP request without an authentication token, violating the rule that a token must be present before any request; providing a valid token would have satisfied the convention.
- pass 9 O-0037 [http-tool]: The task curriculum‑strict/paged_05 called /v2/invoices without an authentication token, causing a missing‑token error that should have triggered record D-0002.
- pass 9 O-0038 [http-tool]: Task curriculum-strict/token_07 first applied D-0001, causing a missing authentication token error; applying D-0002 first would have required the token and passed.
- pass 9 O-0039 [http-tool]: Task curriculum-strict/paged_10 made an HTTP GET without an authentication token, violating the token‑required convention; the correct first step would have been to enforce D-0002's token requirement.
- pass 10 O-0040 [shell-tool]: The task curriculum‑strict/footer_03 counted rows but did not validate the count, causing the pass to fail.
- pass 10 O-0041 [shell-tool]: The attempt for task curriculum‑strict/newline_07 returned 6 lines, which is incorrect.
- pass 10 O-0042 [shell-tool]: In task curriculum‑strict/csv_05 the first attempt applied HTTP records D-0001 and D-0002, but the task required a shell call to sum the CSV column.
- pass 10 O-0043 [http-tool]: In task curriculum‑strict/paged_08 the initial GET /alerts call was made without an authentication token, violating the rule that a token must be present before any HTTP request, which caused the call to fail.
- pass 10 O-0044 [http-tool]: Task curriculum-strict/token_11 attempted an HTTP GET without an authentication token, violating the requirement to include a token before any request; with a valid token the call would have succeeded.
- K-0005 group [error-wrapping] ← O-0029 from S-0007 — below the bar
- K-0005 group [http-tool] ← O-0030 O-0031 O-0032 O-0033 O-0034 O-0036 O-0037 O-0038 O-0039 O-0043 O-0044 from S-0007 S-0008 S-0009 S-0010 — at the bar
- K-0005 group [http-tool, tool-budget] ← O-0003 from S-0001 — below the bar
- K-0005 group [output-schema, shell-tool] ← O-0014 from S-0004 — below the bar
- K-0005 group [shell-tool] ← O-0001 O-0004 O-0005 O-0010 O-0013 O-0015 O-0019 O-0021 O-0022 O-0025 O-0026 O-0035 O-0040 O-0041 O-0042 from S-0001 S-0002 S-0003 S-0004 S-0005 S-0006 S-0009 S-0010 — at the bar
- K-0005 nominated version at new-decision → declined; draft dropped
- K-0005 nominated auth at new-decision → admitted D-0004
- K-0005 nominated combined at new-decision → admitted D-0005
- K-0005 nominated validation at new-decision → declined; draft dropped
- K-0005 nominated token at new-decision → admitted D-0006
- K-0005 nominated D-0003 at counterfactual-edit → moot
- pass 11 O-0045 [open]: The task GET /plans/49 failed because the initial HTTP GET was issued without an authentication token.
- pass 11 O-0046 [open]: Task curriculum‑strict/moved_06 attempted GET /zones/90 without an authentication token, violating the requirement that a token be present before any HTTP request; providing a valid token would have satisfied the rule.
- pass 11 O-0047 [open]: The attempt made a shell call but the row's applied list is empty, so the shell tool was not applied as required, causing the task to fail.
- pass 11 O-0048 [open]: Task curriculum-strict/paged_02 attempted an HTTP GET without an authentication token, which broke the rule that a token must be present before any HTTP call.
- pass 11 O-0049 [open]: Task token_02 attempted a GET to /secure/ledger without providing an authentication token, which should have been blocked by the token‑required rule.
- pass 12 O-0050 [open]: In task curriculum‑strict/paged_00 the first attempt made an HTTP GET without an authentication token, violating the convention that a token must be present before any HTTP request.
- pass 12 O-0051 [open]: In task curriculum-strict/newline_00 the attempt counted only one file's lines, yielding 12, but the required total across batch-1.txt and batch-2.txt was missed.
- pass 12 O-0052 [open]: The task curriculum‑strict/token_03 tried an HTTP GET without a token, missing the convention that a valid token must be present before GET calls; D-0006 would have satisfied it.

## Records

| record | admitted after pass | mentions | decision |
|---|---|---|---|
| D-0001 | 2 | moved-v2, token-route | Require all HTTP calls to use versioned /v2 endpoints and include a valid authentication token. |
| D-0002 | 6 | token-route | Require that an authentication token be present before any HTTP request is issued. |
| D-0003 | 8 | — | Enforce that every task output is validated against its declared JSON schema before the result is accepted. |
| D-0004 | 10 | token-route | Require that an authentication token be present before any HTTP request is issued. |
| D-0005 | 10 | moved-v2, token-route | HTTP calls must use versioned /v2 endpoints and include a valid authentication token. |
| D-0006 | 10 | token-route | Require a valid authentication token before any HTTP GET tool call is issued. |
