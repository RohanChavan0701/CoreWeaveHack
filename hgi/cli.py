"""``hgi`` — the command surface.

    hgi genesis                                  # seed a store
    hgi boot        --session S-nnnn --pass n    # assemble; print the consultation plan
    hgi evaluate    --session S-nnnn             # run the oracle; write facts; emit fires; settle
    hgi close       --session S-nnnn             # dispositions, observations, steers, proposals, session record
    hgi consolidate                              # the backward pass over the ledgers
    hgi lint                                     # the floor
    hgi index                                    # regenerate projections
    hgi lineage     D-0007                       # the path query over the DAG
    hgi experiment  run experiments/x.toml       # every arm of an experiment file, each in its own store
    hgi suite       show                         # the task suite in scope: families, counts, hash, faults
    hgi roles       try nominate --store <arm>   # one role request against a copy of a store; how the reply parsed

Every command that writes ends in a commit whose message names the record
ids it admitted, flipped or retired. ``--store`` (or ``$HGI_STORE``) names
the store root; ``--no-commit`` leaves the tree for the caller to commit.

Every surface the environment configures — the inference endpoint
(``$HGI_INFERENCE_BASE_URL``, ``$HGI_INFERENCE_API_KEY``, ``$HGI_MODEL_ID``),
the trace store (``$HGI_WEAVE_PROJECT``, ``$WANDB_ENTITY``), the coder
(``$TYPESAFE_*``) and the store root — is read from the process environment.
:func:`load_env` fills it from an env file first, so that configuring a run
is editing ``.env`` and not exporting by hand; an endpoint that goes
unconfigured is not an error but a silent fall back to the deterministic
stub (:mod:`hgi.model`), so the file is read before any command runs.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from hgi import index as _index
from hgi import lint as _lint
from hgi import registry as _registry
from hgi.store import Store, commit


ENV_FILE = ".env"


def load_env(path: Path | None = None) -> dict[str, str]:
    """Fill the process environment from an env file; return what it set.

    The file is ``$HGI_ENV_FILE`` or ``./.env``, and an absent one is the
    normal case, not an error. The format is the one ``.env.example`` is
    written in: ``KEY=value`` a line, an optional ``export`` prefix, a
    comment or a blank line ignored, and a value's surrounding quotes
    stripped. A value is the rest of its line — a trailing ``#`` is part of
    it, so a comment belongs on a line of its own. A blank value reads as
    unset and is not exported, which is what ``.env.example`` means by
    leaving a variable empty: the surface stays off and the default behind
    it — the stub model, an untraced run — stands. The process environment
    wins: a variable already set is never overwritten, so a flag exported
    for one run outranks the file, and the loader is idempotent.
    """
    path = path or Path(os.environ.get("HGI_ENV_FILE", ENV_FILE))
    if not path.is_file():
        return {}
    loaded = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.removeprefix("export ").partition("=")
        key, value = key.strip(), value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        if key and value and key not in os.environ:
            os.environ[key] = value
            loaded[key] = value
    return loaded


def _store(args) -> Store:
    root = Path(args.store) if args.store else _registry.default_root()
    return Store(root)


def _finish(store: Store, args, message: str) -> None:
    """Regenerate projections and commit, so every write ends in a coherent tree."""
    _index.regenerate(store)
    if getattr(args, "no_commit", False):
        return
    sha = commit(store, message)
    if sha:
        print(f"committed {sha}: {message.splitlines()[0]}")


def cmd_genesis(args) -> int:
    from hgi.genesis import seed

    root = Path(args.store) if args.store else _registry.default_root()
    if any(root.glob("registry/*.json")) and not args.force:
        print(f"{root} already holds a registry; pass --force to reseed", file=sys.stderr)
        return 1
    seed(root, model_id=os.environ.get("HGI_MODEL_ID"))
    store = Store(root)
    _finish(store, args, "Genesis: seed the registry and the constitution C-0001..C-0007")
    print(f"seeded {root}")
    return 0


def cmd_lint(args) -> int:
    store = _store(args)
    report = _lint.run(store, model_id=args.model)
    print(report)
    return 0 if report.green else 1


def cmd_index(args) -> int:
    store = _store(args)
    stale = _index.check(store)
    _index.regenerate(store)
    print(f"regenerated {len(_index.PROJECTIONS)} projections" + (f"; {len(stale)} were stale: {', '.join(stale)}" if stale else "; all were current"))
    if not args.no_commit:
        sha = commit(store, "Regenerate projections")
        if sha:
            print(f"committed {sha}")
    return 0


def cmd_lineage(args) -> int:
    store = _store(args)
    paths = _index.paths_to(store, args.id)
    for p in paths:
        print(" -> ".join(p))
    return 0


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--store", help="the store root (default: $HGI_STORE or ./store)")
    common.add_argument("--no-commit", action="store_true", help="write without committing")
    parser = argparse.ArgumentParser(prog="hgi", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter, parents=[common])
    sub = parser.add_subparsers(dest="command", required=True)

    def add(name, help):
        return sub.add_parser(name, help=help, parents=[common])

    p = add("genesis", "seed a store")
    p.add_argument("--force", action="store_true")
    p.set_defaults(fn=cmd_genesis)

    p = add("lint", "the floor")
    p.add_argument("--model", help="the session's model id, for the model-pricing check")
    p.set_defaults(fn=cmd_lint)

    p = add("index", "regenerate projections")
    p.set_defaults(fn=cmd_index)

    p = add("lineage", "the path query over the DAG")
    p.add_argument("id")
    p.set_defaults(fn=cmd_lineage)

    _register_pass_commands(add)
    return parser


def _register_pass_commands(add) -> None:
    """The forward- and backward-pass commands register themselves as their modules land."""
    try:
        from hgi import boot, close, consolidate, contract, evaluate, experiment, mirror, world  # noqa: F401
    except ImportError:
        return
    for module in (boot, evaluate, close, consolidate, mirror, experiment, world, contract):
        module.register(add, _store, _finish)


def main(argv: list[str] | None = None) -> int:
    load_env()
    args = build_parser().parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
