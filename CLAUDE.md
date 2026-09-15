# HGI — working notes for agents

The **H**uman-**G**uided-**I**mprovement loop: an agent runs a task suite, and a
backward pass distills recurring failures into a store of decisions the next run
consults. This file is the always-loaded constitution — layout and conventions.
Operational procedure lives in skills (see the end).

## Layout

- `hgi/` — the loop: the `hgi` CLI, the roles (`hgi/roles/*.md`), the store, the
  backward pass (`consolidate.py`, `drafting.py`), projections (`index.py`,
  `evolution.py`), the experiment runner (`experiment.py`).
- `suite/` — the world: task families (`suite/families/*.py`), the task/tool
  layer (`tasks.py`, `tools.py`), scorers, the stream (`stream.py`).
- `experiments/` — experiment TOMLs, `seeds/` (hand-authored seed stores),
  `results/` (committed run outputs).
- `tests/` — `pytest`.

## Environment

- **The venv is uv-managed at `.venv`.** `hgi` is **not** on PATH and the system
  `python3` lacks the deps. Use `uv run <cmd>` or `.venv/bin/python`;
  `.venv/bin/hgi` for the CLI.
- **No `pip` in the venv** — install with `uv pip install <pkg>` (does not touch
  `pyproject.toml`/`uv.lock`).
- **Tests:** `.venv/bin/python -m pytest` (or `uv run pytest`). The full suite is
  the bar; don't weaken a test to make it pass.

## Conventions

- **Git: agents share one working tree.** Stage only your own files by explicit
  path (`git add <path> ...`); **never `git add -A` / `git add .`** — it sweeps a
  concurrent agent's changes into your commit. Commit locally; don't push or open
  a PR unless asked. One commit per logical step; branch off `main` for PRs.
- **Docs are standing, present-tense descriptions of what *is*.** READMEs,
  docstrings, and seed schema cards describe the current state, not "changed from
  X". Temporal notes stay out of the durable docs, split by kind: what's left to
  do and where the build stands go in `carry-forward.md` (its "Leftover work"
  to-do list); the decisions made and why each may be right or wrong go in
  `decision-log.md` (the decision log). `carry-forward.md` stays future-facing —
  a decision, once taken, moves to the log rather than bloating the to-do surface.
- Derive, don't duplicate: reuse existing helpers and registries rather than
  copying vocab lists or logic.

## Skills

- **experiment-runner** — running/piloting/calibrating experiments on the real
  endpoint: the W&B `WANDB_ENTITY`/weave-project 401 trap, the 429 concurrency
  ceiling (arms run sequentially), scratch runs, `hgi roles try`, the
  reasoning-core generator stack, reading a run back. Load it before launching
  any arm or pilot.
- **consult-decisions** — read an HGI decision store from outside the loop
  before doing work it may already have settled.
