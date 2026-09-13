"""The incidents family: nine bundles, each a budgeted walk whose decoy readings are the convention."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import suite as _suite
from hgi import experiment as _experiment
from suite.faults import FaultProfile
from suite.families import FAMILIES
from suite.lessons import LESSONS, naive_outcome
from suite.stream import StreamSpec, lessons_of, partition
from suite.tasks import SuiteSpec, build

INCIDENT_TASKS = 9
EXPERIMENTS = Path(__file__).resolve().parents[1] / "experiments"


@pytest.fixture
def world():
    return build(SuiteSpec(families=["incidents"]))


def test_the_family_loads_nine_tasks_and_is_pinned_stable(world):
    assert world.families() == {"incidents": INCIDENT_TASKS}
    assert world.hash == build(SuiteSpec(families=["incidents"])).hash


def test_every_reading_is_named_in_the_prompt_and_the_budget_is_cause_plus_two(world):
    for record in FAMILIES["incidents"].records():
        task = world.by_id[f"incidents/{record['id']}"]
        assert task.routes["/readings"] == {"readings": sorted(record["readings"])}
        for name in record["readings"]:
            assert name in task.prompt, f"{task.id}: listing must be free — {name} is not in the prompt"
            assert task.routes[f"/readings/{name}"]["text"] == record["readings"][name]
        assert task.http_budget == len(record["cause_readings"]) + 2


def test_the_check_takes_the_gold_answer_and_refuses_the_decoy(world, tmp_path):
    for record in FAMILIES["incidents"].records():
        check = world.by_id[f"incidents/{record['id']}"].check
        klass, cause, decoy = record["class"], record["cause_readings"], record["decoy_readings"]
        assert check({"class": klass, "cause_readings": cause}, tmp_path)
        assert not check({"class": "poison-message" if klass != "poison-message" else "bad-deploy", "cause_readings": cause}, tmp_path)
        assert not check({"class": klass, "cause_readings": decoy[:1]}, tmp_path)
        assert not check({"class": klass, "cause_readings": cause + decoy[:1]}, tmp_path)
        assert not check(f"{klass}: {cause[0]}", tmp_path)


def test_the_pool_look_alike_control_grades_as_upstream_outage(world):
    record = next(r for r in FAMILIES["incidents"].records() if r["id"] == "upstream-outage-b")
    assert record["class"] == "upstream-outage"
    assert "pool-debug" in record["decoy_readings"]


def test_every_task_names_its_decoy_shape_as_a_lesson_and_declares_the_cause_count_as_its_floor(world):
    for record in FAMILIES["incidents"].records():
        task = world.by_id[f"incidents/{record['id']}"]
        assert task.lesson == f"decoy-{record['decoy']}" and task.lesson in LESSONS
        assert task.knowing == {"http": len(record["cause_readings"])}


def test_the_naive_walk_down_the_bundle_dies_on_the_budget():
    """First contact reads every reading in the order the prompt lists them; every bundle holds more than the budget."""
    world = build(SuiteSpec(families=["incidents"], faults=FaultProfile(http_fault_fraction=0.0)))
    token = _suite.use(world)
    try:
        for task in world.tasks:
            naive = naive_outcome(task.id)
            assert "call budget" in (naive["error"]["cause"] or ""), f"{task.id}: the naive walk must die on the budget, got {naive}"
    finally:
        _suite.reset(token)


def test_the_stream_deals_the_whole_pool_over_the_decoy_shapes():
    batches = partition(StreamSpec(families=["incidents", "incidents-transfer"], batch=3, batches=6))
    assert len(batches) == 6 and all(len(b.tasks) == 3 for b in batches)
    assert len({t.id for b in batches for t in b.tasks}) == 6 * 3, "no task is dealt twice"
    dealt = {k for b in batches for k in lessons_of(b)}
    assert dealt == {f"decoy-{r['decoy']}" for r in FAMILIES["incidents"].records()}, "every decoy shape is in the pool"


def test_the_incidents_smoke_runs_both_arms_naively_over_the_three_decoy_lessons(tmp_path, monkeypatch):
    monkeypatch.delenv("HGI_WEAVE_PROJECT", raising=False)
    exp = _experiment.load(EXPERIMENTS / "incidents-smoke.toml")
    record = _experiment.run_arm(exp, "attached", tmp_path, commit=False)
    assert record["sessions"] == [f"S-000{n}" for n in range(1, 8)], "six stream passes and one revisit"
    log = json.loads((tmp_path / "incidents-smoke" / "attached" / "evolution.json").read_text())
    assert [p["kind"] for p in log["passes"]] == ["stream"] * 6 + ["revisit"]
    assert all(p["symptoms"] == {"naive": 3} for p in log["passes"]), "the stub walks the whole bundle and dies on the budget"
    assert set(log["lessons"]) == {"decoy-dependency", "decoy-saturation", "decoy-state"}
    detached = _experiment.run_arm(exp, "detached", tmp_path, commit=False)
    assert detached["sessions"] == [f"S-000{n}" for n in range(1, 7)] and detached["stream"]["revisit"] == []
