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
passes and consolidations settles on seven decisions.

| id | decision, in one line | what it looks like in the trace without it | floor it saves |
|---|---|---|---|
| D-0001 | The schema card: eight tables, every column and type, the join keys, the coded columns, the A-column meanings, the region spellings. Applied at boot so no call is spent on `.schema`. | visible: a `.schema` call first, then the query; on strict, a budget overrun (`tool_budget_respected`) or no query at all | the one strict call |
| D-0002 | Dates are TEXT `'YYYY-MM-DD'`: year is `STRFTIME('%Y', col) = '1997'`, ranges and exact days are ISO string literals; never `YEAR()`. | loud: `no such function: YEAR`, the task fails on the raise | a repair call |
| D-0003 | A percentage or ratio casts before dividing: `CAST(SUM(...) AS REAL) * 100 / COUNT(...)`; boolean-sum for conditional counts; no ROUND. | invisible: the query runs and returns `29` where the gold returns `29.77`; only the row comparison says failed | nothing to repair, because nothing looks wrong |
| D-0004 | Coded literals, exact and case-sensitive: `status` A/B/C/D and their meanings, `frequency` three Czech phrases, `gender` F/M, `disp.type`, `card.type`, `A3` region spellings with a lowercase compass word. | invisible: `status = 'running'` or `A3 = 'North Bohemia'` runs and returns zero rows or the wrong count | a `SELECT DISTINCT` call |
| D-0005 | The table `order` is a reserved word: quote it and alias it; nothing else in the schema needs quoting. | loud: `near "order": syntax error` | a repair call |
| D-0006 | The one-call method: compose the full SELECT from the card, run it exactly once, return the statement; superlatives are `ORDER BY ... LIMIT 1`; only the asked columns; COUNT vs COUNT(DISTINCT); GROUP BY for per-entity lists. | visible: two or three exploratory calls before a query; or loud: rows returned in place of a statement, failed before comparison | the whole slack budget, and the strict call |
| D-0007 | The `trans` codes: `type` PRIJEM/VYDAJ/VYBER and `operation` VYBER KARTOU/VYBER/VKLAD/PREVOD Z UCTU/PREVOD NA UCET are Czech literals, case-sensitive; `'VYBER'` is both a type and an operation, so a cash withdrawal is `operation = 'VYBER'` and a non-credit-card debit is `type = 'VYDAJ'`. | invisible: `operation = 'cash withdrawal'`, or a cash withdrawal read off `type = 'VYBER'`, runs and returns zero or the wrong rows | a `SELECT DISTINCT` call |

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
- `trans(trans_id, account_id, date, type, operation, amount INTEGER, balance INTEGER,
  k_symbol, bank, account)` kept whole (1,056,320 rows); `type` in `'PRIJEM'`, `'VYDAJ'`,
  `'VYBER'`; `operation` in `'VKLAD'`, `'VYBER'`, `'VYBER KARTOU'`, `'PREVOD Z UCTU'`,
  `'PREVOD NA UCET'`, NULL; `balance` is the account balance after the transaction.
  Questions read it for credit-card withdrawals (`operation = 'VYBER KARTOU'`), cash
  withdrawals (`operation = 'VYBER'`), non-credit-card debits (`type = 'VYDAJ'`) and
  balance growth across two dates.
- Every date column is TEXT `'YYYY-MM-DD'`; `SUM(status='A')*100/COUNT(*)` returns
  `29` against `29.77` with the cast; `YEAR(date)` raises; bare `FROM order` raises.

## What the pinned questions turn on

Read from the gold SQL in `suite/data/text2sql.jsonl`, the conventions the 32
questions exercise (the questions themselves are never in the seed):

- Dates: STRFTIME year filters on `loan.date` and `account.date` (q98, q99, q119, q120,
  q152, q169) and on `client.birth_date` (q100); an ISO `BETWEEN` range (q136); a
  `LIKE '1996-01%'` month filter (q129); exact ISO days rewritten from `1976/1/29`,
  `1993/7/5`, `1998/12/27`, `1993/3/22` (q112, q116); `STRFTIME('%Y', CURRENT_TIMESTAMP)
  - STRFTIME('%Y', birth_date)` for age (q194).
- `CAST(... AS REAL)` percentages with a boolean-sum numerator (q117, q118, q168, q115,
  q186); a rate increment `CAST((A13 - A12) AS REAL) * 100 / A12` (q125); the growth-rate
  idiom `CAST((SUM(cond_A) - SUM(cond_B)) AS REAL) * 100 / SUM(cond_B)` over two periods,
  its conditional sums written with `IIF` or `CASE WHEN` (q116, q169); a direct `AVG`
  where the gold takes one (q192, q152, q145).
