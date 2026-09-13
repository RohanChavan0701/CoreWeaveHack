# text2sql/120b-attached — evolution

attached on `openai/gpt-oss-120b`; 8 batches × 2 tasks from text2sql+text2sql-holdout, seed 0; revisit [1, 2].

## Passes

| pass | batch | first sight | economy / turns / transfer | symptoms | in context | mentions | filed | consolidation after |
|---|---|---|---|---|---|---|---|---|
| 1 | 1 | 0.50 | 0.25 / 0.33 / — | error:not-json=1 pass=1 | none | — | 2 obs, 1 prop |  |
| 2 | 2 | 0.50 | 0.17 / 0.25 / — | pass=1 wrong=1 | none | — | 2 obs, 1 prop | K-0001: 4 groups, 0 at the bar; admitted nothing; 4 refused by the floor: 1 distinct session |
| 3 | 3 | 0.00 | 0.00 / 0.00 / — | wrong=2 | none | — | 4 obs, 1 prop |  |
| 4 | 4 | 0.00 | 0.00 / 0.00 / — | wrong=2 | none | — | 4 obs, 1 prop | K-0002: 8 groups, 1 at the bar; admitted D-0001; 1 admitted D-0001, 2 decline |
| 5 | 5 | 0.50 | 0.50 / 0.50 / — | pass=1 wrong=1 | none | — | 2 obs, 0 prop |  |
| 6 | 6 | 1.00 | 1.00 / 1.00 / — | pass=2 | none | — | 0 obs, 1 prop | K-0003: 9 groups, 0 at the bar; admitted D-0002 D-0003 D-0004; 1 admitted D-0002, 1 admitted D-0003, 1 admitted D-0004, 1 decline |
| 7 | 7 | 0.00 | 0.00 / 0.00 / — | error:not-json=1 wrong=1 | D-0002 | — | 3 obs, 1 prop |  |
| 8 | 8 | 0.50 | 0.17 / 0.25 / — | pass=1 wrong=1 | D-0002 | — | 2 obs, 1 prop | K-0004: 2 groups, 1 at the bar; admitted D-0005 D-0006 D-0007; 1 The cited anchor is not rotted, the premises are supported, and the finding does not provide evidence that the premise is false.; still-holds: D-0002 stands, 1 admitted D-0005, 1 admitted D-0006, 1 admitted D-0007, 1 decline, 4 moot: retired through the genesis-deadline door, 2 still-holds: kept; retired L-0001 L-0010 L-0006 L-0007 |
| 9 (revisit) | 1 | 0.50 | 0.17 / 0.25 / — | error:not-json=1 pass=1 | D-0002 D-0005 D-0006 D-0007 | — | 0 obs, 0 prop |  |
| 10 (revisit) | 2 | 0.00 | 0.00 / 0.00 / — | wrong=2 | D-0002 D-0005 D-0006 D-0007 | — | 2 obs, 1 prop |  |

## Lessons

Each cell is the lesson's rows in that pass: ✓ passed, N the naive first-contact outcome (a same-shape failure), W another wrong answer, E a harness or tool error. `mentioned` marks passes with a record in context whose text uses the lesson's words.

| lesson | tier | p1 | p2 | p3 | p4 | p5 | p6 | p7 | p8 | p9r | p10r | first sight | economy / turns / transfer | naive before / after first mention | first mention | revisit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| text2sql | — | E | ✓ | W | W | ✓ | ✓ | WE | ✓W | E | W | 0.40 (4/10) | 0.31 / 0.34 / — | 0.00 (0/10) / — | — | batch 1: 0/1, batch 2: 0/1 |
| text2sql-holdout | — | ✓ | W | W | W | W | ✓ |  |  | ✓ | W | 0.33 (2/6) | 0.25 / 0.28 / — | 0.00 (0/6) / — | — | batch 1: 1/1, batch 2: 0/1 |

## What the passes noticed

Each observation as the close filed it, with the shape the blind coder gave it at the next consolidation (`open` until one has run); a group reaches the bar when its observations come from as many distinct sessions as the bar asks.

