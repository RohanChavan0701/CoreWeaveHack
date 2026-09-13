# reasoning-core — evolution: first-sight produce-and-verify on unseen regexes and grammars as the store grows, a strong teacher over a mid-sized actor

6 batches × 4 tasks from reasoning-core, seed 0; every arm meets the same batches in the same order. A pass's score is first sight — nothing in the store was learned on that batch — so the curve is performance on unseen tasks as the store grows.

## First sight, per batch

Pass rate, then economy / turns / transfer per arm.

| batch | qwen-attached | qwen-detached | 20b-attached | qwen-strict | qwen-strict-detached | qwen-attached quality | qwen-detached quality | 20b-attached quality | qwen-strict quality | qwen-strict-detached quality | in context (attached) | consolidation after |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.75 | 0.75 | 0.75 | 0.75 | 1.00 | 0.40 / 0.47 / — | 0.25 / 0.37 / — | 0.50 / 0.58 / — | 0.33 / 0.46 / — | 0.58 / 0.71 / — | none |  |
| 2 | 1.00 | 1.00 | 0.50 | 1.00 | 1.00 | 0.33 / 0.47 / — | 0.25 / 0.40 / — | 0.38 / 0.29 / — | 0.71 / 0.79 / — | 0.67 / 0.75 / — | none | admitted D-0001 D-0002 |
| 3 | 1.00 | 1.00 | 1.00 | 0.75 | 0.75 | 0.58 / 0.85 / — | 0.52 / 0.64 / — | 0.71 / 0.65 / — | 0.46 / 0.54 / — | 0.38 / 0.46 / — | D-0001 D-0002 |  |
| 4 | 0.50 | 0.75 | 0.50 | 1.00 | 1.00 | 0.12 / 0.20 / — | 0.21 / 0.33 / — | 0.31 / 0.35 / — | 0.88 / 0.83 / — | 0.71 / 0.79 / — | D-0001 D-0002 | admitted D-0003 |
| 5 | 0.75 | 0.75 | 0.75 | 1.00 | 1.00 | 0.44 / 0.52 / — | 0.25 / 0.37 / — | 0.46 / 0.45 / — | 0.62 / 0.71 / — | 0.62 / 0.75 / — | D-0001 D-0002 D-0003 |  |
| 6 | 0.75 | 1.00 | 1.00 | 0.75 | 0.75 | 0.46 / 0.54 / — | 0.36 / 0.52 / — | 0.75 / 0.73 / — | 0.38 / 0.46 / — | 0.38 / 0.50 / — | D-0001 D-0002 D-0003 | admitted D-0004 D-0005 |

Over the stream: qwen-attached 0.79 (19/24), quality 0.39 / 0.51 / —; qwen-detached 0.88 (21/24), quality 0.31 / 0.44 / —; 20b-attached 0.75 (18/24), quality 0.52 / 0.51 / —; qwen-strict 0.88 (21/24), quality 0.56 / 0.63 / —; qwen-strict-detached 0.92 (22/24), quality 0.56 / 0.66 / —.

## First sight, per lesson

Pass rate per arm, then economy / turns / transfer per arm.

| lesson | tier | qwen-attached | qwen-detached | 20b-attached | qwen-strict | qwen-strict-detached | qwen-attached quality | qwen-detached quality | 20b-attached quality | qwen-strict quality | qwen-strict-detached quality | naive-shape before / after first mention (attached) | first mention |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| reasoning-core | — | 0.79 (19/24) | 0.88 (21/24) | 0.75 (18/24) | — | — | 0.39 / 0.51 / — | 0.31 / 0.44 / — | 0.52 / 0.51 / — | — | — | 0.00 (0/24) / — | — |
| reasoning-core-strict | — | — | — | — | 0.88 (21/24) | 0.92 (22/24) | — | — | — | 0.56 / 0.63 / — | 0.56 / 0.66 / — | — | — |

## Revisit

- qwen-attached: batch 1 scored 0.75 at first sight (pass 1) and 1.00 when met again at pass 7 with D-0003 D-0004 D-0005 in context.
- qwen-attached: batch 2 scored 1.00 at first sight (pass 2) and 0.50 when met again at pass 8 with D-0003 D-0004 D-0005 in context.
- 20b-attached: batch 1 scored 0.75 at first sight (pass 1) and 1.00 when met again at pass 7 with D-0002 in context.
- 20b-attached: batch 2 scored 0.50 at first sight (pass 2) and 0.50 when met again at pass 8 with D-0002 in context.
- qwen-strict: batch 1 scored 0.75 at first sight (pass 1) and 1.00 when met again at pass 7 with D-0002 D-0004 in context.
- qwen-strict: batch 2 scored 1.00 at first sight (pass 2) and 1.00 when met again at pass 8 with D-0002 D-0004 in context.

## Records admitted

- qwen-attached D-0001 (after pass 2; mentions no lesson): Before using a non-standard library in a shell call, verify its availability and install it if missing, reserving subsequent calls for the core task.
- qwen-attached D-0002 (after pass 2; mentions no lesson): When a task specifies a maximum number of tool calls, plan the work to fit within that budget, and stop issuing calls once the limit is reached.
- qwen-attached D-0003 (after pass 4; mentions no lesson): When a task imposes a strict limit on tool calls, plan the sequence of operations to complete the core work within that limit, reserving calls for essential steps and avoiding iterative or exploratory calls that risk exhaustion.
- qwen-attached D-0004 (after pass 6; mentions no lesson): Before executing code that imports a library, verify the library is available in the execution environment; if it is not, install it or use a standard-library alternative.
- qwen-attached D-0005 (after pass 6; mentions no lesson): When a task specifies a maximum number of tool calls, plan the work to fit within that budget, and before using a non-standard library in a shell call, verify its availability and install it if missing, reserving subsequent calls for the core task.
- 20b-attached D-0001 (after pass 4; mentions decoy-dependency): When a task fails because a required module is not installed, the first attempt should detect the missing dependency and either install it or skip the task, rather than retrying the same failing call.
- 20b-attached D-0002 (after pass 6; mentions decoy-dependency): When a task fails because a required runtime dependency is absent, the first attempt should detect the missing dependency and either install it or skip the task, rather than retrying the same failing call.
- qwen-strict D-0001 (after pass 2; mentions no lesson): Before importing a non-standard library, verify its availability; if unavailable, use a standard-library alternative or halt with a clear diagnostic.
- qwen-strict D-0002 (after pass 2; mentions no lesson): Enforce a strict budget of one shell call per task; any attempt to make a second shell call must be refused as a non-transient fault.
- qwen-strict D-0003 (after pass 4; mentions no lesson): Before importing a non-standard library, verify its availability; if unavailable, use a standard-library alternative or halt with a clear diagnostic.
- qwen-strict D-0004 (after pass 6; mentions no lesson): Before importing a non-standard library, verify its availability; if unavailable, use a standard-library alternative or halt with a clear diagnostic.

## Reading

A symptom is derived, not judged: `naive` means the row's result equals what the task's scripted first-contact policy returns (or its error is of the same class), so a naive-shape failure after a record for the lesson was in context is the same shape recurring with the memory attached. Quality grades a passed solution: `economy` is the knowing policy's calls over the calls spent (zero on a failed row), `turns` the same over model turns, `transfer` whether the last shell command replayed in the task's twin world gives the twin's answer — a pass that knows a convention spends less and its method carries, where one that discovers it spends the discovery and may not. `mentions` is a keyword heuristic over a record's text and is logged as one. Every count is from one run and is a floor.

