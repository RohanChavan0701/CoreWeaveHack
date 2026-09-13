# reasoning-core/20b-attached — evolution

attached on `openai/gpt-oss-20b`; 6 batches × 4 tasks from reasoning-core, seed 0; revisit [1, 2].

## Passes

| pass | batch | first sight | economy / turns / transfer | symptoms | in context | mentions | filed | consolidation after |
|---|---|---|---|---|---|---|---|---|
| 1 | 1 | 0.75 | 0.50 / 0.58 / — | error:turn-limit=1 pass=3 | none | — | 3 obs, 1 prop |  |
| 2 | 2 | 0.50 | 0.38 / 0.29 / — | error:turn-limit=2 pass=2 | none | — | 5 obs, 1 prop | K-0001: 4 groups, 1 at the bar; admitted nothing; 1 refused by the floor: 1 distinct session; dismissed 2 |
| 3 | 3 | 1.00 | 0.71 / 0.65 / — | pass=4 | none | — | 1 obs, 0 prop |  |
| 4 | 4 | 0.50 | 0.31 / 0.35 / — | error:turn-limit=2 pass=2 | none | — | 5 obs, 0 prop | K-0002: 3 groups, 2 at the bar; admitted D-0001; 1 admitted D-0001, 1 decline, 1 draft refused at parse: a hook-edit supersedes exactly one record; got []; dismissed 7 |
| 5 | 5 | 0.75 | 0.46 / 0.45 / — | error:turn-limit=1 pass=3 | D-0001 | decoy-dependency: D-0001 | 2 obs, 1 prop |  |
| 6 | 6 | 1.00 | 0.75 / 0.73 / — | pass=4 | D-0001 | decoy-dependency: D-0001 | 3 obs, 1 prop | K-0003: 3 groups, 1 at the bar; admitted D-0002; 1 admitted D-0002; the payload was promoted on the examiner's abstraction claim |
| 7 (revisit) | 1 | 1.00 | 0.71 / 0.61 / — | pass=4 | D-0002 | decoy-dependency: D-0002 | 2 obs, 1 prop |  |
| 8 (revisit) | 2 | 0.50 | 0.50 / 0.50 / — | error:turn-limit=2 pass=2 | D-0002 | decoy-dependency: D-0002 | 4 obs, 1 prop |  |

## Lessons

Each cell is the lesson's rows in that pass: ✓ passed, N the naive first-contact outcome (a same-shape failure), W another wrong answer, E a harness or tool error. `mentioned` marks passes with a record in context whose text uses the lesson's words.

| lesson | tier | p1 | p2 | p3 | p4 | p5 | p6 | p7r | p8r | first sight | economy / turns / transfer | naive before / after first mention | first mention | revisit |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| reasoning-core | — | ✓✓✓E | ✓✓EE | ✓✓✓✓ | E✓✓E | ✓✓✓E | ✓✓✓✓ | ✓✓✓✓ | ✓✓EE | 0.75 (18/24) | 0.52 / 0.51 / — | 0.00 (0/24) / — | — | batch 1: 4/4, batch 2: 2/4 |

## What the passes noticed

Each observation as the close filed it, with the shape the blind coder gave it at the next consolidation (`open` until one has run); a group reaches the bar when its observations come from as many distinct sessions as the bar asks.