- pass 1 O-0001 [output-schema]: In task text2sql/q92 the initial attempt ran only "sqlite3 financial.sqlite \".schema\"" and did not output a SELECT statement, which is required.
- pass 1 O-0002 [output-schema]: Task text2sql/q92 failed with error: final reply was not JSON.
- pass 2 O-0003 [output-schema]: In task text2sql-holdout/q168 the first attempt produced a computed result rather than the SQL query text, violating the convention that the answer must be the query itself.
- pass 2 O-0004 [other(no store records consulted)]: Task text2sql‑holdout/q168 failed without consulting any store records.
- K-0001 group [other(answer must be the query text, not a computed result)] ← O-0003 from S-0002 — below the bar
- K-0001 group [other(failed without consulting store records)] ← O-0004 from S-0002 — below the bar
- K-0001 group [other(output format not JSON)] ← O-0002 from S-0001 — below the bar
- K-0001 group [output-schema] ← O-0001 from S-0001 — below the bar
- K-0001 nominated output-schema at new-decision → refused by the floor: 1 distinct session(s) in the evidence (S-0001) against the bar 2; the adjudicator's decline(insufficient independence) was overridden: a decline stands only on an upheld premise kill
- K-0001 nominated query-text-output at new-decision → refused by the floor: 1 distinct session(s) in the evidence (S-0002) against the bar 2; the adjudicator's decline(insufficient independence) was overridden: a decline stands only on an upheld premise kill
- K-0001 nominated consult-store-records at new-decision → refused by the floor: 1 distinct session(s) in the evidence (S-0002) against the bar 2; the adjudicator's decline(insufficient independence: the draft rests on one session against a bar of two) was overridden: a decline stands only on an upheld premise kill
- K-0001 nominated json-output-format at new-decision → refused by the floor: 1 distinct session(s) in the evidence (S-0001) against the bar 2; the adjudicator's decline(warrant:independence landed: the draft is anchored on a single session (S-0001) against the bar of 2 distinct sessions, so the floor refuses it.) was overridden: a decline stands only on an upheld premise kill
- pass 3 O-0005 [other(EXISTS vs all-transactions requirement)]: The attempt used EXISTS, which checks only for any 'POPLATEK PO OBRATU' transaction rather than requiring all transactions to be of that type, violating the task's requirement.
- pass 3 O-0006 [other(missing column a.date, should use trans table date)]: In task text2sql/q119 the query referenced a missing column a.date; the correct convention is to use the transaction date from the trans table.
- pass 3 O-0007 [other(no matching rule)]: Task text2sql-holdout/q192 failed with no matching rule.
- pass 3 O-0008 [other(no matching rule)]: Task text2sql/q119 failed with no matching rule.
- pass 4 O-0009 [other(district vs client average salary)]: The attempt used district.A11 to represent average salary, but the task required the lowest average salary per client, not per district.
- pass 4 O-0010 [output-schema]: In task text2sql/q136 the attempt produced a SELECT statement but did not trigger the check record that compares the query output to the expected rows.
- pass 4 O-0011 [other(no applicable rule)]: Task text2sql-holdout/q189 failed with no applicable rule.
- pass 4 O-0012 [other(no applicable rule)]: Task text2sql/q136 failed with no applicable rule.
- K-0002 group [other(check record not triggered)] ← O-0010 from S-0004 — below the bar
- K-0002 group [other(incorrect logical condition: EXISTS vs all)] ← O-0005 from S-0003 — below the bar
- K-0002 group [other(missing column: a.date)] ← O-0006 from S-0003 — below the bar
- K-0002 group [other(no applicable rule)] ← O-0011 O-0012 from S-0004 — below the bar
- K-0002 group [other(no matching rule)] ← O-0007 O-0008 from S-0003 — below the bar
- K-0002 group [other(no store records consulted)] ← O-0004 from S-0002 — below the bar
- K-0002 group [other(wrong aggregation scope: district vs client)] ← O-0009 from S-0004 — below the bar
- K-0002 group [output-schema] ← O-0001 O-0002 O-0003 from S-0001 S-0002 — at the bar
- K-0002 nominated output-schema at new-decision → admitted D-0001
- K-0002 nominated work-shape/prompt at hook-edit → decline(escapes name a shape already covered by 'tool-budget' and 'shell-tool' — the coder's reading of 'multiple questions in one prompt' is a vertical distinction that cross-cuts several members, not a missing peer)
- K-0002 nominated work-shape/task at hook-edit → decline(escapes name a shape already covered by registered terms: 'task-planning' and 'tool-budget' are both registered, and the blind coder found them rather than escaping); the coder read the presentations as ['task-planning', 'tool-budget']
- pass 5 O-0013 [other(wrong year columns queried)]: The attempt queried A12 and A13 (2015/2016) rather than the 1995/1996 unemployment rates required by the task.
- pass 5 O-0014 [other(no rule matched)]: Task text2sql‑holdout/q125 was executed but no rule matched, resulting in a failure.
- K-0003 group [other(EXISTS vs all-transactions requirement)] ← O-0005 from S-0003 — below the bar
- K-0003 group [other(check record not triggered)] ← O-0010 from S-0004 — below the bar
- K-0003 group [other(district vs client average salary)] ← O-0009 from S-0004 — below the bar
- K-0003 group [other(missing column a.date, should use trans table date)] ← O-0006 from S-0003 — below the bar
- K-0003 group [other(no applicable rule)] ← O-0011 O-0012 from S-0004 — below the bar
- K-0003 group [other(no matching rule)] ← O-0007 O-0008 from S-0003 — below the bar
- K-0003 group [other(no rule matched)] ← O-0014 from S-0005 — below the bar
- K-0003 group [other(no store records consulted)] ← O-0004 from S-0002 — below the bar
- K-0003 group [other(wrong year columns queried)] ← O-0013 from S-0005 — below the bar
- K-0003 nominated output-schema-recall at hook-edit → admitted D-0002
- K-0003 nominated sql-logic-errors at new-decision → admitted D-0003
- K-0003 nominated no-rule-consulted at new-decision → admitted D-0004
- K-0003 nominated work-shape/presentation at hook-edit → decline(escapes name a shape already covered by registered terms: 'presentation' is a partition of 'shell-tool' and 'tool-budget', both of which the coder used, and the coder did not escape — it found registered terms, so the boundary stays open); the coder read the presentations as ['tool-budget', 'task-planning']
- pass 7 O-0015 [output-schema]: In task text2sql/q93 the first attempt produced a COUNT(*) query, but the task requires a SELECT that returns the matching customer rows, violating the output‑schema convention.
- pass 7 O-0016 [output-schema]: The initial attempt executed a schema inspection command and produced a non‑JSON reply, missing the required SQL query output for the task.
- pass 7 O-0017 [output-schema]: Task text2sql/q118 failed with error "final reply was not JSON" and no rule was consulted.
- pass 8 O-0018 [output-schema]: The task required returning only the raw SELECT statement, but the attempt included additional formatting, breaching the output‑schema rule.
- pass 8 O-0019 [other(no rule matched)]: The pass attempted a text2sql/q99 task but no rule matched, leading to failure.
- K-0004 group [other(no rule matched)] ← O-0019 from S-0008 — below the bar
- K-0004 group [output-schema] ← O-0010 O-0015 O-0016 O-0017 O-0018 from S-0004 S-0007 S-0008 — at the bar
- K-0004 nominated output-schema at new-decision → admitted D-0005
- K-0004 nominated sql-correctness at hook-edit → admitted D-0006
- K-0004 nominated rule-consultation at hook-edit → admitted D-0007
- K-0004 nominated D-0002 at counterfactual-edit → The cited anchor is not rotted, the premises are supported, and the finding does not provide evidence that the premise is false.; still-holds: D-0002 stands
- K-0004 nominated L-0001 at counterfactual-edit → moot: retired through the genesis-deadline door
- K-0004 nominated L-0002 at counterfactual-edit → still-holds: kept
- K-0004 nominated L-0009 at counterfactual-edit → still-holds: kept
- K-0004 nominated L-0010 at counterfactual-edit → moot: retired through the genesis-deadline door
- K-0004 nominated L-0006 at counterfactual-edit → moot: retired through the genesis-deadline door
- K-0004 nominated L-0007 at counterfactual-edit → moot: retired through the genesis-deadline door
- K-0004 nominated work-shape/presentation at hook-edit → decline(escapes name a shape already covered by 'shell-tool' and 'tool-budget'; the blind coder's escape is not independent evidence of a new shape); the coder read the presentations as ['shell-tool']
- pass 10 O-0020 [open]: The first attempt used dist.A11 > 10000, but the correct column for district average salary is different, so the SQL query was logically incorrect.
- pass 10 O-0021 [open]: In task text2sql/q98 the first attempt produced a query selecting only account_id, omitting the required weekly issuance statement column, violating the output-schema convention that the result must include the statement.

## Records

| record | admitted after pass | mentions | decision |
|---|---|---|---|
| D-0001 | 4 | — | A solution must produce output that conforms to the task's specified schema, not a diagnostic or intermediate artifact. |
| D-0002 | 6 | — | A solution must produce output that conforms to the task's specified schema, not a diagnostic or intermediate artifact. |
| D-0003 | 6 | — | A SQL solution must correctly translate the task's logical requirements into the query, not a superficially similar but semantically different condition. |
| D-0004 | 6 | — | A solution must consult the store's rules before execution; a failure with no applicable rule is a process failure, not a task failure. |
| D-0005 | 8 | — | A solution's final output must be a valid JSON object conforming to the task's declared response schema, not a diagnostic, intermediate artifact, or incorrectly formatted string. |
| D-0006 | 8 | — | A SQL solution must correctly translate the task's logical requirements into the query, not a superficially similar but semantically different condition. |
| D-0007 | 8 | — | A solution must consult the store's rules before execution; a failure with no applicable rule is a process failure, not a task failure. |
