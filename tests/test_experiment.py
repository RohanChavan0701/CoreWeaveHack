"""The experiment surface: a file resolves to arms with every per-run decision fixed; an arm runs in
its own store with the cadence in its bars and its roles on their own backends; the report reads the
curves back from the stores."""

from __future__ import annotations

from pathlib import Path

import pytest

from hgi import experiment as _experiment
from hgi import model as _model
from hgi import registry as _registry
from hgi.store import Store, admitting_commit, git

EXPERIMENTS = Path(__file__).resolve().parents[1] / "experiments"


@pytest.fixture(autouse=True)
def clean_backends():
    _model.reset()
    yield
    _model.reset()


def test_the_smoke_file_resolves_its_arms_from_the_defaults():
    exp = _experiment.load(EXPERIMENTS / "smoke.toml")
    attached, detached = exp.resolve("attached"), exp.resolve("detached")
    assert (attached.mode, attached.passes, attached.passes_per_round) == ("attached", 2, 2)
    assert detached.mode == "detached" and detached.passes == 2
    assert set(exp.roster("attached").values()) == {"stub"}


def test_every_shipped_experiment_resolves():
    for path in EXPERIMENTS.glob("*.toml"):
        exp = _experiment.load(path)
        for arm in exp.arms:
            spec = exp.resolve(arm)
            assert spec.passes == spec.rounds * spec.passes_per_round
            assert exp.roster(arm)["pass"]


def test_roles_resolve_to_their_own_backends_and_the_seed_is_priced_for_the_pass(tmp_path):
    exp = _experiment.Experiment(name="roles", models={"judge": _experiment.ModelSpec(id="stub-judge", stub=True)},
                                 arms={"a": {"roles": {"adjudicator": "judge", "examiner": "judge"}}})
    spec = exp.resolve("a")
    roster = _experiment.install(exp, spec)
    assert roster["pass"] == "stub" and roster["adjudicator"] == "stub-judge" and roster["examiner"] == "stub-judge"
    assert _model.model_id("consolidator") == "stub"
    reg = _experiment.seed_arm(exp, "a", spec, tmp_path / "store", roster)
    assert {lens.priced_for.model_id for lens in reg.lenses("boot")} == {"stub"}
    assert reg.bars["consolidation_every_passes"] == 2


def test_an_unknown_model_or_role_is_refused():
    exp = _experiment.Experiment(name="bad", arms={"a": {"model": "nowhere"}, "b": {"roles": {"oracle": "stub"}}})
    with pytest.raises(SystemExit, match="no model 'nowhere'"):
        exp.resolve("a")
    with pytest.raises(SystemExit, match="unknown roles"):
        exp.resolve("b")


def test_bars_override_deep_merges_over_the_seed(tmp_path):
    exp = _experiment.Experiment(name="bars", arms={"a": {"passes_per_round": 3, "bars": {"retirement": {"window_passes": 4}}}})
    spec = exp.resolve("a")
    reg = _experiment.seed_arm(exp, "a", spec, tmp_path / "store", _experiment.install(exp, spec))
    assert reg.bars["consolidation_every_passes"] == 3
    assert reg.bars["retirement"] == {"applied_over_considered_below": 0.1, "window_passes": 4}


def test_an_arm_runs_in_its_own_store_and_the_report_reads_its_curve_back(tmp_path, monkeypatch):
    monkeypatch.delenv("HGI_WEAVE_PROJECT", raising=False)
    exp = _experiment.load(EXPERIMENTS / "smoke.toml")
    record = _experiment.run_arm(exp, "attached", tmp_path, commit=False)
    where = tmp_path / "smoke" / "attached"
    assert record["sessions"] == ["S-0001", "S-0002"] and sorted(record["curve"]) == [1, 2]
    assert (where / "store" / "consolidations" / "K-0001.json").exists(), "one round of two passes ends in a consolidation"
    assert (where / "arm.json").exists() and record["finished_at"]
    assert _registry.load(where / "store").bars["consolidation_every_passes"] == 2
    assert "HGI_STORE" not in __import__("os").environ, "the arm's store root does not leak into the process"

    detached = _experiment.run_arm(exp, "detached", tmp_path, commit=False)
    assert detached["sessions"] == ["S-0001", "S-0002"] and all(v == 0.5 for v in detached["curve"].values())

    table = _experiment.report(exp, tmp_path)
    assert "| attached | stub | attached | 1×2 |" in table and "| detached | stub | detached | 1×2 | 0.50 | 0.50 | nothing |" in table


def test_rerunning_an_arm_needs_force(tmp_path, monkeypatch):
    monkeypatch.delenv("HGI_WEAVE_PROJECT", raising=False)
    exp = _experiment.load(EXPERIMENTS / "smoke.toml")
    _experiment.run_arm(exp, "detached", tmp_path, commit=False)
    with pytest.raises(SystemExit, match="--force"):
        _experiment.run_arm(exp, "detached", tmp_path, commit=False)
    assert _experiment.run_arm(exp, "detached", tmp_path, commit=False, force=True)["finished_at"]


def test_the_arm_genesis_commit_anchors_the_constitution_articles(tmp_path):
    """The seed's articles are named as a range on the arm's genesis commit, so `hgi lineage C-0003`
    resolves an admitting commit inside an arm's store, as it does in the demonstration store."""
    exp = _experiment.Experiment(name="lineage", arms={"a": {}})
    spec = exp.resolve("a")
    roster = _experiment.install(exp, spec)
    where = tmp_path / "lineage" / "a"
    where.mkdir(parents=True)
    store_root = where / "store"
    reg = _experiment.seed_arm(exp, "a", spec, store_root, roster)
    token = _registry.use(reg)
    try:
        git("init", "-q", cwd=where)
        git("config", "user.email", "committer@example.invalid", cwd=where)
        git("config", "user.name", "the committer", cwd=where)
        store = Store(store_root, registry=reg)
        message = _experiment._genesis_message(exp, "a", spec, store, roster)
        assert "constitution C-0001..C-0007" in message
        _experiment._commit_arm(where, store, True, message)

        at = admitting_commit(store, "C-0003")
        assert at is not None and at["subject"] == message
        assert admitting_commit(store, "C-0007") == at
    finally:
        _registry.reset(token)


def test_show_names_every_arms_plan_without_touching_a_store(tmp_path, monkeypatch):
    monkeypatch.setenv("HGI_RUNS", str(tmp_path))
    exp = _experiment.load(EXPERIMENTS / "model-sweep.toml")
    out = _experiment.show(exp)
    assert "arm split-roles: attached, 3 rounds × 2 passes = 6 passes" in out
    assert "pass=openai/gpt-oss-20b" in out and "adjudicator=openai/gpt-oss-120b" in out
    assert not any(tmp_path.iterdir())


def test_wandb_inference_needs_an_entity_and_project(monkeypatch):
    monkeypatch.setenv("WANDB_API_KEY", "not-checked-here")
    monkeypatch.delenv("WANDB_ENTITY", raising=False)
    monkeypatch.setenv("HGI_WEAVE_PROJECT", "hgi")
    with pytest.raises(SystemExit, match="entity/project"):
        _experiment.ModelSpec(id="openai/gpt-oss-120b").backend()
    monkeypatch.setenv("WANDB_ENTITY", "someone")
    assert _experiment.ModelSpec(id="openai/gpt-oss-120b").backend().client.project == "someone/hgi"
