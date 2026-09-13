# Seed: the conventions world

The hand-written conventions of this world and their generated clothes — the
families `genesis`, `conventions`, `transfer`, `curriculum` and
`curriculum-strict` (`suite/families/genesis.py`, `conventions.py`,
`transfer.py`, `curriculum.py`), the seven lessons of `suite/lessons.py`, and
the experiments that run on them: `baseline`, `probe`, `cadence`,
`model-sweep`, `transfer`, `stream`, `stream-probe`, `economy`.

A mature store for this world holds one decision per lesson — the world-fact
the lesson turns on, stated so that a pass reading only the decision and its
summary at boot applies it to a clothing it has never seen — plus the two
decisions the `genesis` family exists to teach and the seed constitution
(`C-0001..C-0007`, which are about the loop, not the world) does not carry:
the transient retry with the cause reported, and the call plan under a
budget. Nine decisions, `decisions/D-0001.json .. D-0009.json`, each in the
shape of `store/decisions/D-0001.json` (`hgi.types.Decision`), status
`accepted`, `admission.proposed_by` `"seed"`, `priced_for.model_id` `null`
(the injector prices them for the arm's pass model and renumbers them past
the store's own).

## The lessons, and what the store must carry for each

Every task in these families presents a shape tuple (`Task.shapes`) drawn
from the registered work-shape terms — `shell-tool`, `file-tool`,
`http-tool`, `tool-budget`, `error-wrapping`, `output-schema` are the six
these families use — and the boot matches a decision's consultation latch
against the terms the classify step names. A batch of eight curriculum tasks
is one session, so the session's work-shape names most of the six and most
of the nine decisions are considered on every pass; the `not_this`
exclusions are what the guard reads to keep a record off the rows it does
not bear on (the strict `stream` arm's D-0001, "all HTTP calls use `/v2`",
had no such bound and cost the paged-api rows 404s), and the decision text
names the row shape it applies to. Every task also declares the knowing
policy's calls (`Task.knowing`) — the floor `solution_economy` and
`turn_economy` grade against; `curriculum` budgets at the knowing count plus
one and `curriculum-strict` at the knowing count exactly.

| id | lesson | tier | the decision, in one line | keys on | excludes | knowing floor (budget: curriculum / strict / hand-written) |
|---|---|---|---|---|---|---|
| D-0001 | trailing-newline | invisible | count lines with `awk 'END{print NR}' <files>` in one call — never `wc -l` (one short per file), never `cat` first (it glues files) | `shell-tool`, `tool-budget` | CSV record counts (the CSV rules); byte/word/match counts; tasks with no shell call | 1 shell (2 / 1 / `conventions` 2 and 1, `transfer` 2 and 1, `genesis/count_lines` 2 over five files) |
| D-0002 | paged-api | visible | a listing answers `{items, next}`; fold every page and follow `next` verbatim until null, one call per page, no probing | `http-tool`, `error-wrapping` | a single resource by id; `/secure` routes; a body with no `next` | one HTTP call per page, 2–4 pages (pages+1 / pages / `conventions` 4 and 5, `transfer` 4 and 5) |
| D-0003 | moved-v2 | loud | single-resource and status routes are served under `/v2`: call `/v2/...` first; a 410 naming a successor is the answer, call the named path once; a 404 on `/v2` means unversioned, fall back once | `http-tool`, `error-wrapping` | paging collection routes; `/secure` routes; a transient 502 or a 404 on the original path | 1 HTTP (2 / 1 / `conventions` 2, `transfer` 2) |
| D-0004 | csv-quoted | visible | parse CSV with Python's `csv` module in one shell call, never split on commas; a quoted field holds a comma and the split shifts its columns | `shell-tool`, `file-tool`, `tool-budget` | plain text line totals; JSON via the file tool; the TOTAL trailer (the footer rule, same parser) | 1 shell (2 / 1 / `conventions` 2) |
| D-0005 | footer-row | visible | an exported CSV ends with a `TOTAL` row that is not a record: `awk -F, 'NR>1 && $1!="TOTAL" ...'` before any sum or count | `shell-tool`, `file-tool`, `tool-budget` | the quoted-field rule (both apply on one file); plain line totals; JSON or API totals | 1 shell (2 / 1 / —) |
| D-0006 | token-route | loud | `/secure/...` answers 401 without the token: read `token.txt` with the file tool (unbudgeted), strip the newline, GET `/secure/<what>?token=<token>` on the first call | `http-tool`, `file-tool`, `error-wrapping` | routes outside `/secure`; a 410 naming `/v2`; a transient 502 | 1 HTTP (2 / 1 / —) |
| D-0007 | bom | loud | a `.json` file may open with U+FEFF: strip it (`lstrip('\ufeff')` or `utf-8-sig`) before `json.loads`; write outputs without it | `file-tool`, `output-schema` | CSV or text via the shell; HTTP bodies; parse failures that are not a leading mark | none — the bom tasks are unbudgeted and carry no floor |
| D-0008 | genesis: retry | — | a 502 marked transient is retried on the same path, up to twice (the world faults at most two leading calls); 401/404/410 and budget refusals are never retried; a reported error carries the cause verbatim | `http-tool`, `error-wrapping`, `tool-call-retry` | any 4xx or a budget refusal; a failure with no tool call behind it | — (`genesis` is unbudgeted; `probe` and `transfer` fault two leading calls) |
| D-0009 | genesis: budget plan | — | under a budget, plan the calls first and spend none on discovery: no `ls`/`cat`/`head`/`wc` before the answering command; independent inputs in one command; a dictated chain (`next`, a 410's successor) one call per link | `shell-tool`, `http-tool`, `tool-budget` | unbudgeted tasks; a call whose input only an earlier call can supply; schema-only tasks | the knowing count itself |

The decision text is generic across clothes: no filename, route or endpoint
from one instance appears in it (the stems, collections, resources and
`/secure` names of `suite/families/curriculum.py` and the `a.txt`, `/items`,
`/users/7` of `conventions` are all absent), so the same record fires on
`transfer`'s `part-1.tsv`, `/records` and `/account/42` as on the source.
Where two rules meet on one row — a CSV that is both exported and quoted, a
line total under a budget — the records co-apply (the boot says so on one
line) and each names the other as the rule for the part it does not settle.

The counterfactual of each decision cites the family line that shows the
overshoot — the naive policy (`suite/families/conventions.py:46` is the
`wc -l` count, `:52` the first page, `:56` the old path, `:62` the
`awk -F,`, `:67` the strict parse; `suite/families/curriculum.py:198` and
`:203` the trailer summed and counted, `:214` the bare `/secure` call) and
the world's construction (`conventions.py:32` builds the files with no
newline, `curriculum.py:128` the `next` field, `:143` the 410's cause,
`:192` the TOTAL row, `:210` the 401's cause, `:232` the byte order mark;
`suite/tools.py:73` the transient 502, `:70` and `:87` the budget refusals,
`suite/faults.py:18` the two faulted calls) — and `warrant.anchors` lists
the same lines. A seed has no observations; these are its anchors, and the
lint resolves record anchors only, so path anchors leave it green with no
priming warning.

## What the injection is expected to change

**`stream` and `economy`** (the `curriculum` pool, ten batches of eight,
faults off; `stream-probe` is two batches of five). Unseeded, the attached
and detached arms sit in one band — 0.46 against 0.54 on `stream`, 0.47
against 0.53 on `economy` — and per lesson the unseeded floor is `bom` 1.00,
`token-route` 0.8–1.0, `moved-v2` 0.25–0.64, `paged-api` and `csv-quoted`
0.45–0.73, and `footer-row` and `trailing-newline` 0.00 on every arm; on
the strict pool 0.34 against 0.33. The unseeded quality series read
`solution_economy` 0.23 against 0.29 and `turn_economy` 0.25 against 0.30,
with `method_transfer` evaluable only on `csv-quoted` rows. The seeded
attached arm is expected to:

- pass at first sight from batch 1 — near 1.0 on every lesson, the two
  silent shell lessons included — against the detached arm's ~0.5 band,
  since every batch is balanced over the seven lessons and the seed carries
  all seven;
- spend the knowing count: `solution_economy` at or near 1.0 on passed rows
  (one awk, one python, one `/v2` call, one page per page), and
  `turn_economy` near 1.0 except on `token-route`, where the file read is a
  turn the floor of one-per-call-plus-one does not count (2/3 at best);
- leave a replayable command on every shell lesson, so `method_transfer` is
  evaluable on `trailing-newline` and `footer-row` rows as well as
  `csv-quoted`, and near 1.0 — the awk and python commands read the
  convention, not the instance, and give the twin's gold;
- on `curriculum-strict`, pass within a budget that holds no discovery call
  — the knowledge-base question answered directly — where the unseeded
  arms tie at a third;
- file same-shape (`naive`) failures at or near zero from pass 1 in the
  evolution log, against the unseeded 10/11 and 12/12 on the silent lessons;
- and, at the consolidations, nominate nothing new on the seven lessons —
  the drafts the unseeded run refused or admitted (the fused `/v2`-and-token
  record, the `active:true` filter, the 410 retry) have no observation
  group to grow from. What the backward pass does with a store that is
  already right is itself a reading: the retirement leg
  (`applied_over_considered_below` 0.1 over 6 passes) should retire nothing,
  and a precision nomination on a record the guard fires too broadly (the
  budget plan on an unbudgeted row, the bom rule on a CSV) is the seed's
  own exclusions being tested.

The detached arm is the unseeded band on the same batches; the paired
difference per batch and per lesson is what the injection bought.

**`transfer`** (`genesis`, `conventions`, `transfer` whole and `api`
sampled, `http_fault_calls = 2`, three rounds of two). The seeded arm scores
the re-dressed clothes without re-discovery on the first pass:
`transfer/report_lines` and `chunk_lines` (fifteen and fourteen lines under
budgets of two and one — 0/0 unseeded), `paged_total` and `paged_active`,
`moved_account` and `moved_health`, beside their `conventions` sources, all
by the same records — nothing in the store names `part-1.tsv`, `/records`
or `/account/42`. Two ceilings hold on both arms and should be read as
such: with `http_fault_fraction` at its default 0.5 and two leading calls
faulted, `conventions/versioned_status` and `transfer/moved_health` are
faulted and budgeted at two calls, so no policy passes them (the two faults
are the budget); `conventions/paged_count` and `transfer/paged_total` are
faulted and budgeted exactly at two faults plus their pages, so only a pass
that retries the 502 (D-0008) and neither probes nor repeats a page
(D-0002, D-0009) passes them. `genesis/sum_numbers` and
`genesis/fetch_user_name` are faulted too but unbudgeted, so they pass under
D-0008's retries; `fetch_user_name` also exercises D-0003's fall-back
(`/v2/users/7` answers 404 in `genesis`, the unversioned path answers),
which is what keeps one record right on the same route the `conventions`
family serves under `/v2`.

**`baseline`, `cadence`, `model-sweep`** (the `genesis` and `conventions`
families under the default profile). `baseline` is saturated at 1.00 for
gpt-oss-120b already; the seed changes its call counts, not its pass rate.
On `cadence` and `model-sweep` the `conventions` rows are where the
injection shows, and the `20b` arm — which follows the 410's hint on every
moved route unseeded — is the arm on which the seed buys least on
`moved-v2` and most on the silent lessons. **`probe`** is the contract
check on a real model; with the seed injected, its reply log should show
every record consulted, guarded and disposed `applied` on the rows its
terms name and `not_applicable` on the rest — the disposition stream the
precision leg reads.

## Validating the seed

The seed is validated in a scratch store: `hgi genesis --store <scratch>`,
the decision files copied into its `decisions/`, `registry/ids.json`'s
`"D"` set to 9, then `hgi index` and `hgi lint`. The lint is green with no
warnings: every consultation latch keys on registered terms and carries
`not_this`, every counterfactual cites path anchors that need no store to
resolve, every premise carries a falsifier, the retirement latch is live,
and the ports for an `accepted` decision (consultation and retirement
required, revisit optional) are met. `hgi consult --store <scratch>
--problem "<a task prompt>"` latches the expected records via the index
and projects their payloads.
