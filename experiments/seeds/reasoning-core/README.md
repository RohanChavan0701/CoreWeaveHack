# Seed: the reasoning-core stream

A hand-authored decision store for the world `experiments/reasoning-core.toml` runs: Reasoning Core's
regex-following and cfg-generation instances (`suite/families/reasoning_core.py`, checkers in
`suite/families/_reasoning_core.py`, instances pinned in `suite/data/reasoning-core.jsonl` — twelve of each),
in two families that differ only in slack: `reasoning-core` budgets the knowing policy's one verification call
plus one, `reasoning-core-strict` budgets exactly that one call. This is what a mature store for the stream
holds once the loop has seen enough passes to draft, attack and admit the method — the target the loop is meant
to reach, injected before the first pass to measure what the method buys.

## The world, as the pass sees it

Every task presents as `("shell-tool", "tool-budget")`. The prompt states the pattern or the grammar, says
to check a candidate with the shell tool before answering, gives the call shape (`python3 -c "import re,sys;
print(bool(re.fullmatch(sys.argv[1], sys.argv[2])))" <pattern> <candidate>` for a regex; "Python's NLTK is
available: `nltk.CFG.fromstring`, then `nltk.parse.earleychart.EarleyChartParser`" for a grammar), and ends
with `You have a budget of N shell calls.` — N = 2 in the lax family, 1 in the strict one. The hidden check
is the generator's own verdict over the returned string: `regex.fullmatch` after stripping backticks and
blanks, refusing empty, whitespace-bearing or non-printable strings; NLTK Earley membership from the *stated*
start symbol, at least `min_tokens` and at most 60 tokens.

What the pass sees of a consulted decision is one line of stakes and the decision text
(`suite/agent.py`, the consultation plan) — never the counterfactual or the exclusions. The payloads below
are therefore self-contained: each carries the literal shell call the pass should run.

Facts of the environment the seed rests on, checked on 2026-09-13:

- The shell tool runs `subprocess.run(command, shell=True)` in the task's workdir (`suite/tools.py`). Under
  `uv run hgi …` the venv's `bin` is first on the inherited PATH, so the shell's `python3` is 3.14 with
  `nltk` 3.10.3 and `regex` 2026.9.10. The system `python3` has no `nltk`: a runner launched outside the venv
  would break every grammar verification. This is premise p1 of D-0001 and its falsifier.
- The prompt's example uses `re`; the checker uses `regex`. On the twelve pinned patterns (level 3: alternation,
  groups, counted repetition, `\b`/`\B`, possessive `*+`/`?+`, lazy `+?`) the two agree — Python 3.11+ `re`
  compiles possessive quantifiers.
- NLTK takes the first production's left side as the start symbol; the pinned rules are shuffled. On **five of
  the twelve** grammars (`cfg_02`, `cfg_05`, `cfg_06`, `cfg_09`, `cfg_11`) the first rule is not `S`, and a
  correct sentence checked with `CFG.fromstring(G)` alone reports no parse. The checker resets the start
  explicitly (`_reasoning_core.py:84-86`); a pass that does not is told its right answer is wrong.
- The tool layer increments the call counter before checking the budget, so a refused call is counted
  (`suite/tools.py:84-87`); a nonzero exit is an error and also counted.
- The "simplest witness per construct" rule (D-0002) produces a `fullmatch` witness on all twelve pinned
  patterns; a leftmost derivation repeating one recursive rule (D-0003) reaches `min_tokens` within 60 on all
  twelve pinned grammars.

## What the probe saw

`runs/rc-probe/attached/` ran two passes of three lax tasks each on Qwen3.6-35B-A3B under DeepSeek-V4-Pro as
teacher. First sight was 1.00 on all six, but economy was 0.39 and 0.67: the passes spent the repair call. Two
observations were filed and nothing was admitted:

- a pass on `regex_05` made a third shell call under the budget of two and had it refused (the budget
  overshoot D-0004 names);
- the first candidate for `regex_11` (`piece{3}[^Y1F]\w*`) was `pieceeeXabc` — the `{3}` had bound only the
  `e`, and the pass had read it as prose (the quantifier-scope miss D-0002 names).

Both groups sat below the independence bar (one session each), and the one draft that reached a nomination was
refused at parse for keying on `regex-generation`, a term outside the closed work-shape vocabulary. The seed
keys on the registered terms only and ships no `vocabulary.json`: the shape the stream presents is exactly
`shell-tool` + `tool-budget`, and precision is recovered through `not_this`.

## The mature store: four method decisions

The lesson of this world is a method, not a convention of an instance. Every decision keys its consultation
latch on `shell-tool` and `tool-budget` and is separated from the others by its exclusions.

