# reasoning-core/qwen-attached — evolution

attached on `Qwen/Qwen3.6-35B-A3B`; 6 batches × 4 tasks from reasoning-core, seed 0; revisit [1, 2].

## Passes

| pass | batch | first sight | economy / turns / transfer | symptoms | in context | mentions | filed | consolidation after |
|---|---|---|---|---|---|---|---|---|
| 1 | 1 | 0.75 | 0.40 / 0.47 / — | error:shell-timeout=1 pass=3 | none | — | 4 obs, 1 prop |  |
| 2 | 2 | 1.00 | 0.33 / 0.47 / — | pass=4 | none | — | 3 obs, 1 prop | K-0001: 3 groups, 2 at the bar; admitted D-0001 D-0002; 1 admitted D-0001, 1 admitted D-0002 |
| 3 | 3 | 1.00 | 0.58 / 0.85 / — | pass=4 | D-0001 D-0002 | — | 1 obs, 1 prop |  |
| 4 | 4 | 0.50 | 0.12 / 0.20 / — | pass=2 wrong=2 | D-0001 D-0002 | — | 4 obs, 1 prop | K-0002: 2 groups, 1 at the bar; admitted D-0003; 1 The agent exceeding the tool-call budget is a failure of budget enforcement, not a failure of the agent's ability to count its own calls, so the premise that the agent can count its own tool calls is not falsified by this evidence.; still-holds: D-0002 stands, 1 admitted D-0003 |
| 5 | 5 | 0.75 | 0.44 / 0.52 / — | error:not-json=1 pass=3 | D-0001 D-0002 D-0003 | — | 2 obs, 1 prop |  |
| 6 | 6 | 0.75 | 0.46 / 0.54 / — | error:not-json=1 pass=3 | D-0001 D-0002 D-0003 | — | 2 obs, 1 prop | K-0003: 3 groups, 2 at the bar; admitted D-0004 D-0005; 1 admitted D-0004, 1 admitted D-0005 |
| 7 (revisit) | 1 | 1.00 | 0.35 / 0.49 / — | pass=4 | D-0003 D-0004 D-0005 | — | 3 obs, 1 prop |  |
| 8 (revisit) | 2 | 0.50 | 0.19 / 0.27 / — | error:not-json=2 pass=2 | D-0003 D-0004 D-0005 | — | 2 obs, 1 prop |  |

## Lessons

Each cell is the lesson's rows in that pass: ✓ passed, N the naive first-contact outcome (a same-shape failure), W another wrong answer, E a harness or tool error. `mentioned` marks passes with a record in context whose text uses the lesson's words.

| lesson | tier | p1 | p2 | p3 | p4 | p5 | p6 | p7r | p8r | first sight | economy / turns / transfer | naive before / after first mention | first mention | revisit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| reasoning-core | — | ✓✓✓E | ✓✓✓✓ | ✓✓✓✓ | ✓✓WW | ✓✓✓E | ✓✓E✓ | ✓✓✓✓ | ✓E✓E | 0.79 (19/24) | 0.39 / 0.51 / — | 0.00 (0/24) / — | — | batch 1: 4/4, batch 2: 2/4 |

## What the passes noticed

Each observation as the close filed it, with the shape the blind coder gave it at the next consolidation (`open` until one has run); a group reaches the bar when its observations come from as many distinct sessions as the bar asks.

