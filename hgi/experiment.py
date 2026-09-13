"""Experiments: the per-run decisions, declared once and kept out of the run.

An experiment file (TOML) names the models it may use, the defaults every
arm inherits, and its arms. An arm is one run of the loop with every
decision fixed: which model serves which role, how many rounds, how many
passes a round holds (the consolidation cadence, written into the arm's
bars), whether the memory is attached or detached, which bars it overrides,
which suite it runs on (the task families, the sample size and the fault
profile — :class:`suite.tasks.SuiteSpec`), and how many tasks the oracle
evaluates at once. Nothing in the file is a secret: a model names the
environment variable that holds its key.

::

    name = "baseline"
    weave_project = "hgi-experiments"       # under $WANDB_ENTITY

    [models.gpt-oss-120b]
    id = "openai/gpt-oss-120b"              # base_url defaults to W&B Inference, the key to $WANDB_API_KEY

    [defaults]
    model = "gpt-oss-120b"
    rounds = 3
    passes_per_round = 2
    [defaults.suite]
    families = ["genesis", "conventions"]   # the task families; size samples each, seeded
    [defaults.suite.faults]
    http_fault_calls = 2                    # the world's fault profile, part of the suite hash

    [arms.attached]
    mode = "attached"
    [arms.detached]
    mode = "detached"
    [arms.strong-judge.roles]
    adjudicator = "gpt-oss-120b"            # any role not named runs on the arm's model

The runner gives each arm a fresh store under ``runs/<experiment>/<arm>/``,
in its own git repository so the write law (every write ends in a commit)
holds per arm and the code repository's history stays the code's. It seeds
the store priced for the arm's pass model, writes the cadence into the bars,
and drives the same commands ``demo.sh`` drives — ``boot``, ``evaluate``,
``close``, ``consolidate`` at each round's end, ``evaluate --detached`` for
a detached arm — through the command surface, so an arm is exactly what a
hand-run would be. ``arm.json`` beside the store records what the arm
resolved to and, at the end, its curve; the report reads every arm's curve
back from its store.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import tomllib
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

import suite as _suite
from hgi import model as _model
from hgi import registry as _registry
from hgi import tracing
from hgi.roles import ROLES
from suite.tasks import SuiteSpec, build

RUNS = Path("runs")
"""Where arms run: ``$HGI_RUNS`` or ``./runs``, one directory per experiment, one per arm."""

BACKWARD_ROLES = ("consolidator", "examiner", "adjudicator", "coder")


class ModelSpec(BaseModel):
    """One model behind one OpenAI-compatible endpoint. The alias is the key it is declared under."""

    id: str
    """The model id the endpoint serves — ``openai/gpt-oss-120b`` on W&B Inference."""
    base_url: str = _model.WANDB_INFERENCE
    api_key_env: str = "WANDB_API_KEY"
    """The environment variable holding the key. On W&B Inference an absent variable falls back to the netrc entry ``wandb login`` wrote."""
    temperature: float = 0.0
    project: str | None = None
    """The ``OpenAI-Project`` header; on W&B Inference, ``entity/project`` for usage attribution, defaulting to the Weave project."""
    stub: bool = False
    """The deterministic stub under this alias's ``id`` — for offline arms and for telling two stub roles apart."""

    model_config = ConfigDict(extra="forbid")

    def backend(self) -> _model.Backend:
        if self.stub:
            b = _model.Stub()
            b.model_id = self.id
            return b
        on_wandb = self.base_url.startswith(_model.WANDB_INFERENCE)
        key = os.environ.get(self.api_key_env) or (_model.wandb_api_key() if on_wandb else None)
        if not key:
            raise SystemExit(f"model {self.id!r}: ${self.api_key_env} is not set" + (" and wandb holds no key" if on_wandb else ""))
        project = self.project or (_wandb_project() if on_wandb else None)
        return _model.OpenAICompatible(self.base_url, key, self.id, temperature=self.temperature, project=project)


STUB = ModelSpec(id="stub", stub=True)


def _wandb_project() -> str:
    """W&B Inference answers 401 without an ``entity/project`` to attribute usage to: the Weave project under ``$WANDB_ENTITY``."""
    project = tracing.project_name()
    if not project or "/" not in project:
        raise SystemExit("W&B Inference needs an entity/project for usage attribution: set WANDB_ENTITY and a weave project "
                         "(the experiment's weave_project or $HGI_WEAVE_PROJECT), or `project` on the model")
    return project