- Coded literals: `status` `'A'`, `'C'`, `IN ('C','D')`, `'D'` (q117, q118, q137, q192,
  q125); all three `frequency` phrases (q98, q89, q136, q119, q186, q192); `gender`
  `'F'`/`'M'` (q92, q93, q100, q112, q115, q128, q168, q186, q189); `disp.type` `'OWNER'`
  and `!= 'OWNER'` (q149, q194, q169); `card.type = 'gold'` (q194); `A3` region spellings
  with the lowercase compass word — `'north Bohemia'`, `'east Bohemia'`, `'south Bohemia'`
  (q93, q89, q115, q120); `district_id = 1` for "Branch location 1" (q137).
- `trans` codes: `operation = 'VYBER KARTOU'` for a credit-card withdrawal (q145),
  `operation = 'VYBER'` for a cash withdrawal (q159), `type = 'VYDAJ'` for a
  non-credit-card debit (q129); `trans.balance` at two exact dates for a growth rate
  (q116). `'VYBER'` is both a `type` and an `operation` value.
- Shapes: superlatives as `ORDER BY ... LIMIT 1` (q98, q99, q189, q94); a second-highest
  as `ORDER BY ... DESC LIMIT 1, 1` (q138); a top-nine as `GROUP BY ... ORDER BY COUNT
  DESC LIMIT 9` (q128) and a top-ten as `SELECT DISTINCT ... ORDER BY ... LIMIT 10`
  (q129); a derived table joined back to its parent (q173, `` `order` `` grouped and
  summed by `k_symbol`); a scalar subquery for a `MAX(A11) - MIN(A11)` gap and for a
  correlated superlative (q94, q95); `COUNT(DISTINCT district_id)` where districts are
  counted across clients (q92) against plain `COUNT` elsewhere; the three-column
  projection in the asked order (q119); the client-to-account walk through `disp`
  (q189, q159, q169, q194).

One graded question, q173, reads the reserved-word `` `order` `` table (a derived table
over `` `order` `` grouped by `k_symbol`), so D-0005's reserved-word convention fires;
its use ratio stays low, which the decision's own residue notes.

## Latches, exclusions, stakes

Every decision carries a consultation latch keyed on registered work-shape terms
only, so no `vocabulary.json` is needed:

- D-0001 and D-0006 key on `shell-tool`, `file-tool`, `tool-budget` — the exact
  presentation of every task in the three families.
- D-0002 through D-0005 and D-0007 key on `shell-tool`, `tool-budget`.

All seven share the same three exclusions, worded so the boot's guard does not exclude
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
`suite/families/text2sql.py` by line: 19 and 22–29 (the docstring's statement of each
convention), 152 (`trans` kept whole), 98 (the knowing floor), 169–172 (the prompt),
197 (two-decimal rounding), 202 (multiset comparison), 209 and 214 (the check's two
failure modes), 333 (the task's blob and budget). `warrant.anchors` lists the same.

## The compare/contrast expectation

`experiments/text2sql.toml` has not run; there are no run stores. The seed is the
target the loop is meant to reach, and injecting it against an empty store isolates
what the seven decisions buy:

- **`120b-strict-seeded`, the seeded strict arm.** Near 1.0 first-sight pass rate and
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
  with the loop expected to converge on roughly this seven-decision store after the
  consolidations. The revisit at 1 and 2 after the stream measures whether what the
  loop admitted retained the same conventions the seed carries.
- **Scorers.** `task_pass_rate` separates the seeded and unseeded arms on strict;
  `tool_budget_respected` and `solution_economy` show the discovery call the seed
  saves; `method_transfer` should read the same on graded and holdout batches for the
  seeded arm.

## Validation

Injecting the seed into a fresh store — `hgi genesis` then `hgi seed text2sql --model
gpt-oss-120b` — mints the seven decisions past the store's ids, prices them for the arm's
pass model, and runs the write-seam floor, which they pass. `hgi lint --model
gpt-oss-120b` over the resulting store is green: no failures, and `model-pricing` is
quiet on the seed, its decisions priced for the session's model. `hgi consult --terms
shell-tool,file-tool,tool-budget --problem "<a strict prompt>"` reaches all seven via the
index with no `excluded_by`.
