#!/usr/bin/env bash
# The demonstration of § 14: six passes with the store attached, six detached, the same suite hash,
# consolidation every two passes, both runs recorded as Weave evaluations under one project.
#
#   HGI_WEAVE_PROJECT=hgi WANDB_ENTITY=<entity> ./demo.sh
#
# Every hgi command that writes ends in its own commit. Without HGI_WEAVE_PROJECT the run is untraced;
# without HGI_INFERENCE_BASE_URL the frozen model is the deterministic stub (see hgi/stub.py).
set -euo pipefail
PASSES="${PASSES:-6}"
EVERY=$(uv run python -c "from hgi.store import Store; print(Store().registry.bars['consolidation_every_passes'])")

for n in $(seq 1 "$PASSES"); do
  SESSION=$(uv run hgi boot --pass "$n" | sed -n 's/^== \(S-[0-9]*\) pass.*/\1/p')
  uv run hgi evaluate --session "$SESSION"
  uv run hgi close --session "$SESSION"
  if [ $((n % EVERY)) -eq 0 ]; then uv run hgi consolidate; fi
done

for n in $(seq 1 "$PASSES"); do
  uv run hgi evaluate --detached --pass "$n"
done

uv run hgi lint
if [ -n "${HGI_WEAVE_PROJECT:-}" ]; then uv run hgi mirror; fi