- pass 1 O-0001 [tool-budget]: The first attempt in reasoning-core/cfg_02 issued four shell calls instead of the prompt's two-call budget, missing the explicit constraint before attempting grammar verification.
- pass 1 O-0002 [shell-tool]: In reasoning-core/cfg_07, the first shell call failed with a ModuleNotFoundError for nltk because the dependency was not installed beforehand.
- pass 1 O-0003 [other(regex pattern match convention)]: The first attempt submitted 'Mfutureimprtr', which failed to match the required regex pattern '[1MV](?:futureimportant{1,3}[rzu])+', missing the convention that the candidate must fully match the regex.
- pass 1 O-0004 [shell-tool]: The task reasoning-core/cfg_02 failed due to a missing NLTK module and a subsequent timeout.
- pass 2 O-0005 [tool-budget]: The first attempt in reasoning-core/cfg_04 missed the convention of respecting the 2-shell-call budget, executing four shell commands before exhausting the limit.
- pass 2 O-0006 [tool-budget]: In reasoning-core/cfg_05, the first attempt missed the 2-shell-call budget convention, executing four calls and triggering budget-exceeded errors before succeeding via manual verification.
- pass 2 O-0007 [shell-tool]: The first shell attempt in reasoning-core/cfg_03 failed with a non-transient ModuleNotFoundError because the environment lacked the `nltk` library, contradicting the prompt's availability assumption.
- K-0001 group [other(regex pattern mismatch)] ← O-0003 from S-0001 — below the bar
- K-0001 group [shell-tool] ← O-0002 O-0004 O-0007 from S-0001 S-0002 — at the bar
- K-0001 group [tool-budget] ← O-0001 O-0005 O-0006 from S-0001 S-0002 — at the bar
- K-0001 nominated pre-install at new-decision → admitted D-0001
- K-0001 nominated budget-cap at new-decision → admitted D-0002
- pass 3 O-0008 [tool-budget]: reasoning-core/cfg_00 missed the convention of verifying library availability and installing it before running the core script, causing it to exceed the 2-call budget.
- pass 4 O-0009 [tool-budget]: The task reasoning-core/regex_09 issued four shell calls instead of two, missing the hard-limit convention that the agent must plan its work to fit within the specified tool-call budget.
- pass 4 O-0010 [tool-budget]: In `reasoning-core/regex_11`, the first attempt issued three shell calls to test regex candidates, violating the prompt's hard limit of two; it would have passed by sequencing the tests to stay within the two-call budget.
- pass 4 O-0011 [tool-budget]: In task reasoning-core/cfg_09, the first attempt missed the convention that the execution environment lacks the `nltk` library and `pip`, requiring an installation step that consumes the shell call budget.
- pass 4 O-0012 [tool-budget]: reasoning-core/cfg_01 missed the convention that non-standard libraries are not pre-installed in the execution environment and must be installed before use, consuming a tool call against the strict budget.
- K-0002 group [other(regex pattern match convention)] ← O-0003 from S-0001 — below the bar
- K-0002 group [tool-budget] ← O-0008 O-0009 O-0010 O-0011 O-0012 from S-0003 S-0004 — at the bar
- K-0002 nominated budget-planning at new-decision → admitted D-0003
- K-0002 nominated D-0002 at counterfactual-edit → The agent exceeding the tool-call budget is a failure of budget enforcement, not a failure of the agent's ability to count its own calls, so the premise that the agent can count its own tool calls is not falsified by this evidence.; still-holds: D-0002 stands
- pass 5 O-0013 [tool-budget]: reasoning-core/cfg_10's first attempt failed by attempting to install `nltk` despite the prompt stating it was available, and by exceeding the 2-shell-call budget through exploratory testing rather than a single planned derivation; it would have passed by directly using the available library and planning a single derivation call within the budget, adhering to the convention of verifying tool availability and respecting call limits.
- pass 5 O-0014 [other(verify tool/library availability before execution)]: The first shell call in reasoning-core/cfg_06 failed with a ModuleNotFoundError for nltk because the pass assumed the library was available without installing it first.
- pass 6 O-0015 [tool-budget]: The first attempt in reasoning-core/cfg_08 exhausted its 2-shell-call budget running `python` and `python3` against a non-existent script, never generating or verifying the grammar output; writing the verification script once and executing it with `python3` within the call limit would have passed, adhering to the convention that strict tool budgets require executing core work rather than probing the environment.
- pass 6 O-0016 [other(verify tool/library availability before execution)]: The pass missed the convention of verifying tool/library availability before execution, resulting in a ModuleNotFoundError for nltk on the first shell call.
- K-0003 group [other(regex pattern match convention)] ← O-0003 from S-0001 — below the bar
- K-0003 group [other(verify tool/library availability before execution)] ← O-0014 O-0016 from S-0005 S-0006 — at the bar
- K-0003 group [tool-budget] ← O-0013 O-0015 from S-0005 S-0006 — at the bar
- K-0003 nominated library-availability at new-decision → admitted D-0004
- K-0003 nominated tool-budget-planning at new-decision → admitted D-0005
- pass 7 O-0017 [open]: reasoning-core/cfg_07 failed its initial shell call because the `nltk` library was not pre-installed in the environment.
- pass 7 O-0018 [open]: In task reasoning-core/cfg_02, the initial shell call failed with a ModuleNotFoundError for nltk because the library was not pre-installed.
- pass 7 O-0019 [open]: In task reasoning-core/regex_10, the first attempt missed the convention of the two-shell-call budget limit.
- pass 8 O-0020 [open]: The task `reasoning-core/cfg_04` failed its first attempt when the shell call crashed with a `ModuleNotFoundError` for `nltk` instead of verifying the library's availability or installing it beforehand, missing the convention of checking environment dependencies before execution.
- pass 8 O-0021 [open]: In reasoning-core/cfg_05, the first attempt missed the task's tool-call budget of 2 shell calls, using 4 instead.

## Records

| record | admitted after pass | mentions | decision |
|---|---|---|---|
| D-0001 | 2 | — | Before using a non-standard library in a shell call, verify its availability and install it if missing, reserving subsequent calls for the core task. |
| D-0002 | 2 | — | When a task specifies a maximum number of tool calls, plan the work to fit within that budget, and stop issuing calls once the limit is reached. |
| D-0003 | 4 | — | When a task imposes a strict limit on tool calls, plan the sequence of operations to complete the core work within that limit, reserving calls for essential steps and avoiding iterative or exploratory calls that risk exhaustion. |
| D-0004 | 6 | — | Before executing code that imports a library, verify the library is available in the execution environment; if it is not, install it or use a standard-library alternative. |
| D-0005 | 6 | — | When a task specifies a maximum number of tool calls, plan the work to fit within that budget, and before using a non-standard library in a shell call, verify its availability and install it if missing, reserving subsequent calls for the core task. |
