"""The experiment surface: a file resolves to arms with every per-run decision fixed; an arm runs in
its own store with the cadence in its bars and its roles on their own backends; the report reads the
curves back from the stores."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from hgi import evolution as _evolution
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


def test_the_text2sql_stream_deals_four_to_a_batch_over_the_whole_pool():
    """Item 51: a batch is four tasks, not two. The lax pool of ten graded and six held-out questions deals into four
    batches of four, every task exactly once; ten graded and six held-out do not split evenly, so three batches carry
    two of each group and the fourth carries the four graded questions the round-robin has left. The strict pool of ten
    graded questions deals into two batches of five — five, not four, so the ten divide evenly and the whole pool is dealt."""
    exp = _experiment.load(EXPERIMENTS / "text2sql.toml")

    def group(task_id: str) -> str:
        return "holdout" if "holdout" in task_id else ("strict" if "strict" in task_id else "graded")

    lax = {"120b-attached", "120b-detached", "20b-attached", "120b-seeded"}
    strict = {"120b-strict", "120b-strict-detached", "120b-strict-seeded"}
    for arm in lax:
        spec = exp.resolve(arm)
        assert (spec.stream.batch, spec.stream.batches) == (4, 4)
        batches = spec.batches()
        assert all(len(b.tasks) == 4 for b in batches)
        ids = [t.id for b in batches for t in b.tasks]
        assert len(ids) == len(set(ids)) == 16, "every one of the sixteen lax tasks is dealt exactly once"
        counts = [{g: sum(group(t.id) == g for t in b.tasks) for g in ("graded", "holdout")} for b in batches]
        assert sum(c["graded"] for c in counts) == 10 and sum(c["holdout"] for c in counts) == 6
        mixed = [c for c in counts if c["graded"] and c["holdout"]]
        assert len(mixed) == 3 and all(c == {"graded": 2, "holdout": 2} for c in mixed), "three batches carry two of each group"
        assert sorted(counts, key=lambda c: c["holdout"])[0] == {"graded": 4, "holdout": 0}, "the fourth batch is the leftover graded"
    for arm in strict:
        spec = exp.resolve(arm)
        assert (spec.stream.batch, spec.stream.batches) == (5, 2)
        batches = spec.batches()
        ids = [t.id for b in batches for t in b.tasks]
        assert all(len(b.tasks) == 5 for b in batches) and len(ids) == len(set(ids)) == 10
        assert all(group(t.id) == "strict" for b in batches for t in b.tasks)


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


def test_progress_writes_a_per_pass_health_block(tmp_path, monkeypatch):
    """Each pass writes a health block into arm.json from the store already on disk — no model call — so a failing
    arm is diagnosable while it runs: what retrieval reached, the tool/harness errors its rows carried, the failed
    rows against the observations filed from them, and the round's draft disposition."""
    monkeypatch.delenv("HGI_WEAVE_PROJECT", raising=False)
    exp = _experiment.load(EXPERIMENTS / "smoke.toml")
    record = _experiment.run_arm(exp, "attached", tmp_path, commit=False)

    health = record["health"]
    assert sorted(health) == [1, 2], "one block per evaluated pass, keyed by pass"
    on_disk = __import__("json").loads((tmp_path / "smoke" / "attached" / "arm.json").read_text())
    assert set(on_disk["health"]) == {"1", "2"}, "the block is durable on disk, tail-able as the arm runs"

    for n, h in health.items():
        assert set(h) == {"pass", "reach", "errors", "coverage", "consolidation"} and h["pass"] == n
        assert h["reach"]["in_context"] == len(h["reach"]["records"]) <= h["reach"]["considered"]
        assert h["errors"]["rows"] == 6 and h["errors"]["tool_error_rows"] <= h["errors"]["rows"]
        assert sum(h["errors"]["by_class"].values()) >= h["errors"]["tool_error_rows"]
        assert h["coverage"]["shaped"] <= h["coverage"]["observed"] <= h["coverage"]["failed"]

    assert health[1]["consolidation"] is None, "no round closes on the first pass of a two-pass round"
    k = health[2]["consolidation"]
    assert k["nominated"] == 2 and k["admitted"] == 2 and k["outcomes"] == {"admitted": 2}

    detached = _experiment.run_arm(exp, "detached", tmp_path, commit=False)
    assert all(h["consolidation"] is None for h in detached["health"].values()), "a detached arm consolidates nothing"
    assert all(h["reach"]["considered"] == 0 and h["coverage"]["observed"] == 0 for h in detached["health"].values()), \
        "no store, so no reach and no noticing — only the ablation's own error rate carries signal"
    assert all(h["errors"]["rows"] == 6 for h in detached["health"].values())


