"""``hgi suite`` — the world the loop is judged on, as a command.

    hgi suite show   [--spec suites/x.toml]     # the resolved suite: families, counts, hash, faults; nothing touched
    hgi suite tasks  [--spec suites/x.toml]     # every task's id, shapes and budgets
    hgi suite fetch  <family> [--rows N]        # transcribe a dataset family into suite/data/<family>.jsonl

A suite spec is the ``[suite]`` table of an experiment file or a TOML file
of its own (``$HGI_SUITE`` for a hand-run). ``fetch`` runs a family's
transcriber once against the public dataset and pins the records into the
repository, so every run after that reads the file and the suite hash is
stable; re-fetching rewrites the file and changes the hash.
"""

from __future__ import annotations

import sys

import suite as _suite
from suite.families import FAMILIES
from suite.tasks import SuiteSpec, build, load_spec


def _suite_of(args):
    if getattr(args, "spec", None):
        return build(load_spec(args.spec))
    return _suite.current()


def show(world) -> str:
    lines = [world.describe(), f"families: " + "; ".join(f"{f.name} ← {f.source}" for f in FAMILIES.values() if f.name in world.families())]
    return "\n".join(lines)


def tasks(world) -> str:
    return "\n".join(f"{t.id}  [{', '.join(t.shapes)}]" + (f"  shell≤{t.shell_budget}" if t.shell_budget else "") + (f"  http≤{t.http_budget}" if t.http_budget else "")
                     for t in world.tasks)


def fetch(name: str, rows: int) -> str:
    if name not in FAMILIES:
        raise SystemExit(f"no task family {name!r}; families are {sorted(FAMILIES)}")
    fam = FAMILIES[name]
    if fam.fetch is None:
        raise SystemExit(f"family {name!r} is hand-written ({fam.source}); nothing to fetch")
    records = fam.fetch(rows)
    path = fam.pin(records)
    world = build(SuiteSpec(families=[name]))
    return f"pinned {len(records)} records to {path}; {world.describe()}"


def register(add, store_of, finish) -> None:
    p = add("suite", "the task suite: show it, list its tasks, or fetch a dataset family")
    p.add_argument("action", choices=["show", "tasks", "fetch"])
    p.add_argument("family", nargs="?", help="for `fetch`: the family to transcribe")
    p.add_argument("--spec", help="a suite TOML (default: $HGI_SUITE, else the genesis family)")
    p.add_argument("--rows", type=int, default=200, help="for `fetch`: at most this many records")
    p.set_defaults(fn=_cmd)


def _cmd(args) -> int:
    if args.action == "fetch":
        if not args.family:
            raise SystemExit("`fetch` names a family")
        print(fetch(args.family, args.rows), file=sys.stderr)
        return 0
    world = _suite_of(args)
    print(show(world) if args.action == "show" else tasks(world))
    return 0
