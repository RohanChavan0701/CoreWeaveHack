# Seed: the text-to-SQL world

A hand-authored store for the `text2sql`, `text2sql-strict` and `text2sql-holdout`
families (`suite/families/text2sql.py`, records `suite/data/text2sql.jsonl`, database
`suite/data/text2sql.sqlite`): BIRD mini-dev's `financial` questions over one pinned
SQLite database, graded by re-executing the returned `SELECT` and comparing its rows
to the gold's as an order-insensitive multiset with floats rounded to two decimals.
The experiment is `experiments/text2sql.toml`. Every task presents as
`("shell-tool", "file-tool", "tool-budget")`; the prompt names the database as
`financial.sqlite` in the working directory, invites the pass to inspect its schema
with `sqlite3 financial.sqlite ".schema"` or a `SELECT DISTINCT`, and asks for the
query text as `result`, never a computed value. `text2sql` and the holdout budget three
shell calls with a knowing floor of one; `text2sql-strict` budgets exactly the floor.

## What a mature store holds

The lesson of this world is the database's own schema and dialect. BIRD's evidence
names the domain mapping the question needs (`status = 'A'` means finished with no
problems; `'POPLATEK TYDNE'` means weekly issuance) but never the dialect, so a
general model meets each convention cold and either errors (loud) or returns a query
that runs and is wrong (invisible until the check). A store that has seen enough
passes and consolidations settles on six decisions.

| id | decision, in one line | what it looks like in the trace without it | floor it saves |
|---|---|---|---|
| D-0001 | The schema card: eight tables, every column and type, the join keys, the coded columns, the A-column meanings, the region spellings. Applied at boot so no call is spent on `.schema`. | visible: a `.schema` call first, then the query; on strict, a budget overrun (`tool_budget_respected`) or no query at all | the one strict call |
| D-0002 | Dates are TEXT `'YYYY-MM-DD'`: year is `STRFTIME('%Y', col) = '1997'`, ranges and exact days are ISO string literals; never `YEAR()`. | loud: `no such function: YEAR`, the task fails on the raise | a repair call |
| D-0003 | A percentage or ratio casts before dividing: `CAST(SUM(...) AS REAL) * 100 / COUNT(...)`; boolean-sum for conditional counts; no ROUND. | invisible: the query runs and returns `29` where the gold returns `29.77`; only the row comparison says failed | nothing to repair, because nothing looks wrong |
| D-0004 | Coded literals, exact and case-sensitive: `status` A/B/C/D and their meanings, `frequency` three Czech phrases, `gender` F/M, `disp.type`, `card.type`, `A3` region spellings with a lowercase compass word. | invisible: `status = 'running'` or `A3 = 'North Bohemia'` runs and returns zero rows or the wrong count | a `SELECT DISTINCT` call |
| D-0005 | The table `order` is a reserved word: quote it and alias it; nothing else in the schema needs quoting. | loud: `near "order": syntax error` | a repair call |
| D-0006 | The one-call method: compose the full SELECT from the card, run it exactly once, return the statement; superlatives are `ORDER BY ... LIMIT 1`; only the asked columns; COUNT vs COUNT(DISTINCT); GROUP BY for per-entity lists. | visible: two or three exploratory calls before a query; or loud: rows returned in place of a statement, failed before comparison | the whole slack budget, and the strict call |

The card (D-0001) is the point of the seed and is long by design; the others are
crisp. The concrete facts were enumerated from the shipped database, not guessed:

- `district(district_id, A2 name, A3 region, A4..A16)`, A11 average salary INTEGER,
  A12/A13 unemployment 1995/1996 REAL; A3 holds exactly `'Prague'`, `'central Bohemia'`,
  `'east Bohemia'`, `'north Bohemia'`, `'south Bohemia'`, `'west Bohemia'`,
  `'north Moravia'`, `'south Moravia'`.
- `account(account_id, district_id, frequency, date)`; `frequency` in
  `'POPLATEK MESICNE'` (monthly), `'POPLATEK TYDNE'` (weekly), `'POPLATEK PO OBRATU'`
  (after transaction).
- `client(client_id, gender 'F'|'M', birth_date, district_id)`.
- `disp(disp_id, client_id, account_id, type 'OWNER'|'DISPONENT')` — the only
  client-to-account link.
- `loan(loan_id, account_id, date, amount INTEGER, duration in 12|24|36|48|60,
  payments REAL, status 'A'|'B'|'C'|'D')`; at most one loan per account.
- `card(card_id, disp_id, type 'classic'|'gold'|'junior', issued)`.
- `` `order`(order_id, account_id, bank_to, account_to, amount REAL, k_symbol) ``,
  `k_symbol` in `''`, `'LEASING'`, `'POJISTNE'`, `'SIPO'`, `'UVER'`.
- `trans(...)`, sampled to twenty accounts in the pinned copy; no selected question
  reads it.
- Every date column is TEXT `'YYYY-MM-DD'`; `SUM(status='A')*100/COUNT(*)` returns
  `29` against `29.77` with the cast; `YEAR(date)` raises; bare `FROM order` raises.

## What the graded questions turn on