def test_in_context_records_counts_only_guard_passed_non_constitution_accepted():
    """Retrieval's reach mirrors the log's own computation: a record counts when its guard passed, it did not come
    via the constitution, and it is still an accepted decision the store holds. Empty is the silent failure."""
    considered = [
        SimpleNamespace(record="D-0001", guard_passed=True, via="index"),      # reached
        SimpleNamespace(record="D-0002", guard_passed=False, via="index"),     # guard failed
        SimpleNamespace(record="C-0001", guard_passed=True, via="constitution"),  # the constitution, always there
        SimpleNamespace(record="D-0003", guard_passed=True, via="lexical"),    # not an accepted decision
    ]
    session = SimpleNamespace(considered=considered)
    assert _evolution.in_context_records(session, {"D-0001", "D-0002"}) == ["D-0001"]
    assert _evolution.in_context_records(SimpleNamespace(considered=[]), {"D-0001"}) == []


def test_row_error_classes_reads_the_final_error_and_the_whole_trace():
    """The bad-call signal is the row's final error and every tool error in its trace: a row that recovered from a
    broken call and answered wrong still shows the call through ``tool_errors``, which its final symptom hides."""
    recovered = {"error": None, "tool_errors": [{"message": "model call failed after a malformed tool call"}]}
    assert _evolution._row_error_classes(recovered) == ["malformed-tool-call"]
    both = {"error": {"message": "HTTP 410 Gone"}, "tool_errors": [{"message": "call budget exhausted"}]}
    assert _evolution._row_error_classes(both) == ["budget", "http-410"]
    assert _evolution._row_error_classes({"error": None, "tool_errors": []}) == []


def test_consolidation_disposition_tells_nothing_drafted_from_nothing_admitted():
    """The round's draft disposition distinguishes the two flat curves: nothing nominated (nothing to learn) from
    everything nominated and nothing admitted (refused at the floor or declined — text2sql, economy)."""
    def nom(subject, outcome):
        return SimpleNamespace(subject=subject, outcome=outcome)

    everything_refused = SimpleNamespace(
        id="K-0002", admitted=[],
        nominations=[nom("u1", "refused by the floor: below the independence floor (N=1)"),
                     nom("u2", "declined; draft dropped"), nom("C-0003", "anchored")])
    d = _evolution._consolidation_disposition(everything_refused)
    assert d == {"id": "K-0002", "nominated": 2, "admitted": 0,
                 "outcomes": {"refused_floor": 1, "declined": 1}}, "the anchoring of a constitution article is not a draft"

    admitted = SimpleNamespace(id="K-0001", admitted=["D-0001"],
                               nominations=[nom("u1", "admitted D-0001; the payload was promoted")])
    assert _evolution._consolidation_disposition(admitted)["outcomes"] == {"admitted": 1}


def test_arm_json_records_the_tree_commit(tmp_path, monkeypatch):
    """The runner's own tree, not the arm's store repository — pinned at the arm's start so a log written
    under a later commit can be told apart from the tree that actually ran (item 35)."""
    monkeypatch.delenv("HGI_WEAVE_PROJECT", raising=False)
    exp = _experiment.load(EXPERIMENTS / "smoke.toml")
    record = _experiment.run_arm(exp, "attached", tmp_path, commit=False)
    assert record["commit"] == git("rev-parse", "HEAD")