- pass 1 O-0001 [other(missing valid derivation string)]: The task reasoning-core/cfg_02 failed to produce a CFG derivation string in the first attempt; the row did not produce a result, missing the convention of returning a valid derivation string.
- pass 1 O-0002 [other(missing nltk import)]: The first attempt failed due to missing nltk import in task reasoning-core/cfg_07
- pass 1 O-0003 [tool-budget]: The task reasoning-core/cfg_02 failed due to turn limit reached.
- pass 2 O-0004 [shell-tool]: The task reasoning-core/cfg_04 failed because the first shell call attempted to run Python but the environment lacked a python executable, violating the convention that shell calls must use a valid interpreter.
- pass 2 O-0005 [tool-budget]: Task reasoning-core/cfg_03 failed to produce a string because the grammar's recursive rule B -> S S was not applied, causing the parser to run out of turns.
- pass 2 O-0006 [other(missing nltk import)]: The first attempt failed due to missing nltk module, violating the Python import convention.
- pass 2 O-0007 [other(missing valid derivation string)]: Failed task reasoning-core/cfg_04
- pass 2 O-0008 [other(missing valid derivation string)]: Failed task reasoning-core/cfg_03
- K-0001 group [other(missing import)] ← O-0002 O-0006 from S-0001 S-0002 — at the bar
- K-0001 group [other(unspecified failure)] ← O-0007 O-0008 from S-0002 — below the bar
- K-0001 group [other(valid derivation string)] ← O-0001 from S-0001 — below the bar
- K-0001 group [shell-tool] ← O-0004 from S-0002 — below the bar
- K-0001 nominated missing-import at hook-edit → refused by the floor: 1 distinct session(s) in the evidence (S-0001) against the bar 2; the adjudicator's decline(insufficient independence) was overridden: a decline stands only on an upheld premise kill
- pass 3 O-0009 [shell-tool]: The first shell command failed because the 'python' interpreter was not found; the convention of using 'python3' was missed.
- pass 4 O-0010 [other(missing valid derivation string)]: The task reasoning-core/cfg_09 failed to produce a final answer within the turn limit, missing the convention of providing a derivation string.
- pass 4 O-0011 [other(missing valid derivation string)]: Task reasoning-core/cfg_01 failed to produce a final answer within 8 turns; the first attempt did not meet the convention of providing a string of at least 9 space-separated tokens derived from the grammar.
- pass 4 O-0012 [other(regex possessive quantifier unsupported)]: The first attempt for task reasoning-core/regex_09 failed due to an unsupported possessive quantifier in the regex pattern.
- pass 4 O-0013 [other(missing valid derivation string)]: The reasoning-core/cfg_09 task failed due to turn limit reached.
- pass 4 O-0014 [other(missing valid derivation string)]: The reasoning-core/cfg_01 task failed due to turn limit reached.
- K-0002 group [other(missing nltk import)] ← O-0002 O-0006 from S-0001 S-0002 — at the bar
- K-0002 group [other(missing valid interpreter)] ← O-0004 O-0009 from S-0002 S-0003 — at the bar
- K-0002 group [other(unsupported possessive quantifier in regex)] ← O-0012 from S-0004 — below the bar
- K-0002 nominated missing-import at new-decision → admitted D-0001
- K-0002 nominated missing-interpreter at hook-edit → draft refused at parse: a hook-edit supersedes exactly one record; got []
- K-0002 nominated work-shape/presentation at hook-edit → decline(tool-budget is already a registered term covering the shape; the coder found it, so the boundary stays open); the coder read the presentations as ['tool-budget']
- pass 5 O-0015 [other(task output length requirement)]: The task reasoning-core/cfg_06 failed to produce a final answer within the turn limit; the first attempt did not generate a string of at least 7 tokens, violating the task's requirement.
- pass 5 O-0016 [shell-tool]: The first attempt failed due to missing python binary, a non-transient fault.
- pass 6 O-0017 [shell-tool]: The task 'reasoning-core/cfg_11' failed on first attempt due to missing Python and NLTK modules.
- pass 6 O-0018 [shell-tool]: The task 'reasoning-core/cfg_11' succeeded on second attempt after installing missing dependencies.
- pass 6 O-0019 [shell-tool]: The first attempt failed due to missing 'nltk' module and missing pip, a non-transient fault that was corrected on retry.
- K-0003 group [other(regex possessive quantifier unsupported)] ← O-0012 from S-0004 — below the bar
- K-0003 group [other(task output length requirement)] ← O-0015 from S-0005 — below the bar
- K-0003 group [shell-tool] ← O-0004 O-0009 O-0016 O-0017 O-0018 O-0019 from S-0002 S-0003 S-0005 S-0006 — at the bar
- K-0003 nominated shell-interpreter at hook-edit → admitted D-0002; the payload was promoted on the examiner's abstraction claim
- pass 7 O-0020 [open]: In task reasoning-core/regex_10, the first attempt produced the string 'Mfutureimportantu', which does not match the regex because it misspells 'futureimportant'.
- pass 7 O-0021 [open]: The first attempt failed due to missing nltk module.
- pass 8 O-0022 [open]: The task 'reasoning-core/cfg_03' failed because the shell could not find the python interpreter; the missing‑dependency handling record D-0002 should have fired to address this.
- pass 8 O-0023 [open]: The task reasoning-core/cfg_04 failed because the first attempt did not invoke the shell tool to parse the grammar, missing the required runtime dependency; the record D-0002 should have fired to install or skip the task.
- pass 8 O-0024 [open]: Task reasoning-core/cfg_03 failed due to missing python interpreter.
- pass 8 O-0025 [open]: Task reasoning-core/cfg_04 failed due to turn limit reached.

## Records

| record | admitted after pass | mentions | decision |
|---|---|---|---|
| D-0001 | 4 | decoy-dependency | When a task fails because a required module is not installed, the first attempt should detect the missing dependency and either install it or skip the task, rather than retrying the same failing call. |
| D-0002 | 6 | decoy-dependency | When a task fails because a required runtime dependency is absent, the first attempt should detect the missing dependency and either install it or skip the task, rather than retrying the same failing call. |
