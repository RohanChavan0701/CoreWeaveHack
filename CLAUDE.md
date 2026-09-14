# HGI — working notes for agents

The **H**uman-**G**uided-**I**mprovement loop: an agent runs a task suite, and a
backward pass distills recurring failures into a store of decisions the next run
consults. This file records the environment and conventions every agent here
needs, so they aren't re-derived each session.

## Layout

- `hgi/` — the loop: the `hgi` CLI, the roles (`hgi/roles/*.md`), the store, the
  backward pass (`consolidate.py`, `drafting.py`), projections (`index.py`,
  `evolution.py`), the experiment runner (`experiment.py`).
- `suite/` — the world: task families (`suite/families/*.py`), the task/tool
  layer (`tasks.py`, `tools.py`), scorers, the stream (`stream.py`).
- `experiments/` — experiment TOMLs, `seeds/` (hand-authored seed stores),
  `results/` (committed run outputs).
- `tests/` — `pytest`.

## Environment — read this before running anything

- **The venv is uv-managed at `.venv`.** `hgi` is **not** on PATH and the system
  `python3` lacks the deps. Always use `.venv/bin/python` and `.venv/bin/hgi`.
- **No `pip` in the venv** — install with `uv pip install <pkg>` (does not touch
  `pyproject.toml`/`uv.lock`).
- **Tests:** `.venv/bin/python -m pytest` (add paths to scope; the full suite is
  the bar). Don't weaken an existing test to make it pass.

## Running the loop / experiments

- Loop commands: `hgi {genesis,boot,evaluate,close,consolidate,lint,index,price,
  lineage,experiment,suite,roles,consult,seed}`. `--store` / `$HGI_STORE` names
  the store root; `--no-commit` leaves the tree for you to commit.
- One experiment arm: `.venv/bin/hgi experiment run experiments/<x>.toml --arm
  <arm> --no-commit`. Omit `--arm` to run every arm. `$HGI_RUNS` = the runs
  directory — point it at a scratch dir for pilots so you don't pollute `runs/`.
- Verify a role prompt on a model without a full run:
  `.venv/bin/hgi roles try <request> --store <arm store>` (copies the store,
  sends the real request, shows how the reply parsed). Role prompts declare a
  `priced_for:` frontmatter line; `hgi lint` warns (does not fail) when a role
  runs on a model not listed there.

## Real-model endpoint (W&B Inference)

- Backend defaults to W&B Inference. The API key comes from `~/.netrc`
  (`machine api.wandb.ai`) or `$WANDB_API_KEY`.
- **You must set `WANDB_ENTITY` (this repo uses `slavazinevich-worldvue`) and a
  weave project** (the TOML's `weave_project`, or `$HGI_WEAVE_PROJECT=hgi-experiments`)
  or W&B returns **401** — this is the most common "why won't it run".
- Model ids are W&B Inference ids: `openai/gpt-oss-120b`, `openai/gpt-oss-20b`,
  `Qwen/Qwen3.6-35B-A3B`, `deepseek-ai/DeepSeek-V4-Pro`. `hgi experiment models`
  lists what's live today.
- **Concurrency ceiling ≈ 12–30 concurrent requests before 429s.** A single
  detached arm already fans out internally. Run multiple arms **sequentially**
  (chain with `&&`), never concurrently, or you lose rows to rate limits.

## reasoning-core specifics

- Generating/re-pinning its instances needs the generator stack (only for
  `fetch`, not to run a pinned experiment):
  `uv pip install 'reasoning_core==0.5.0' gramforge greenery faker nltk exrex`.
- The **shell tool the model drives** must be able to `import nltk` and `regex`
  (grammar verification runs there). `run_arm` preflights this; `.venv` on PATH
  provides it. If the shell's `python3` is the system one, every cfg row fails on
  a missing import — the classic confounded run.

## Working conventions

- **Git: agents share one working tree.** Stage only your own files by explicit
  path (`git add <path> ...`); **never `git add -A` / `git add .`** — it sweeps a
  concurrent agent's changes into your commit. Commit locally; don't push or open
  a PR unless asked. One commit per logical step; branch off `main` for PRs.
- **Docs are standing, present-tense descriptions of what *is*.** READMEs,
  docstrings, and seed schema cards describe the current state, not "changed from
  X". Temporal notes — what a run showed, what's left, why a choice was made —
  go in `carry-forward.md` (its "Leftover work" to-do list and decision log),
  not into the durable docs.
- Derive, don't duplicate: reuse existing helpers and registries rather than
  copying vocab lists or logic.