def test_tree_commit_is_null_outside_a_checkout(tmp_path):
    assert _experiment._tree_commit(tmp_path) is None


def test_serial_detached_is_the_default_and_never_touches_a_thread_pool(tmp_path, monkeypatch):
    """The safe default (decision 36): a detached arm's passes are drawn one at a time, so several arms of
    an experiment can run together without multiplying anyone's concurrency past the endpoint's ceiling."""
    monkeypatch.delenv("HGI_WEAVE_PROJECT", raising=False)
    monkeypatch.setattr("concurrent.futures.ThreadPoolExecutor",
                         lambda *a, **k: (_ for _ in ()).throw(AssertionError("thread pool used under serial_detached")))
    exp = _experiment.load(EXPERIMENTS / "smoke.toml")
    assert exp.resolve("detached").serial_detached is True
    record = _experiment.run_arm(exp, "detached", tmp_path, commit=False)
    assert record["sessions"] == ["S-0001", "S-0002"]


def test_serial_detached_can_be_turned_off_for_the_old_concurrent_draw(tmp_path, monkeypatch):
    monkeypatch.delenv("HGI_WEAVE_PROJECT", raising=False)
    exp = _experiment.Experiment(name="concurrent-detached", defaults={"rounds": 1, "passes_per_round": 2},
                                  arms={"a": {"mode": "detached", "serial_detached": False}})
    assert exp.resolve("a").serial_detached is False
    record = _experiment.run_arm(exp, "a", tmp_path, commit=False)
    assert record["sessions"] == ["S-0001", "S-0002"]


def test_weave_is_rejoined_in_each_worker_thread_of_a_concurrent_detached_draw(tmp_path, monkeypatch):
    """Moot under the serial default (no worker threads); needed the moment ``serial_detached`` is turned
    off, since a worker thread starts with no project bound in its own context (item 34)."""
    monkeypatch.delenv("HGI_WEAVE_PROJECT", raising=False)
    calls = []
    monkeypatch.setattr(_experiment.tracing, "rejoin", lambda: calls.append(True))

    concurrent_exp = _experiment.Experiment(name="concurrent-detached", defaults={"rounds": 1, "passes_per_round": 2},
                                             arms={"a": {"mode": "detached", "serial_detached": False}})
    _experiment.run_arm(concurrent_exp, "a", tmp_path, commit=False)
    assert len(calls) == 2, "once per worker-thread draw"

    calls.clear()
    serial_exp = _experiment.load(EXPERIMENTS / "smoke.toml")
    _experiment.run_arm(serial_exp, "detached", tmp_path, commit=False)
    assert calls == [], "the serial draw runs in this thread, already joined by tracing.run"


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


def test_reasoning_effort_rides_every_call_to_the_model_that_declares_it(monkeypatch):
    """The knob is per model, not per call: a spec that sets it sends it on every completion, one that leaves it unset sends nothing."""
    monkeypatch.setenv("WANDB_API_KEY", "not-checked-here")
    monkeypatch.setenv("WANDB_ENTITY", "someone")
    monkeypatch.setenv("HGI_WEAVE_PROJECT", "hgi")

    def sent(**spec) -> dict:
        backend = _experiment.ModelSpec(**spec).backend()
        seen: dict = {}

        def create(**kwargs):
            seen.update(kwargs)
            message = SimpleNamespace(content="{}", tool_calls=None)
            return SimpleNamespace(choices=[SimpleNamespace(message=message)])

        backend.client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
        backend.chat([{"role": "user", "content": "hi"}], json_mode=True)
        return seen

    assert sent(id="openai/gpt-oss-20b", reasoning_effort="low")["reasoning_effort"] == "low"
    assert "reasoning_effort" not in sent(id="openai/gpt-oss-120b")
