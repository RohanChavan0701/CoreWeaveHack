# text2sql/120b-strict — evolution

attached on `openai/gpt-oss-120b`; 5 batches × 2 tasks from text2sql-strict, seed 0; revisit [1, 2].

## Passes

| pass | batch | first sight | economy / turns / transfer | symptoms | in context | mentions | filed | consolidation after |
|---|---|---|---|---|---|---|---|---|
| 1 | 1 | 0.00 | 0.00 / 0.00 / — | wrong=2 | none | — | 4 obs, 1 prop | K-0001: 3 groups, 0 at the bar; admitted nothing; 3 refused by the floor: 1 distinct session |
| 2 | 2 | 0.00 | 0.00 / 0.00 / — | wrong=2 | none | — | 4 obs, 1 prop | K-0002: 5 groups, 1 at the bar; admitted nothing; 1 refused by the floor: 1 distinct session |
| 3 | 3 | 0.00 | 0.00 / 0.00 / — | error:not-json=1 wrong=1 | none | — | 4 obs, 1 prop | K-0003: 9 groups, 1 at the bar; admitted D-0001; 1 admitted D-0001, 1 decline, 1 draft refused at parse: a hook-edit supersedes exactly one record; got [], 1 refused by the floor: 1 distinct session |
| 4 | 4 | 0.00 | 0.00 / 0.00 / — | wrong=2 | none | — | 4 obs, 1 prop | K-0004: 6 groups, 2 at the bar; admitted D-0002; 1 admitted D-0002, 1 decline, 1 minted work-shape/task, 6 moot: retired through the genesis-deadline door, 3 refused by the floor: 1 distinct session, 1 still-holds: kept; retired L-0001 L-0002 L-0003 L-0010 L-0006 L-0007 |
| 5 | 5 | 0.50 | 0.50 / 0.50 / — | error:not-json=1 pass=1 | D-0001 D-0002 | csv-quoted: D-0002 | 1 obs, 1 prop | K-0005: 8 groups, 0 at the bar; admitted nothing; 1 draft refused at parse: sketch: a drafting reply carries a `sketch` object, 1 moot: retired through the genesis-deadline door; retired L-0009 |
| 6 (revisit) | 1 | 1.00 | 1.00 / 1.00 / — | pass=2 | D-0001 D-0002 | csv-quoted: D-0002 | 0 obs, 0 prop |  |
| 7 (revisit) | 2 | 0.00 | 0.00 / 0.00 / — | wrong=2 | D-0001 D-0002 | csv-quoted: D-0002 | 1 obs, 1 prop |  |

## Lessons

Each cell is the lesson's rows in that pass: ✓ passed, N the naive first-contact outcome (a same-shape failure), W another wrong answer, E a harness or tool error. `mentioned` marks passes with a record in context whose text uses the lesson's words.

| lesson | tier | p1 | p2 | p3 | p4 | p5 | p6r | p7r | first sight | economy / turns / transfer | naive before / after first mention | first mention | revisit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| text2sql-strict | — | WW | WW | EW | WW | ✓E | ✓✓ | WW | 0.10 (1/10) | 0.10 / 0.10 / — | 0.00 (0/10) / — | — | batch 1: 2/2, batch 2: 0/2 |

## What the passes noticed

Each observation as the close filed it, with the shape the blind coder gave it at the next consolidation (`open` until one has run); a group reaches the bar when its observations come from as many distinct sessions as the bar asks.