| id | decision, in one line | excludes | stakes / floor saved |
|---|---|---|---|
| D-0001 | Derive the candidate from the structure first, spend the shell call on the checker's own verdict over that exact candidate, return the string the call printed True for; the verifying call is the first call. Carries the literal regex one-liner (both arguments single-quoted) and names the heredoc shape for grammars. | answers that are programs, files or numbers; tasks with no checker in the prompt; shell tasks whose calls are the work | first-sight pass on what is otherwise the ~0.5 unverified band; `solution_economy` 1.0 (one call over the knowing floor of one) instead of 0.5 |
| D-0002 | The regex witness rule: left to right, each construct's cheapest witness (`[^set]` one char outside, `x*`/`x?` nothing, `x+` one, `x{m,n}` m copies, `A\|B` the cheapest satisfiable non-empty alternative, `\b`/`\B` placement, backreference verbatim); a quantifier binds only the single atom before it (`piece{3}` = `pieceee`); non-empty, printable, no whitespace, no backticks. | grammar tasks; tasks asking for a regex; strings with a constraint outside the pattern | the repair call the strict pool does not have; the probe's `regex_11` miss |
| D-0003 | The grammar derivation rule: leftmost derivation from the stated start, repeat a recursive rule until the terminal count reaches the minimum, close with terminal rules; ≤ 60 tokens, unquoted, single-spaced. Carries the literal heredoc that sets `CFG(Nonterminal(start), …)` explicitly, catches exceptions, and prints the count and the verdict. | regex tasks; tasks asking for the grammar, a tree or a derivation; grammars checked by something other than the shell's NLTK | five of twelve grammars report a correct sentence as a non-member without the explicit start; the pass would repair a right answer into a wrong one |
| D-0004 | The budget rule: every call counts, refused and failed ones included; the verification is the first call; no probing (`import nltk`, `which python3`), no printing, no splitting; the command exits 0 whatever the verdict; under a budget of 1 a False verdict is repaired by re-derivation, never by a second call; never a third call. | tasks with no stated budget; HTTP budgets; budgets of three or more | `tool_budget_respected` on the strict pool; the probe's `regex_05` third call |

Latches, per decision: one `consultation` latch on `work-shape` (`shell-tool`, `tool-budget`) with the
exclusions above, owed `apply`, dispositive; one `revisit` latch on `world-state` (`suite-v1`;
`solution_economy < 0.9` for D-0001, `task_pass_rate < 0.9` for D-0002 and D-0003,
`tool_budget_respected < 1.0` for D-0004; persistence 2) that re-opens the warrant if the method stops
paying; the standard `retirement` latch (applied over considered below 0.1 across 6 passes). Counterfactuals
and warrant anchors cite `path:line` into `suite/families/reasoning_core.py`, `suite/families/_reasoning_core.py`
and `suite/tools.py`, since a seed has no observations; premises carry falsifiers, the loudest being "a shell
call that prints `ModuleNotFoundError` for nltk".

What is loud, visible and invisible in the trace: the budget overshoot (D-0004) is loud — a refused call with
`call budget of 2 exceeded at call 3` in the tool errors. The repair call (D-0001) is visible — two shell
commands where one would do, `solution_economy` 0.5. The start-symbol trap (D-0003) is visible but misleading
— a False verdict on a member, which reads as a wrong candidate. The quantifier-scope miss (D-0002) is
invisible until the verdict: nothing in the trace says why the string failed.

## The compare/contrast expectation

The experiment deals the 24 instances into six batches of four, balanced over the two generators; pass k meets
batch k at first sight and batches 1 and 2 are revisited after the stream. Arms: `qwen-attached` (the loop,
empty store), `qwen-detached` (the actor alone), `20b-attached` (gpt-oss-20b under the same teacher),
`qwen-strict` and `qwen-strict-detached` (the same instances at a budget of one), and their seeded twins
`qwen-seeded` and `qwen-strict-seeded` (`seed = "reasoning-core"`), which start from these four decisions
injected before pass 1 — `hgi seed reasoning-core --store <root>` does the same by hand.

Expected, per batch and scorer:

- **Unseeded** (`qwen-detached`, and `qwen-attached` before the loop has admitted anything — which in the
  probe was still nothing after two consolidations): first-sight `task_pass_rate` on the ~0.5 band in the
  strict pool, higher in the lax pool where the repair call rescues a wrong first candidate;
  `solution_economy` around 0.5 in the lax pool (two calls over a floor of one); occasional
  `tool_budget_respected` failures from a third call.
- **Seeded** (`qwen-attached` + seed, `qwen-strict` + seed): a member produced first time on every batch —
  first-sight `task_pass_rate` near 1.0 in both pools, `solution_economy` near 1.0 (the one verifying call),
  `tool_budget_respected` 1.0 on `qwen-strict`. The gap is the value of the four payloads; the strict pool is
  where it shows, because there the unseeded pass cannot buy its way out with a repair.
- The revisit of batches 1 and 2 after the stream should show no drop for the seeded arm (the method is
  instance-independent), which separates retention from transfer.

If the seeded strict arm does not reach the band, the first thing to read is the shell commands in the trace
against the literal calls in D-0001 and D-0003: a pass that ran `CFG.fromstring` without the explicit start,
or a probing first call, has not applied the payload; a `ModuleNotFoundError` has broken premise p1.

## Validation

The seed lints green in a fresh genesis store: `hgi genesis --store <scratch>/store`, copy `decisions/*.json`
in, set `"D": 4` in `registry/ids.json`, `hgi index`, `hgi lint`. The decision files are the schema of
`hgi.types.Decision` exactly; they are generated from one skeleton so the envelope is derived once.
