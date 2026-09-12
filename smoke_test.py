"""Smoke test: confirm wandb + weave can authenticate and log to the backend."""

import math
import os
import random

import wandb
import weave

# Entity to log under. Defaults to a writable entity; override with WANDB_ENTITY.
ENTITY = os.environ.get("WANDB_ENTITY", "slavazinevich-worldvue")
PROJECT = os.environ.get("WANDB_PROJECT", "coreweave-smoke-test")


def run_wandb_smoke_test() -> str:
    """Log a handful of metrics to a short W&B run and return its URL."""
    run = wandb.init(
        entity=ENTITY,
        project=PROJECT,
        config={"lr": 0.01, "epochs": 5},
        settings=wandb.Settings(silent=False),
    )
    for epoch in range(5):
        wandb.log(
            {
                "epoch": epoch,
                "loss": math.exp(-epoch) + random.uniform(0, 0.05),
                "accuracy": 1 - math.exp(-epoch) - random.uniform(0, 0.05),
            }
        )
    url = run.url
    run.finish()
    return url


@weave.op()
def add_and_square(a: int, b: int) -> int:
    """A trivial traced op so Weave records at least one call."""
    return (a + b) ** 2


def run_weave_smoke_test() -> None:
    """Initialize Weave and invoke a traced op."""
    weave.init(f"{ENTITY}/{PROJECT}")
    result = add_and_square(3, 4)
    print(f"weave op result: add_and_square(3, 4) = {result}")


if __name__ == "__main__":
    print("=== W&B smoke test ===")
    wandb_url = run_wandb_smoke_test()
    print(f"W&B run logged: {wandb_url}")

    print("\n=== Weave smoke test ===")
    run_weave_smoke_test()

    print("\nSmoke test complete.")