class ArmSpec(BaseModel):
    """One run of the loop with every per-run decision fixed."""

    mode: Literal["attached", "detached"] = "attached"
    rounds: int = Field(default=3, ge=1)
    """Consolidation cycles. A detached arm has no consolidation; its rounds only size the run."""
    passes_per_round: int = Field(default=2, ge=1)
    """Passes between consolidations — written into the arm's bars as ``consolidation_every_passes``."""
    model: str = "stub"
    """The alias every role runs on unless ``roles`` says otherwise."""
    roles: dict[str, str] = Field(default_factory=dict)
    bars: dict[str, Any] = Field(default_factory=dict)
    """Overrides merged over the seed's bars, nested tables deep-merged (``[arms.x.bars.retirement] window_passes = 4``)."""
    suite: SuiteSpec = Field(default_factory=SuiteSpec)
    """The world: task families, sample size and seed, fault profile. Deep-merged like ``bars``."""
    concurrency: int = Field(default=4, ge=1)
    """Tasks the oracle evaluates at once — W&B Inference answers 429 past its concurrency limit."""
    description: str = ""

    model_config = ConfigDict(extra="forbid")

    @property
    def passes(self) -> int:
        return self.rounds * self.passes_per_round

    def alias_for(self, role: str) -> str:
        return self.roles.get(role, self.model)


class Experiment(BaseModel):
    name: str
    description: str = ""
    weave_project: str | None = None
    """The Weave project the arms trace into (under ``$WANDB_ENTITY``); absent, the environment's ``$HGI_WEAVE_PROJECT`` stands."""
    models: dict[str, ModelSpec] = Field(default_factory=dict)
    defaults: dict[str, Any] = Field(default_factory=dict)
    arms: dict[str, dict[str, Any]]
    path: Path | None = None

    model_config = ConfigDict(extra="forbid")

    def model_spec(self, alias: str) -> ModelSpec:
        if alias in self.models:
            return self.models[alias]
        if alias == "stub":
            return STUB
        raise SystemExit(f"experiment {self.name}: no model {alias!r} declared; models are {sorted(self.models) + ['stub']}")

    def resolve(self, arm: str) -> ArmSpec:
        """The arm with the experiment's defaults under it: scalars overridden, ``roles`` and ``bars`` merged."""
        if arm not in self.arms:
            raise SystemExit(f"experiment {self.name}: no arm {arm!r}; arms are {sorted(self.arms)}")
        merged = _merge(deepcopy(self.defaults), self.arms[arm])
        spec = ArmSpec(**merged)
        unknown = set(spec.roles) - set(ROLES)
        if unknown:
            raise SystemExit(f"arm {arm}: unknown roles {sorted(unknown)}; roles are {ROLES}")
        for alias in {spec.model, *spec.roles.values()}:
            self.model_spec(alias)
        return spec

    def roster(self, arm: str) -> dict[str, str]:
        """Role → model id, as the arm resolves it."""
        spec = self.resolve(arm)
        return {role: self.model_spec(spec.alias_for(role)).id for role in ROLES}


def _merge(base: dict[str, Any], over: dict[str, Any]) -> dict[str, Any]:
    for k, v in over.items():
        base[k] = _merge(base[k], v) if isinstance(v, dict) and isinstance(base.get(k), dict) else deepcopy(v)
    return base


def load(path: Path | str) -> Experiment:
    path = Path(path)
    with path.open("rb") as f:
        raw = tomllib.load(f)
    return Experiment(**raw, path=path)


def runs_root() -> Path:
    return Path(os.environ.get("HGI_RUNS", RUNS))


def arm_dir(exp: Experiment, arm: str, root: Path | None = None) -> Path:
    return (root or runs_root()) / exp.name / arm


# --- running an arm ------------------------------------------------------------------------

def install(exp: Experiment, spec: ArmSpec) -> dict[str, str]:
    """Install the arm's backends — one client per alias — and return the roster."""
    _model.reset()
    clients = {alias: exp.model_spec(alias).backend() for alias in {spec.model, *spec.roles.values()}}
    _model.use(clients[spec.model])
    for role, alias in spec.roles.items():
        _model.use(clients[alias], role=role)
    return _model.roster()


def seed_arm(exp: Experiment, arm: str, spec: ArmSpec, root: Path, roster: dict[str, str]):
    """A fresh store priced for the pass model, with the cadence and the arm's overrides written into its bars."""
    from hgi.genesis import seed

    reg = seed(root, model_id=roster["pass"])
    bars = _merge(_merge(dict(reg.bars), {"consolidation_every_passes": spec.passes_per_round}), spec.bars)
    _registry.write_json(root / "registry" / "bars.json", bars)
    return _registry.load(root)


