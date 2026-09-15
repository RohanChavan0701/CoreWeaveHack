# Seed: the reasoning-core HARD tier

A hand-authored decision store for the world `experiments/reasoning-core-hard.toml` runs: Reasoning Core's
regex-following and cfg-generation instances at the harder tier (`suite/families/reasoning_core.py`, checkers in
`suite/families/_reasoning_core.py`, the `HARD` tier at `suite/families/_reasoning_core.py:129`, instances
pinned in `suite/data/reasoning-core-hard.jsonl` — twelve of each), in two families that differ only in slack:
`reasoning-core-hard` budgets the knowing policy's one verification call plus one, `reasoning-core-hard-strict`
budgets exactly that one call. This is what a mature store for the harder stream holds once the loop has seen
enough passes to draft, attack and admit the method — the target the loop is meant to reach, injected before the
first pass to measure what the method buys.

The method is the same one the moderate seed (`experiments/seeds/reasoning-core/`) carries, and it transfers to
this tier unchanged in substance: verify a candidate with the checker before answering, and pick a candidate the
pattern or grammar provably admits. Only the level-specific facts move — the regex constructs, the grammar
window, and which grammars trip the start-symbol trap.

## The harder tier, as it differs from the moderate one

The tier is `HARD = Tier(regex_level=5, cfg_level=3, cfg_tokens=(8, 14), …)`
(`suite/families/_reasoning_core.py:129`), on seed bases disjoint from the moderate tier, so the two tiers share
no instance.

- **Regex is level 5.** The twelve pinned patterns nest capturing and non-capturing `(?:…)` groups several deep,
  quantify whole groups (`([4-l])+`, `((\D{2,3})))??`, `(…)*`), use counted repetition (`{3,5}`, `{2,3}`,
  `{3,4}`), escaped metacharacter classes (`\w`, `\d`, `\D`, `\W`), escaped literal metacharacters (`\+`, `\)`,
  `\[`, `\]`, `\.`), the `\B` non-boundary anchor (`regex_10`), alternation (`regex_09`, `regex_11`), negated
  classes (`[^yiB]`) and ranges (`[J-g]`, `[4-l]`). They carry **no lookaround, no backreference and no
  possessive quantifier**, and `re.fullmatch` and the checker's `regex.fullmatch` agree on every construct in the
  set. A distinctive level-5 hazard: **many patterns match the empty string** (their whole body is optional, e.g.
  `(?:(([TND]MV*)?))?`), but `_is_sft_sample` (`suite/families/_reasoning_core.py:62`) refuses an empty,
  whitespace-bearing or non-printable string — so a witness must be made non-empty by taking one iteration of an
  optional or starred group.
- **Grammars are level 3 with an eight-to-fourteen-token required derivation.** `cfg_tokens=(8, 14)` is the
  witness-length window an instance is kept within, and the witness's own length becomes the instance's
  `min_tokens` — 8 to 11 across the pinned twelve. The grammars are larger and reach a recursive rule through
  more unit-rule indirection than the moderate tier, so the leftmost-derivation-from-the-stated-start method
  earns more.
- **The start-symbol trap hits nine of the twelve grammars.** NLTK reads the first rule's left side as the start
  symbol and the pinned rules are shuffled; on **nine of the twelve** (`cfg_01`, `cfg_02`, `cfg_04`, `cfg_05`,
  `cfg_06`, `cfg_07`, `cfg_08`, `cfg_09`, `cfg_10`) the first rule's left side is not `S`, so a correct sentence
  checked with `CFG.fromstring(G)` alone reports no parse or raises. The checker resets the start explicitly
  (`suite/families/_reasoning_core.py:95`); a pass that does not is told its right answer is wrong.

## The world, as the pass sees it

