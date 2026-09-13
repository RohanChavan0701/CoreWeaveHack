# reasoning-core/qwen-strict — evolution

attached on `Qwen/Qwen3.6-35B-A3B`; 6 batches × 4 tasks from reasoning-core-strict, seed 0; revisit [1, 2].

## Passes

| pass | batch | first sight | economy / turns / transfer | symptoms | in context | mentions | filed | consolidation after |
|---|---|---|---|---|---|---|---|---|
| 1 | 1 | 0.75 | 0.33 / 0.46 / — | error:not-json=1 pass=3 | none | — | 3 obs, 1 prop |  |
| 2 | 2 | 1.00 | 0.71 / 0.79 / — | pass=4 | none | — | 2 obs, 1 prop | K-0001: 2 groups, 2 at the bar; admitted D-0001 D-0002; 1 admitted D-0001, 1 admitted D-0002 |
| 3 | 3 | 0.75 | 0.46 / 0.54 / — | pass=3 wrong=1 | D-0001 D-0002 | — | 3 obs, 1 prop |  |
| 4 | 4 | 1.00 | 0.88 / 0.83 / — | pass=4 | D-0001 D-0002 | — | 2 obs, 1 prop | K-0002: 3 groups, 1 at the bar; admitted D-0003; 1 The pass on `reasoning-core-strict/cfg_09` executed two shell calls without penalty, directly falsifying the premise that the task environment enforces a strict budget of one shell call.; reversed: premise p1 of D-0002 reversed, 1 admitted D-0003, 1 refused by the floor: 1 distinct session |
| 5 | 5 | 1.00 | 0.62 / 0.71 / — | pass=4 | D-0002 D-0003 | — | 2 obs, 0 prop |  |
| 6 | 6 | 0.75 | 0.38 / 0.46 / — | pass=3 wrong=1 | D-0002 D-0003 | — | 4 obs, 1 prop | K-0003: 2 groups, 1 at the bar; admitted D-0004; 1 The pass's finding cites a specific run , 1 The pass's finding cites evidence of multiple shell calls allowed without penalty, directly contradicting the premise's strict budget of one shell call.; reversed: premise p1 of D-0002 reversed, 1 The pass's finding cites evidence that the task environment allowed multiple shell calls without penalty, directly falsifying premise p1's claim of a strict one-call budget.; reversed: premise p1 of D-0002 reversed, 1 The pass's finding cites evidence that the task environment allowed multiple shell calls without penalty, directly falsifying the premise that a strict one-call budget is enforced.; reversed: premise p1 of D-0002 reversed, 1 The pass's finding cites reasoning-core-strict/cfg_11 exceeding the one-call budget, which directly falsifies premise p1's claim of a strict one-call budget.; reversed: premise p1 of D-0002 reversed, 1 admitted D-0004 |
| 7 (revisit) | 1 | 1.00 | 0.62 / 0.71 / — | pass=4 | D-0002 D-0004 | — | 4 obs, 1 prop |  |
| 8 (revisit) | 2 | 1.00 | 0.75 / 0.83 / — | pass=4 | D-0002 D-0004 | — | 2 obs, 1 prop |  |

## Lessons

Each cell is the lesson's rows in that pass: ✓ passed, N the naive first-contact outcome (a same-shape failure), W another wrong answer, E a harness or tool error. `mentioned` marks passes with a record in context whose text uses the lesson's words.

| lesson | tier | p1 | p2 | p3 | p4 | p5 | p6 | p7r | p8r | first sight | economy / turns / transfer | naive before / after first mention | first mention | revisit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| reasoning-core-strict | — | ✓✓E✓ | ✓✓✓✓ | ✓✓✓W | ✓✓✓✓ | ✓✓✓✓ | ✓✓W✓ | ✓✓✓✓ | ✓✓✓✓ | 0.88 (21/24) | 0.56 / 0.63 / — | 0.00 (0/24) / — | — | batch 1: 4/4, batch 2: 4/4 |

## What the passes noticed

Each observation as the close filed it, with the shape the blind coder gave it at the next consolidation (`open` until one has run); a group reaches the bar when its observations come from as many distinct sessions as the bar asks.