def run_arm(exp: Experiment, arm: str, root: Path | None = None, *, commit: bool = True, force: bool = False) -> dict[str, Any]:
    """Run one arm to completion in its own store; return the ``arm.json`` record."""
    from hgi import cli
    from hgi.store import Store, git

    spec = exp.resolve(arm)
    where = arm_dir(exp, arm, root)
    if where.exists():
        if not force:
            raise SystemExit(f"{where} exists; pass --force to rerun the arm (its store is discarded)")
        shutil.rmtree(where)
    where.mkdir(parents=True)
    store_root = where / "store"
    if commit:
        git("init", "-q", cwd=where)

    if exp.weave_project:
        os.environ["HGI_WEAVE_PROJECT"] = exp.weave_project
    os.environ["WEAVE_PARALLELISM"] = str(spec.concurrency)
    roster = install(exp, spec)
    world = build(spec.suite)
    suite_token = _suite.use(world)
    reg = seed_arm(exp, arm, spec, store_root, roster)
    token = _registry.use(reg)
    store = Store(store_root, registry=reg)
    record: dict[str, Any] = {
        "experiment": exp.name, "arm": arm, "spec": spec.model_dump(), "passes": spec.passes, "roster": roster,
        "suite": {"hash": world.hash, "tasks": len(world.tasks), "families": world.families()},
        "weave_project": tracing.project_name(), "started_at": _now(), "finished_at": None, "sessions": [], "curve": {},
    }
    _write(where / "arm.json", record)
    previous_store = os.environ.get("HGI_STORE")
    os.environ["HGI_STORE"] = str(store_root)
    tracing.run(exp.name, arm)
    argv = ["--store", str(store_root)] + ([] if commit else ["--no-commit"])

    def hgi(*args: str) -> None:
        if cli.main([args[0], *argv, *args[1:]]) != 0:
            raise SystemExit(f"hgi {args[0]} failed in arm {arm}")

    try:
        _commit_arm(where, store, commit, f"Genesis for {exp.name}/{arm}: priced for {roster['pass']}, {spec.rounds} rounds of {spec.passes_per_round}")
        for n in range(1, spec.passes + 1):
            if spec.mode == "attached":
                session = store.mint("session")
                hgi("boot", "--session", session, "--pass", str(n))
                hgi("evaluate", "--session", session)
                hgi("close", "--session", session)
                if n % spec.passes_per_round == 0:
                    hgi("consolidate")
            else:
                hgi("evaluate", "--detached", "--pass", str(n))  # the detached command mints its own session
            record["sessions"] = [s.id for s in _sessions(store, spec.mode)]
            record["curve"] = curve(store, spec.mode)
            _write(where / "arm.json", record)
        hgi("lint", "--model", roster["pass"])
    finally:
        record["finished_at"] = _now()
        _write(where / "arm.json", record)
        _commit_arm(where, store, commit, f"Arm {exp.name}/{arm} finished: {_curve_line(record['curve'])}")
        tracing.run()
        _registry.reset(token)
        _suite.reset(suite_token)
        _model.reset()
        if previous_store is None:
            os.environ.pop("HGI_STORE", None)
        else:
            os.environ["HGI_STORE"] = previous_store
    return record


def _commit_arm(where: Path, store, commit: bool, message: str) -> None:
    from hgi.store import git

    if not commit:
        return
    git("add", "-A", ".", cwd=where)
    if git("status", "--porcelain", cwd=where):
        git("commit", "-q", "-m", message, cwd=where)


def _sessions(store, mode: str):
    attached = mode == "attached"
    return sorted((s for s in store.all("session") if s.attached == attached and s.evaluation is not None), key=lambda s: s.pass_)


def curve(store, mode: str, scorer: str = "task_pass_rate") -> dict[int, float | None]:
    """Pass → the scorer's value over the arm's sessions of ``mode``; ``None`` where unevaluable."""
    return {s.pass_: (s.evaluation.scores[scorer].value if scorer in s.evaluation.scores else None) for s in _sessions(store, mode)}


def _curve_line(c: dict[Any, float | None]) -> str:
    return " ".join("—" if v is None else f"{v:.2f}" for _, v in sorted(c.items(), key=lambda kv: int(kv[0]))) or "no passes"


