"""Seed stores: hand-authored decisions injected into a fresh arm store before its first pass.

A seed under ``experiments/seeds/<world>/`` is what a mature store for that
world would hold — one decision per convention the world turns on, keyed on
registered work-shape terms so the boot's consultation reaches it. Injecting
it into an arm and running that arm beside the same arm from an empty store
is the compare/contrast: what the loop would buy if it had already learned
the world (``experiments/seeds/AUTHORING.md`` is the authoring rule).

The injector copies the seed's decisions into the store with ids minted past
the store's own, prices them for the arm's pass model, registers any
work-shape terms the seed's ``vocabulary.json`` declares, regenerates the
projections and runs the write-seam lint, refusing a seed that does not pass
it. Every injected record keeps ``admission.proposed_by = "seed"`` so the
analyst mirror and the evolution log can tell an injected decision from one
the loop admitted.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from hgi import index as _index
from hgi import lint as _lint
from hgi import registry as _registry
from hgi.registry import read_json, write_json
from hgi.store import Store

SEEDS_ROOT = Path("experiments") / "seeds"


def resolve(seed: str, experiment_path: Path | None = None) -> Path:
    """The seed directory for an arm's ``seed`` field: a path as given, else relative to the experiment file, else a world name under ``experiments/seeds``."""
    candidates = [Path(seed)]
    if experiment_path is not None:
        candidates += [experiment_path.parent / seed, experiment_path.parent / "seeds" / seed]
    candidates.append(SEEDS_ROOT / seed)
    for c in candidates:
        if (c / "decisions").is_dir():
            return c
    raise SystemExit(f"seed {seed!r}: no directory with a decisions/ folder among {', '.join(str(c) for c in candidates)}")


def decisions_of(seed_dir: Path) -> list[dict[str, Any]]:
    return [read_json(p) for p in sorted((seed_dir / "decisions").glob("D-*.json"))]


def inject(store_root: Path, seed_dir: Path, *, model_id: str | None, now: datetime | None = None) -> dict[str, Any]:
    """Copy a seed's decisions into ``store_root``; return the manifest written beside them as ``seed.json``."""
    reg = _registry.load(store_root)
    seed_dir = Path(seed_dir)
    now = now or datetime.now(timezone.utc).astimezone()
    since = now.date().isoformat()

    vocab_path = seed_dir / "vocabulary.json"
    added_terms: list[str] = []
    if vocab_path.exists():
        for vocab, terms in read_json(vocab_path).items():
            for term, means in terms.items():
                if term not in reg.terms(vocab):
                    reg.add_term(vocab, term, means, since)
                    added_terms.append(f"{vocab}:{term}")

    renamed: dict[str, str] = {}
    records = decisions_of(seed_dir)
    for raw in records:
        renamed[raw["id"]] = reg.mint("D")
    injected: list[dict[str, str]] = []
    for raw in records:
        text = json.dumps(raw)
        for old, new in renamed.items():  # cross-references between seed decisions follow the renumbering
            text = text.replace(f'"{old}"', f'"{new}"')
        rec = json.loads(text)
        rec["priced_for"] = {**rec.get("priced_for", {}), "model_id": model_id, "authored_for": rec.get("priced_for", {}).get("authored_for")}
        rec.setdefault("admission", {})["proposed_by"] = "seed"
        rec["admission"]["committed_at"] = now.isoformat()
        write_json(store_root / "decisions" / f"{rec['id']}.json", rec)
        injected.append({"id": rec["id"], "seed_id": raw["id"], "decision": rec.get("decision", "")})

    token = _registry.use(reg)
    try:
        store = Store(store_root, registry=reg)
        report = _lint.run(store, seams=("write",), model_id=model_id)  # the floor first: a record refused at parse never reaches a projection
        failures = [f for f in report.findings if f.level == "fail"]
        if failures:
            lines = "\n".join(f"  {f.check} {f.record}: {f.message}" for f in failures)
            raise SystemExit(f"seed {seed_dir}: injected store fails the write-seam lint:\n{lines}")
        _index.regenerate(store)
    finally:
        _registry.reset(token)
    manifest = {"seed": str(seed_dir), "injected": injected, "terms_added": added_terms, "at": now.isoformat(),
                "warnings": [f"{f.check} {f.record}: {f.message}" for f in report.findings if f.level != "fail"]}
    write_json(store_root / "seed.json", manifest)
    return manifest


def register(add, store_of, finish) -> None:
    p = add("seed", "inject a hand-authored seed store's decisions into the store (experiments/seeds/<world>)")
    p.add_argument("seed", help="a seed directory, or a world name under experiments/seeds")
    p.add_argument("--model", default=None, help="the model id to price the injected decisions for")
    p.set_defaults(fn=lambda args: _cmd(args, store_of))


def _cmd(args, store_of) -> int:
    store = store_of(args)
    manifest = inject(store.root, resolve(args.seed), model_id=args.model)
    print(f"injected {len(manifest['injected'])} decision(s) from {manifest['seed']} into {store.root}")
    for r in manifest["injected"]:
        print(f"  {r['id']} (seed {r['seed_id']}): {r['decision'][:100]}")
    for w in manifest["warnings"]:
        print(f"  warning: {w}")
    return 0