- pass 1 O-0001 [tool-budget]: The `reasoning-core-strict/cfg_00` first attempt missed the 1-shell-call budget convention by failing to account for the missing `nltk` dependency, which required a second shell call to install it and exceed the limit.
- pass 1 O-0002 [tool-budget]: reasoning-core-strict/regex_08 missed the shell call budget convention of 1 by attempting a second verification, which was refused as a non-transient fault.
- pass 1 O-0003 [other(missing dependency before import)]: In `reasoning-core-strict/cfg_01`, the first attempt to parse the CFG string failed because the `nltk` module was not installed, violating the convention of ensuring dependencies are available before import.
- pass 2 O-0004 [tool-budget]: In reasoning-core-strict/cfg_10, the first attempt missed the convention of limiting shell calls to a budget of 1, triggering a second call to install nltk and exceeding the budget.
- pass 2 O-0005 [other(missing dependency before import)]: In task reasoning-core-strict/cfg_04, the first attempt to parse the CFG failed because the `nltk` package was not installed, despite the prompt claiming it was available.
- K-0001 group [other(missing dependency before import)] ← O-0003 O-0005 from S-0001 S-0002 — at the bar
- K-0001 group [tool-budget] ← O-0001 O-0002 O-0004 from S-0001 S-0002 — at the bar
- K-0001 nominated dependency-availability at new-decision → admitted D-0001
- K-0001 nominated shell-call-budget at new-decision → admitted D-0002
- pass 3 O-0006 [tool-budget]: The first attempt in `reasoning-core-strict/regex_09` exceeded the one-shell-call budget by making two verification calls; a single call would have sufficed to verify the candidate and stay within the task's strict budget convention.
- pass 3 O-0007 [other(verify library availability before import)]: In reasoning-core-strict/cfg_05, the first shell attempt failed with a non-transient ModuleNotFoundError for nltk, missing the convention to verify non-standard library availability before import.
- pass 3 O-0008 [tool-budget]: In task reasoning-core-strict/cfg_08, the first shell call to parse the grammar failed due to a missing nltk dependency, exhausting the strict one-shell-call budget and preventing subsequent installation or verification steps.
- pass 4 O-0009 [tool-call-retry]: The pass attempted a tool call to `/submit` that failed with a non-transient HTTP 404, which was corrected by proceeding to return the shell-verified result.
- pass 4 O-0010 [other(verify library availability before import)]: The first attempt missed the convention of verifying library availability before importing, causing a non-transient ModuleNotFoundError in reasoning-core-strict/cfg_09.
- K-0002 group [http-tool] ← O-0009 from S-0004 — below the bar
- K-0002 group [other(verify library availability before import)] ← O-0007 O-0010 from S-0003 S-0004 — at the bar
- K-0002 group [tool-budget] ← O-0006 O-0008 from S-0003 — below the bar
- K-0002 nominated library-availability at hook-edit → admitted D-0003
- K-0002 nominated self-sufficient-shell at new-decision → refused by the floor: 1 distinct session(s) in the evidence (S-0003) against the bar 2; the adjudicator's decline(insufficient independence: the draft's evidence anchors only one distinct session (S-0003) against the bar of 2, so the floor refuses it regardless of other claims) was overridden: a decline stands only on an upheld premise kill
- K-0002 nominated D-0002 at counterfactual-edit → The pass on `reasoning-core-strict/cfg_09` executed two shell calls without penalty, directly falsifying the premise that the task environment enforces a strict budget of one shell call.; reversed: premise p1 of D-0002 reversed
- pass 5 O-0011 [tool-budget]: In task reasoning-core-strict/regex_06, the pass exceeded the one-shell-call budget by issuing a second shell command, which was refused as a non-transient fault.
- pass 5 O-0012 [tool-budget]: In reasoning-core-strict/cfg_02, the first shell call missed the convention of verifying library availability before importing, causing a ModuleNotFoundError that forced a second call.
- pass 6 O-0013 [tool-budget]: In `reasoning-core-strict/regex_10`, the first attempt tested `Mfutureimprtr` against the regex and then issued a second shell call, violating the one-call budget; it would have passed by deriving a valid match like `Mfutureimpr` and returning it directly, respecting the strict shell-call limit that the task enforces.
- pass 6 O-0014 [tool-budget]: The pass on reasoning-core-strict/cfg_11 missed the one-shell-call budget convention on its first attempt, making two shell calls instead of one.
- pass 6 O-0015 [tool-budget]: The first shell command in reasoning-core-strict/cfg_03 failed with a ModuleNotFoundError for nltk, missing the convention of verifying non-standard library availability before import.
- pass 6 O-0016 [tool-budget]: In task reasoning-core-strict/cfg_06, the first shell attempt missed the convention of verifying non-standard library availability before import, directly importing `nltk` without checking for installation.
- K-0003 group [tool-budget] ← O-0006 O-0008 O-0011 O-0012 O-0013 O-0014 O-0015 O-0016 from S-0003 S-0005 S-0006 — at the bar
- K-0003 group [tool-call-retry] ← O-0009 from S-0004 — below the bar
- K-0003 nominated budget-exhaustion at counterfactual-edit → admitted D-0004
- K-0003 nominated D-0002 at counterfactual-edit → The pass's finding cites evidence of multiple shell calls allowed without penalty, directly contradicting the premise's strict budget of one shell call.; reversed: premise p1 of D-0002 reversed
- K-0003 nominated D-0002 at counterfactual-edit → The pass's finding cites reasoning-core-strict/cfg_11 exceeding the one-call budget, which directly falsifies premise p1's claim of a strict one-call budget.; reversed: premise p1 of D-0002 reversed
- K-0003 nominated D-0002 at counterfactual-edit → The pass's finding cites evidence that the task environment allowed multiple shell calls without penalty, directly falsifying the premise that a strict one-call budget is enforced.; reversed: premise p1 of D-0002 reversed
- K-0003 nominated D-0002 at counterfactual-edit → The pass's finding cites a specific run (reasoning-core-strict/regex_10) where multiple shell calls were allowed without penalty, directly falsifying the premise's claim of a strict one-call budget.; reversed: premise p1 of D-0002 reversed
- K-0003 nominated D-0002 at counterfactual-edit → The pass's finding cites evidence that the task environment allowed multiple shell calls without penalty, directly falsifying premise p1's claim of a strict one-call budget.; reversed: premise p1 of D-0002 reversed
- pass 7 O-0017 [open]: In task reasoning-core-strict/cfg_07, the first attempt missed verifying library availability before importing, causing a ModuleNotFoundError that forced a second shell call to install nltk, which then exhausted the strict one-call budget.
- pass 7 O-0018 [open]: In reasoning-core-strict/regex_08, the pass used its single allowed shell call to check 'iQBUq', then attempted a second call for 'iQ' which was refused as a non-transient budget fault.
- pass 7 O-0019 [open]: In task reasoning-core-strict/cfg_00, the pass attempted to import NLTK for CFG parsing, which triggered a non-transient ModuleNotFoundError, missing the convention to verify library availability before importing.
- pass 7 O-0020 [open]: In task reasoning-core-strict/cfg_01, the first attempt missed the convention of a strict one-shell-call budget per task.
- pass 8 O-0021 [open]: In task reasoning-core-strict/cfg_04, the first attempt missed the convention of verifying library availability before importing, attempting to use `nltk` directly and failing with a `ModuleNotFoundError`.
- pass 8 O-0022 [open]: The first shell command in the reasoning-core-strict/cfg_10 task failed with a ModuleNotFoundError for nltk because the library was not pre-installed.

## Records

| record | admitted after pass | mentions | decision |
|---|---|---|---|
| D-0001 | 2 | — | Before importing a non-standard library, verify its availability; if unavailable, use a standard-library alternative or halt with a clear diagnostic. |
| D-0002 | 2 | — | Enforce a strict budget of one shell call per task; any attempt to make a second shell call must be refused as a non-transient fault. |
| D-0003 | 4 | — | Before importing a non-standard library, verify its availability; if unavailable, use a standard-library alternative or halt with a clear diagnostic. |
| D-0004 | 6 | — | Before importing a non-standard library, verify its availability; if unavailable, use a standard-library alternative or halt with a clear diagnostic. |