Read from the gold SQL in `suite/data/text2sql.jsonl`, the conventions the sixteen
questions exercise (the questions themselves are never in the seed):

- STRFTIME year filters on `loan.date` and `account.date` (q98, q99, q119); an ISO
  `BETWEEN` range (q136); an exact ISO birth date rewritten from `1976/1/29` (q112).
- `CAST(... AS REAL)` percentages with a boolean-sum numerator (q117, q118, q168) and a
  rate increment `CAST((A13 - A12) AS REAL) * 100 / A12` (q125).
- Coded literals: `status` `'A'`, `'C'`, `IN ('C','D')`, `'D'` (q117, q118, q137, q192,
  q125); all three `frequency` phrases (q98, q89, q136, q119, q192); `gender` `'F'`/`'M'`
  (q92, q93, q112, q168, q128, q189); `A3 = 'north Bohemia'` / `'east Bohemia'` with the
  lowercase compass word (q93, q89); `district_id = 1` for "Branch location 1" (q137).
- Shapes: superlatives as `ORDER BY ... LIMIT 1` (q98, q99, q189), a top-nine as
  `GROUP BY ... ORDER BY COUNT DESC LIMIT 9` (q128), `COUNT(DISTINCT district_id)`
  where districts are counted across clients (q92) against plain `COUNT` elsewhere,
  the three-column projection in the asked order (q119), the client-to-account walk
  through `disp` (q189).

No graded or held-out question reads `` `order` ``; D-0005 is cheap insurance whose
use ratio may stay low, which its own residue notes.

## Latches, exclusions, stakes

Every decision carries a consultation latch keyed on registered work-shape terms
only, so no `vocabulary.json` is needed:

- D-0001 and D-0006 key on `shell-tool`, `file-tool`, `tool-budget` — the exact
  presentation of every task in the three families.
- D-0002 through D-0005 key on `shell-tool`, `tool-budget`.

All six share the same three exclusions, worded so the boot's guard does not exclude
a `financial.sqlite` task and so none of the phrases occurs in the task prompt (the
consult reading would otherwise flag `excluded_by`):

- a question over a database other than `financial.sqlite`, whose schema this card
  does not describe;
- a task that creates, alters or writes to the database (DDL or DML) rather than
  reading it with a SELECT;
- a shell task with no SQLite database in the working directory.

Each decision also carries a `revisit` latch on the oracle (`suite-v1`,
`task_pass_rate < 0.5` persisting two passes, re-adjudicate) and the standard
retirement latch (applied-over-considered below 0.1 over six passes at consolidation).
Counterfactuals name both overshoots — the convention missed, and the convention
over-applied (a `.schema` call the card already answers; `DATE()` around an ISO
literal; `ROUND` that breaks the two-decimal comparison; quoting every identifier;
re-running a query that already executed) — and anchor into
`suite/families/text2sql.py` by line: 19 and 22–27 (the docstring's statement of each
convention), 47 (`trans` sampled), 96 (the knowing floor), 112–116 (the prompt),
141 (two-decimal rounding), 146 (multiset comparison), 153 and 158 (the check's two
failure modes), 264 (the task's blob and budget). `warrant.anchors` lists the same.

## The compare/contrast expectation

`experiments/text2sql.toml` has not run; there are no run stores. The seed is the
target the loop is meant to reach, and injecting it against an empty store isolates
what the six decisions buy:

- **`120b-strict`, seeded attached arm.** Near 1.0 first-sight pass rate and
  `tool_budget_respected` at 1.0: the pass applies the card at boot, writes the query,
  spends its one call running it, returns the statement. The only expected misses are
  judgment residue the floor does not check — which date column a phrase means, whether
  the numerator and denominator share a filter.
- **`120b-strict-detached` / unseeded.** On the ~0.5 band the header hypothesises
  (carry-forward item 89): the pass takes the prompt's invitation, spends the one call
  on `.schema`, and either overruns the budget or guesses the query; the dialect
  conventions are met cold, so YEAR() and uncast division each take their share.
- **`120b-attached` (slack, `text2sql` + `text2sql-holdout`).** The seeded arm should
  hold the knowing floor of one call on both groups, holdout included, since every
  decision is schema-scoped rather than question-scoped; the unseeded arm spends its
  first call on discovery on every batch and re-learns each convention as it meets it,
  with the loop expected to converge on roughly this six-decision store after the
  consolidations. The revisit at 1 and 2 after the stream measures whether what the
  loop admitted retained the same conventions the seed carries.
- **Scorers.** `task_pass_rate` separates the seeded and unseeded arms on strict;
  `tool_budget_respected` and `solution_economy` show the discovery call the seed
  saves; `method_transfer` should read the same on graded and holdout batches for the
  seeded arm.

## Validation

A scratch store was seeded with `hgi genesis`, the six decisions copied into
`decisions/`, `registry/ids.json` `D` set to 6, then `hgi index` and `hgi lint`:

    lint: green — 0 failures, 0 warnings

`hgi consult --terms shell-tool,file-tool,tool-budget --problem "<a strict prompt>"`
reaches all six via the index with no `excluded_by`.