Every task presents as `("shell-tool", "tool-budget")`. The prompt states the pattern or the grammar, says to
check a candidate with the shell tool before answering, gives the call shape
(`python3 -c "import re,sys; print(bool(re.fullmatch(sys.argv[1], sys.argv[2])))" <pattern> <candidate>` for a
regex, `suite/families/reasoning_core.py:111`; "Python's NLTK is available: `nltk.CFG.fromstring`, then
`nltk.parse.earleychart.EarleyChartParser`" for a grammar, `suite/families/reasoning_core.py:121`), and ends
with `You have a budget of N shell calls.` — N = 2 in the lax family, 1 in the strict one
(`suite/families/reasoning_core.py:72`, `:127`). The hidden check is the generator's own verdict over the
returned string: `regex.fullmatch` after stripping backticks and blanks, refusing empty, whitespace-bearing or
non-printable strings (`suite/families/_reasoning_core.py:67`); NLTK Earley membership from the *stated* start
symbol, at least `min_tokens` and at most 60 tokens (`suite/families/_reasoning_core.py:82`).

What the pass sees of a consulted decision is one line of stakes and the decision text (`suite/agent.py`, the
consultation plan) — never the counterfactual or the exclusions. The payloads are therefore self-contained: each
carries the literal shell call the pass should run.

Facts of the environment the seed rests on, checked on 2026-09-14:

- The shell tool runs `subprocess.run(command, shell=True)` under `shell_env()`, which prefixes `PATH` with the
  driving interpreter's `bin` (`suite/tools.py:28`). Under `uv run hgi …` that is the venv's python 3, with
  `nltk` and `regex` present; the system `python3` has no `nltk`, so a runner launched outside the venv would
  break every grammar verification. This is premise p1 of D-0001 and its falsifier.
- The tool layer increments the call counter before checking the budget, so a refused over-budget call is counted
  (`suite/tools.py:140`, `:142`, `:145`); a nonzero exit is an error and also counted (`suite/tools.py:152`).
- The `-hard` families carry the same `requires = ("nltk", "regex")` preflight as the moderate families
  (`suite/families/reasoning_core.py:159`), so an arm whose shell python cannot import them is refused before
  pass 1 (item 53).

## The mature store: four method decisions

The lesson of this world is a method, not a convention of an instance, and it is the same method the moderate
seed encodes. Every decision keys its consultation latch on `shell-tool` and `tool-budget` and is separated from
the others by its exclusions.

| id | decision, in one line | excludes | stakes / floor saved |
|---|---|---|---|
| D-0001 | Derive the candidate from the structure first, spend the shell call on the checker's own verdict over that exact candidate, return the string the call printed True for; the verifying call is the first call. Carries the literal regex one-liner (both arguments single-quoted) and the grammar heredoc. | answers that are programs, files or numbers; tasks with no checker in the prompt; shell tasks whose calls are the work | first-sight pass on the unverified band the harder tier widens; `solution_economy` 1.0 instead of 0.5 or a refused third call |
| D-0002 | The regex witness rule for level 5: left to right, each construct's cheapest witness (escaped classes `\w`/`\d`/`\D`/`\W`, escaped literals `\+`/`\)`/`\[`/`\]`, `\B` needs the same class on both sides, `[^set]` one char outside, `x{m,n}` m copies, `A\|B` the cheapest satisfiable alternative); a quantifier binds only the single atom before it (`financial{3,5}` = `financialll`); a group repeats as a whole; make an all-optional pattern non-empty with one iteration; non-empty, printable, no whitespace, no backticks. | grammar tasks; tasks asking for a regex; strings with a constraint outside the pattern | the repair call the strict pool does not have; an all-optional pattern answered empty |
| D-0003 | The grammar derivation rule for level 3: leftmost derivation from the stated start, repeat a recursive rule until the terminal count reaches the eight-to-fourteen minimum, close with terminal rules; ≤ 60 tokens, unquoted, single-spaced. Carries the literal heredoc that sets `CFG(Nonterminal(start), …)` explicitly, catches exceptions, and prints the count and the verdict. | regex tasks; tasks asking for the grammar, a tree or a derivation; grammars checked by something other than the shell's NLTK | nine of twelve grammars report a correct sentence as a non-member without the explicit start; the pass would repair a right answer into a wrong one |
| D-0004 | The budget rule: every call counts, refused and failed ones included; the verification is the first call; no probing (`import nltk`, `which python3`), no printing, no splitting; the command exits 0 whatever the verdict; under a budget of 1 a False verdict is repaired by re-derivation, never by a second call; never a third call. | tasks with no stated budget; HTTP budgets; budgets of three or more | `tool_budget_respected` on the strict pool; a third call refused with `call budget of 2 exceeded at call 3` |

Latches, per decision: one `consultation` latch on `work-shape` (`shell-tool`, `tool-budget`) with the
exclusions above, owed `apply`, dispositive; one `revisit` latch on `world-state` (`suite-v1`;
`solution_economy < 0.9` for D-0001, `task_pass_rate < 0.9` for D-0002 and D-0003,
`tool_budget_respected < 1.0` for D-0004; persistence 2) that re-opens the warrant if the method stops paying;
the standard `retirement` latch (applied over considered below 0.1 across 6 passes). Counterfactuals and warrant
anchors cite `path:line` into `suite/families/reasoning_core.py`, `suite/families/_reasoning_core.py` and
`suite/tools.py`, since a seed has no observations; premises carry falsifiers, the loudest being "a shell call
that prints `ModuleNotFoundError` for nltk".

What is loud, visible and invisible in the trace: the budget overshoot (D-0004) is loud — a refused call with
`call budget of 2 exceeded at call 3` in the tool errors. The repair call (D-0001) is visible — two shell
commands where one would do, `solution_economy` 0.5. The start-symbol trap (D-0003) is visible but misleading —
a False verdict on a member, which reads as a wrong candidate. The quantifier-scope miss and the empty-string
witness (D-0002) are invisible until the verdict: nothing in the trace says why the string failed.

## The compare/contrast expectation

The experiment deals the 24 harder instances into six batches of four, balanced over the two generators; pass k
meets batch k at first sight and batches 1 and 2 are revisited after the stream. Arms: `qwen-attached` (the loop,
empty store), `qwen-detached` (the actor alone), `20b-attached` (gpt-oss-20b under the same teacher),
`qwen-strict` and `qwen-strict-detached` (the same instances at a budget of one), and their seeded twins
`qwen-seeded` and `qwen-strict-seeded` (`seed = "reasoning-core-hard"`), which start from these four decisions
injected before pass 1 — `hgi seed reasoning-core-hard --store <root>` does the same by hand.

Expected, per batch and scorer:

- **Unseeded** (`qwen-detached`, and `qwen-attached` before the loop has admitted anything): first-sight
  `task_pass_rate` below the moderate tier's in the strict pool — the harder patterns and longer derivations
  drop the unverified ceiling — and higher in the lax pool where the repair call rescues a wrong first candidate;
  `solution_economy` around 0.5 in the lax pool (two calls over a floor of one); occasional
  `tool_budget_respected` failures from a third call.
- **Seeded** (`qwen-seeded`, `qwen-strict-seeded`): a member produced first time on every batch — first-sight
  `task_pass_rate` near 1.0 in both pools, `solution_economy` near 1.0 (the one verifying call),
  `tool_budget_respected` 1.0 on the strict twin. The gap is the value of the four payloads; the strict pool is
  where it shows, because there the unseeded pass cannot buy its way out with a repair.
- The revisit of batches 1 and 2 after the stream should show no drop for the seeded arm (the method is
  instance-independent, and level-independent — it is the moderate seed's method), which separates retention from
  transfer.

If the seeded strict arm does not reach the band, the first thing to read is the shell commands in the trace
against the literal calls in D-0001 and D-0003: a pass that ran `CFG.fromstring` without the explicit start, that
answered an all-optional pattern with the empty string, or that made a probing first call, has not applied the
payload; a `ModuleNotFoundError` has broken premise p1.

## Validation

The seed lints green in a fresh genesis store: `hgi genesis --store <scratch>/store`, then
`hgi seed reasoning-core-hard --store <scratch>/store --model Qwen/Qwen3.6-35B-A3B --no-commit`, then `hgi index`
and `hgi lint`. The decision files are the schema of `hgi.types.Decision` exactly; they are derived from the
moderate seed's four decisions with only the level-specific text and the code anchors rewritten for the harder
tier, so the envelope is carried once. The seed ships no `vocabulary.json`: the shape the stream presents is
exactly `shell-tool` + `tool-budget`, and precision is recovered through `not_this`.
