# text2sql/20b-attached — evolution

attached on `openai/gpt-oss-20b`; 8 batches × 2 tasks from text2sql+text2sql-holdout, seed 0; revisit [1, 2].

## Passes

| pass | batch | first sight | economy / turns / transfer | symptoms | in context | mentions | filed | consolidation after |
|---|---|---|---|---|---|---|---|---|
| 1 | 1 | 1.00 | 0.50 / 0.67 / — | pass=2 | none | — | 0 obs, 0 prop |  |
| 2 | 2 | 0.00 | 0.00 / 0.00 / — | wrong=2 | none | — | 4 obs, 0 prop | K-0001: 3 groups, 0 at the bar; admitted nothing; 3 refused by the floor: 1 distinct session |
| 3 | 3 | 0.00 | 0.00 / 0.00 / — | wrong=2 | none | — | 4 obs, 1 prop |  |
| 4 | 4 | 0.50 | 0.50 / 0.50 / — | pass=1 wrong=1 | none | — | 2 obs, 0 prop | K-0002: 6 groups, 0 at the bar; admitted D-0001; 1 admitted D-0001, 1 decline; dismissed 3 |
| 5 | 5 | 0.50 | 0.50 / 0.50 / — | pass=1 wrong=1 | D-0001 | — | 2 obs, 1 prop |  |
| 6 | 6 | 1.00 | 1.00 / 1.00 / — | pass=2 | D-0001 | — | 0 obs, 1 prop | K-0003: 2 groups, 1 at the bar; admitted D-0002; 1 admitted D-0002 |
| 7 | 7 | 0.00 | 0.00 / 0.00 / — | wrong=2 | D-0001 D-0002 | — | 2 obs, 1 prop |  |
| 8 | 8 | 0.00 | 0.00 / 0.00 / — | wrong=2 | D-0001 D-0002 | — | 4 obs, 1 prop | K-0004: 5 groups, 1 at the bar; admitted D-0003; 1 admitted D-0003, 2 decline, 5 moot: retired through the genesis-deadline door, 1 moot: retired through the variance-collapse door; the cacheable answer is [{"target": "payload:abstraction", "landed": false}], 1 still-holds: kept; retired L-0001 L-0002 L-0003 L-0010 L-0006 L-0007 |
| 9 (revisit) | 1 | 1.00 | 1.00 / 1.00 / — | pass=2 | D-0003 | — | 0 obs, 1 prop |  |
| 10 (revisit) | 2 | 0.00 | 0.00 / 0.00 / — | wrong=2 | D-0003 | — | 2 obs, 0 prop |  |

## Lessons

Each cell is the lesson's rows in that pass: ✓ passed, N the naive first-contact outcome (a same-shape failure), W another wrong answer, E a harness or tool error. `mentioned` marks passes with a record in context whose text uses the lesson's words.

| lesson | tier | p1 | p2 | p3 | p4 | p5 | p6 | p7 | p8 | p9r | p10r | first sight | economy / turns / transfer | naive before / after first mention | first mention | revisit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| text2sql | — | ✓ | W | W | W | ✓ | ✓ | WW | WW | ✓ | W | 0.30 (3/10) | 0.31 / 0.33 / — | 0.00 (0/10) / — | — | batch 1: 1/1, batch 2: 0/1 |
| text2sql-holdout | — | ✓ | W | W | ✓ | W | ✓ |  |  | ✓ | W | 0.50 (3/6) | 0.42 / 0.44 / — | 0.00 (0/6) / — | — | batch 1: 1/1, batch 2: 0/1 |

## What the passes noticed

Each observation as the close filed it, with the shape the blind coder gave it at the next consolidation (`open` until one has run); a group reaches the bar when its observations come from as many distinct sessions as the bar asks.