- pass 1 O-0001 [tool-budget]: In task text2sql‑strict/q99 the pass made two shell calls, violating the one‑call budget; the correct behavior would have been a single call that returned the query.
- pass 1 O-0002 [schema-coded-value]: The attempt queried with birth_date = '1976/1/29', which does not match the database's ISO date format and thus would have succeeded with '1976-01-29'.
- pass 1 O-0003 [other(no actions applied)]: Task text2sql‑strict/q99 failed with no applied actions.
- pass 1 O-0004 [other(no actions applied)]: Task text2sql‑strict/q112 failed with no applied actions.
- K-0001 group [other(no actions applied)] ← O-0003 O-0004 from S-0001 — below the bar
- K-0001 group [schema-coded-value] ← O-0002 from S-0001 — below the bar
- K-0001 group [tool-budget] ← O-0001 from S-0001 — below the bar
- K-0001 nominated tool-budget at hook-edit → refused by the floor: 1 distinct session(s) in the evidence (S-0001) against the bar 2; the adjudicator's decline(insufficient independence) was overridden: a decline stands only on an upheld premise kill
- K-0001 nominated schema-coded-value at new-decision → refused by the floor: 1 distinct session(s) in the evidence (S-0001) against the bar 2; the adjudicator's decline(independence floor not met: N=1 against the bar 2) was overridden: a decline stands only on an upheld premise kill
- K-0001 nominated no-actions-applied at new-decision → refused by the floor: 1 distinct session(s) in the evidence (S-0001) against the bar 2; the adjudicator's decline(independence floor not met: 1 distinct session against the bar 2) was overridden: a decline stands only on an upheld premise kill
- pass 2 O-0005 [output-schema]: In task text2sql-strict/q93, the first attempt generated a COUNT(*) query, but the convention requires a SELECT statement that returns rows, not an aggregate.
- pass 2 O-0006 [tool-budget]: In task text2sql-strict/q119 the first attempt made two shell calls, exceeding the allowed budget of 1, so it failed the budget rule.
- pass 2 O-0007 [other(no applicable rule)]: Task text2sql‑strict/q93 failed with no applicable rule.
- pass 2 O-0008 [other(no applicable rule)]: Task text2sql‑strict/q119 failed with no applicable rule.
- K-0002 group [other(aggregate instead of row-returning SELECT)] ← O-0005 from S-0002 — below the bar
- K-0002 group [other(no applicable rule)] ← O-0007 O-0008 from S-0002 — below the bar
- K-0002 group [other(no applied actions)] ← O-0003 O-0004 from S-0001 — below the bar
- K-0002 group [schema-coded-value] ← O-0002 from S-0001 — below the bar
- K-0002 group [tool-budget] ← O-0001 O-0006 from S-0001 S-0002 — at the bar
- K-0002 nominated tool-budget at new-decision → refused by the floor: 1 distinct session(s) in the evidence (S-0002) against the bar 2; the adjudicator's decline(insufficient independence) was overridden: a decline stands only on an upheld premise kill
- pass 3 O-0009 [output-schema]: In task text2sql-strict/q92, the initial attempt ran a schema inspection command rather than providing the required SELECT query, violating the convention that the answer must be the SQL statement itself.
- pass 3 O-0010 [other(missing trailing semicolon)]: In task text2sql-strict/q98 the attempt produced a SQL query without a trailing semicolon, violating the convention that queries must end with a semicolon.
- pass 3 O-0011 [other(non-JSON reply)]: Task text2sql‑strict/q92 failed with error: final reply was not JSON.
- pass 3 O-0012 [other(no rule covered the work)]: Task text2sql‑strict/q98 ran but the pass still failed because no rule covered this work.
- K-0003 group [other(aggregate instead of row-returning SELECT)] ← O-0005 from S-0002 — below the bar
- K-0003 group [other(final reply not JSON)] ← O-0011 from S-0003 — below the bar
- K-0003 group [other(missing trailing semicolon)] ← O-0010 from S-0003 — below the bar
- K-0003 group [other(no actions applied)] ← O-0003 O-0004 from S-0001 — below the bar
- K-0003 group [other(no applicable rule)] ← O-0007 O-0008 from S-0002 — below the bar
- K-0003 group [other(no rule covered the work)] ← O-0012 from S-0003 — below the bar
- K-0003 group [other(schema inspection instead of SQL query)] ← O-0009 from S-0003 — below the bar
- K-0003 group [schema-coded-value] ← O-0002 from S-0001 — below the bar
- K-0003 group [tool-budget] ← O-0001 O-0006 from S-0001 S-0002 — at the bar
- K-0003 nominated output-schema at hook-edit → refused by the floor: 1 distinct session(s) in the evidence (S-0003) against the bar 2; the adjudicator's decline(insufficient independence) was overridden: a decline stands only on an upheld premise kill
- K-0003 nominated tool-budget at new-decision → admitted D-0001
- K-0003 nominated schema-coded-value at hook-edit → draft refused at parse: a hook-edit supersedes exactly one record; got []
- K-0003 nominated work-shape/presentation at hook-edit → decline(escapes name a shape already covered by registered terms: the blind coder's escape 'other(multiple questions in one prompt)' matches the existing term 'task-planning', and the escape 'other(presentation)' is too vague to distinguish from 'output-schema' or 'schema-coded-value')
- pass 4 O-0013 [output-schema, tool-budget]: In task text2sql-strict/q89, the first attempt made two shell calls, exceeding the budget of 1, and returned a COUNT query rather than the required SELECT statement, violating the single‑call and query‑format conventions.
- pass 4 O-0014 [tool-budget]: In task text2sql-strict/q136 the attempt made two shell calls, violating the budget of 1; the second call was refused, so the query was not checked against the reference.
- pass 4 O-0015 [tool-budget]: Task text2sql‑strict/q89 failed with a budget‑exceeded shell call error.
- pass 4 O-0016 [tool-budget]: Task text2sql‑strict/q136 failed with a budget‑exceeded shell call error.
- K-0004 group [other(no convention identified)] ← O-0003 O-0004 O-0007 O-0008 O-0011 O-0012 from S-0001 S-0002 S-0003 — at the bar
- K-0004 group [other(query must end with semicolon)] ← O-0010 from S-0003 — below the bar
- K-0004 group [output-schema] ← O-0005 O-0009 from S-0002 S-0003 — at the bar
- K-0004 group [output-schema, tool-budget] ← O-0013 from S-0004 — below the bar
- K-0004 group [schema-coded-value] ← O-0002 from S-0001 — below the bar
- K-0004 group [tool-budget] ← O-0014 O-0015 O-0016 from S-0004 — below the bar
- K-0004 nominated output-schema at new-decision → admitted D-0002
- K-0004 nominated schema-coded-value at new-decision → refused by the floor: 1 distinct session(s) in the evidence (S-0001) against the bar 2; the adjudicator's decline(warrant:independence landed: the anchored observations come from 1 distinct session (S-0001) against the bar of 2; the floor refuses this draft whatever the verdict) was overridden: a decline stands only on an upheld premise kill
- K-0004 nominated semicolon-termination at new-decision → refused by the floor: 1 distinct session(s) in the evidence (S-0003) against the bar 2; the adjudicator's decline(warrant:independence landed: the draft's evidence (O-0010) comes from a single session (S-0003), below the bar of 2 distinct sessions, so the floor refuses it.) was overridden: a decline stands only on an upheld premise kill
- K-0004 nominated tool-budget-recall at hook-edit → refused by the floor: 1 distinct session(s) in the evidence (S-0004) against the bar 2; the adjudicator's decline(warrant:independence landed: the evidence shows 1 distinct session (S-0004) against the bar of 2, so the floor refuses the draft) was overridden: a decline stands only on an upheld premise kill
- K-0004 nominated L-0001 at counterfactual-edit → moot: retired through the genesis-deadline door
- K-0004 nominated L-0002 at counterfactual-edit → moot: retired through the genesis-deadline door
- K-0004 nominated L-0003 at counterfactual-edit → moot: retired through the genesis-deadline door
- K-0004 nominated L-0009 at counterfactual-edit → still-holds: kept
- K-0004 nominated L-0010 at counterfactual-edit → moot: retired through the genesis-deadline door
- K-0004 nominated L-0006 at counterfactual-edit → moot: retired through the genesis-deadline door
- K-0004 nominated L-0007 at counterfactual-edit → moot: retired through the genesis-deadline door
- K-0004 nominated work-shape/prompt at hook-edit → decline(escapes name a shape already covered by registered terms: 'prompt' is a partition of 'task-planning' and 'tool-call-retry', not a missing peer; the blind coder found a registered term, keeping the boundary open)
- K-0004 nominated work-shape/task at hook-edit → minted work-shape/task
- pass 5 O-0017 [other(non-JSON reply and missing SELECT statement)]: The first attempt tried to inspect the database schema via a shell call and produced a non‑JSON reply, missing the required SELECT statement for the task.
- K-0005 group [other(missing trailing semicolon)] ← O-0010 from S-0003 — below the bar
- K-0005 group [other(no actions applied)] ← O-0003 O-0004 from S-0001 — below the bar
- K-0005 group [other(no applicable rule)] ← O-0007 O-0008 from S-0002 — below the bar
- K-0005 group [other(no rule covered the work)] ← O-0012 from S-0003 — below the bar
- K-0005 group [other(non-JSON reply and missing SELECT statement)] ← O-0017 from S-0005 — below the bar
- K-0005 group [other(non-JSON reply)] ← O-0011 from S-0003 — below the bar
- K-0005 group [schema-coded-value] ← O-0002 from S-0001 — below the bar
- K-0005 group [tool-budget] ← O-0014 O-0015 O-0016 from S-0004 — below the bar
- K-0005 nominated none at new-decision → draft refused at parse: sketch: a drafting reply carries a `sketch` object
- K-0005 nominated L-0009 at counterfactual-edit → moot: retired through the genesis-deadline door
- pass 7 O-0018 [open]: In task text2sql‑strict/q119 the attempt generated a SELECT with unnecessary joins, breaching the rule that the final answer must be a plain SELECT returning rows.

## Records

| record | admitted after pass | mentions | decision |
|---|---|---|---|
| D-0001 | 3 | — | Every pass must respect the tool-call budget. If a pass makes more tool calls than the budget allows, the system must abort the pass and report the budget violation. |
| D-0002 | 4 | csv-quoted | When generating SQL, the final answer must be a SELECT statement that returns rows, not an aggregate function, a schema inspection command, or any other non-SELECT output. |