def _write(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# --- reading arms back ----------------------------------------------------------------------

def report(exp: Experiment, root: Path | None = None) -> str:
    """Every arm's curve, read back from its store; an arm that has not run reads as such."""
    from hgi.store import Store

    rows = []
    width = 0
    for arm in exp.arms:
        spec = exp.resolve(arm)
        where = arm_dir(exp, arm, root)
        roster = exp.roster(arm)
        label = roster["pass"] + ("" if all(m == roster["pass"] for m in roster.values()) else " +" + "/".join(
            sorted({m for r, m in roster.items() if m != roster["pass"]})))
        if not (where / "store" / "registry").exists():
            rows.append((arm, label, spec, {}, [], "not run"))
            continue
        reg = _registry.load(where / "store")
        token = _registry.use(reg)
        try:
            store = Store(where / "store", registry=reg)
            c = curve(store, spec.mode)
            admitted = [d for k in store.all("consolidation") for d in k.admitted]  # type: ignore[attr-defined]
        finally:
            _registry.reset(token)
        width = max(width, spec.passes)
        rows.append((arm, label, spec, c, admitted, None))
    head = ["arm", "model", "mode", "rounds×size"] + [f"p{n}" for n in range(1, width + 1)] + ["admitted"]
    lines = [f"# {exp.name}" + (f" — {exp.description}" if exp.description else ""), "", "| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for arm, label, spec, c, admitted, note in rows:
        cells = [arm, label, spec.mode, f"{spec.rounds}×{spec.passes_per_round}"]
        cells += [("—" if c.get(n) is None else f"{c[n]:.2f}") if n <= spec.passes else "" for n in range(1, width + 1)]
        cells.append(note or (" ".join(admitted) or "nothing"))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def show(exp: Experiment) -> str:
    """The resolved plan of every arm — no store touched, no call made."""
    lines = [f"experiment {exp.name}" + (f": {exp.description}" if exp.description else ""),
             f"weave project: {exp.weave_project or '(environment)'}", f"runs under: {runs_root() / exp.name}", ""]
    for arm in exp.arms:
        spec = exp.resolve(arm)
        roster = exp.roster(arm)
        lines.append(f"arm {arm}: {spec.mode}, {spec.rounds} rounds × {spec.passes_per_round} passes = {spec.passes} passes, concurrency {spec.concurrency}")
        if spec.description:
            lines.append(f"  {spec.description}")
        lines.append("  roles: " + ", ".join(f"{r}={m}" for r, m in roster.items()))
        lines.append("  " + build(spec.suite).describe())
        if spec.bars:
            lines.append(f"  bars: {json.dumps(spec.bars, sort_keys=True)}")
    return "\n".join(lines)


def list_models(base_url: str, api_key_env: str = "WANDB_API_KEY") -> list[str]:
    """The model ids the endpoint serves right now — the check an experiment file's ids are made against."""
    from openai import OpenAI

    on_wandb = base_url.startswith(_model.WANDB_INFERENCE)
    key = os.environ.get(api_key_env) or (_model.wandb_api_key() if on_wandb else None)
    if not key:
        raise SystemExit(f"${api_key_env} is not set")
    client = OpenAI(base_url=base_url, api_key=key, project=_wandb_project() if on_wandb else None)
    return sorted(m.id for m in client.models.list())


# --- the command ------------------------------------------------------------------------------

def register(add, store_of, finish) -> None:
    p = add("experiment", "run, show or report an experiment file's arms")
    p.add_argument("action", choices=["run", "show", "report", "models"])
    p.add_argument("file", nargs="?", help="the experiment TOML (not needed for `models`)")
    p.add_argument("--arm", action="append", help="run only this arm (repeatable); default every arm in file order")
    p.add_argument("--force", action="store_true", help="rerun an arm that has run, discarding its store")
    p.add_argument("--base-url", default=_model.WANDB_INFERENCE, help="for `models`: the endpoint to list")
    p.add_argument("--api-key-env", default="WANDB_API_KEY", help="for `models`: the variable holding the key")
    p.set_defaults(fn=_cmd)


def _cmd(args) -> int:
    if args.action == "models":
        print("\n".join(list_models(args.base_url, args.api_key_env)))
        return 0
    if not args.file:
        raise SystemExit("an experiment file is required")
    exp = load(args.file)
    if args.action == "show":
        print(show(exp))
        return 0
    if args.action == "report":
        print(report(exp))
        return 0
    for arm in args.arm or list(exp.arms):
        print(f"== {exp.name}/{arm} ==", file=sys.stderr)
        record = run_arm(exp, arm, commit=not args.no_commit, force=args.force)
        print(f"{exp.name}/{arm}: {_curve_line(record['curve'])}", file=sys.stderr)
    print(report(exp))
    return 0