- pass 2 O-0001 [other(used .schema instead of SELECT)]: The first attempt in this pass was wrong: it used the .schema command instead of the SELECT query.
- pass 2 O-0002 [other(omitted required weekly issuance statement)]: Task text2sql/q98: the first attempt returned a SELECT statement that omitted the required weekly issuance statement, missing the convention of including the statement in the output.
- pass 2 O-0003 [other(no rule for task shape)]: Task text2sql-holdout/q168 had no rule.
- pass 2 O-0004 [other(no rule for task shape)]: Task text2sql/q98 had no rule.
- K-0001 group [other(missing weekly issuance statement in output)] ← O-0002 from S-0002 — below the bar
- K-0001 group [other(no rule)] ← O-0003 O-0004 from S-0002 — below the bar
- K-0001 group [output-schema] ← O-0001 from S-0002 — below the bar
- K-0001 nominated output-schema at new-decision → refused by the floor: 1 distinct session(s) in the evidence (S-0002) against the bar 2; the adjudicator's decline(insufficient independence) was overridden: a decline stands only on an upheld premise kill
- K-0001 nominated no-rule at new-decision → refused by the floor: 1 distinct session(s) in the evidence (S-0002) against the bar 2; the adjudicator's decline(independence floor not met) was overridden: a decline stands only on an upheld premise kill
- K-0001 nominated weekly-issuance at new-decision → refused by the floor: 1 distinct session(s) in the evidence (S-0002) against the bar 2; the adjudicator's decline(warrant:independence landed: the draft is below the independence floor (N=1 against the bar 2), and the floor refuses it whatever the verdict) was overridden: a decline stands only on an upheld premise kill
- pass 3 O-0005 [other(filtered on account date instead of transaction date)]: Task text2sql/q119: The first attempt incorrectly filtered on account date instead of transaction date, causing the query to miss accounts with statements issued after transactions in 1993.
- pass 3 O-0006 [other(omitted condition for status 'D')]: In task text2sql-holdout/q192, the first attempt produced a SELECT query that omitted the condition for status 'D', causing the hidden check to fail.
- pass 3 O-0007 [other(failed task)]: Failed task text2sql/q119
- pass 3 O-0008 [other(failed task)]: Failed task text2sql-holdout/q192
- pass 4 O-0009 [other(counted loans instead of distinct accounts)]: In task text2sql/q136, the first attempt incorrectly counted loans instead of distinct accounts, missing the requirement to count per account.
- pass 4 O-0010 [other(failed task)]: text2sql/q136 failed
- K-0002 group [other(counted loans instead of distinct accounts)] ← O-0009 from S-0004 — below the bar
- K-0002 group [other(filtered on account date instead of transaction date)] ← O-0005 from S-0003 — below the bar
- K-0002 group [other(no rule)] ← O-0003 O-0004 from S-0002 — below the bar
- K-0002 group [other(omitted condition for status 'D')] ← O-0006 from S-0003 — below the bar
- K-0002 group [other(omitted required weekly issuance statement)] ← O-0002 from S-0002 — below the bar
- K-0002 group [other(used .schema instead of SELECT)] ← O-0001 from S-0002 — below the bar
- K-0002 nominated SQL-query-accuracy at new-decision → admitted D-0001
- K-0002 nominated work-shape/presentation at hook-edit → decline(escapes name a shape already covered by registered terms: 'Presentation' is a concrete instance of 'output-schema' or 'field-quoted', not a distinct shape; the coder found a registered term, keeping the boundary open)
- pass 5 O-0011 [schema-coded-value]: In task text2sql-holdout/q125, the first attempt produced a SQL query with an ambiguous column name 'client_id', causing a shell error; the correct query should qualify the column with its table alias.
- pass 5 O-0012 [other(no rule for task shape)]: The store has no rule for the text2sql-holdout shape.
- K-0003 group [other(ambiguous column name in SQL query)] ← O-0011 from S-0005 — below the bar
- K-0003 group [other(no rule for task shape)] ← O-0003 O-0004 O-0012 from S-0002 S-0005 — at the bar
- K-0003 nominated text2sql-generation at new-decision → admitted D-0002
- pass 7 O-0013 [output-schema]: In task text2sql/q118, the first attempt incorrectly used the loan table instead of the accounts table, violating the requirement to match the requested aggregation target and filtering conditions.
- pass 7 O-0014 [output-schema]: Task text2sql/q93: first attempt used hint column names A2, A3, A11 instead of actual column names, causing the query to be rejected by the hidden check.
- pass 8 O-0015 [output-schema]: Task text2sql/q99: the first attempt returned an extra column (date) not requested, so it did not match the aggregation target.
- pass 8 O-0016 [tool-budget]: Task text2sql/q89: first attempt used 4 shell calls exceeding the budget, violating the shell‑tool call limit; the correct approach would have used only 3 calls and fully qualified column references as per D‑0002.
- pass 8 O-0017 [other(aggregation target mismatch)]: text2sql/q99 failed
- pass 8 O-0018 [other(shell call budget exceeded)]: text2sql/q89 failed
- K-0004 group [other(aggregation target mismatch)] ← O-0017 from S-0008 — below the bar
- K-0004 group [other(shell call budget exceeded)] ← O-0018 from S-0008 — below the bar
- K-0004 group [output-schema] ← O-0013 O-0014 O-0015 from S-0007 S-0008 — at the bar
- K-0004 group [schema-coded-value] ← O-0011 from S-0005 — below the bar
- K-0004 group [tool-budget] ← O-0016 from S-0008 — below the bar
- K-0004 nominated SQL-Constraint-Precision at new-decision → admitted D-0003
- K-0004 nominated L-0001 at counterfactual-edit → moot: retired through the genesis-deadline door
- K-0004 nominated L-0002 at counterfactual-edit → moot: retired through the genesis-deadline door
- K-0004 nominated L-0003 at counterfactual-edit → moot: retired through the genesis-deadline door
- K-0004 nominated L-0009 at counterfactual-edit → still-holds: kept
- K-0004 nominated L-0010 at counterfactual-edit → moot: retired through the genesis-deadline door
- K-0004 nominated L-0006 at counterfactual-edit → moot: retired through the genesis-deadline door
- K-0004 nominated L-0007 at counterfactual-edit → moot: retired through the variance-collapse door; the cacheable answer is [{"target": "payload:abstraction", "landed": false}]
- K-0004 nominated work-shape/prompt at hook-edit → decline(escapes map to existing terms: 'prompt' is covered by 'task-planning' and 'tool-budget' as a work-shape, and the coder found a registered term); the coder read the presentations as ['task-planning']
- K-0004 nominated work-shape/task at hook-edit → decline(escapes name a shape already covered by registered terms: 'shell-tool' and 'tool-budget' are both registered, and the coder found them too — no gap to fill); the coder read the presentations as ['shell-tool', 'tool-budget']
- pass 10 O-0019 [open]: Task text2sql/q98: The first attempt filtered on a.frequency instead of l.frequency for weekly issuance, missing the correct filtering convention.
- pass 10 O-0020 [open]: Task text2sql-holdout/q168: the first attempt used only a schema inspection call and did not generate the SELECT statement required by the prompt, violating the rule that the query must be produced by a shell call that returns the SQL text.

## Records

| record | admitted after pass | mentions | decision |
|---|---|---|---|
| D-0001 | 4 | — | When generating SQL, the query must precisely match the requested aggregation target and filtering conditions as stated in the natural language prompt, without substituting similar but incorrect entities or omitting required clauses. |
| D-0002 | 6 | — | When generating SQL from a natural language prompt, the query must precisely match the requested aggregation target and filtering conditions, and all column references must be fully qualified with their table alias to prevent ambiguity. |
| D-0003 | 8 | — | When generating SQL from a natural language prompt, the query must precisely match the requested aggregation target and filtering conditions, and all column references must be fully qualified with their table alias to prevent ambiguity. |
