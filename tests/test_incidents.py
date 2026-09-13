"""The incidents families: nine bundles worn four ways, each a budgeted walk whose decoy readings are the convention.

Every clothing is proven to grade the same shape — the class, the counts of
cause and decoy readings, the lesson, the knowing floor — and the four
clothes of one scenario to share no name: reading names, service names and
the API surface are pairwise disjoint. That disjointness is the transfer
point the stream turns on: a record keyed on the convention scores on the
next clothing, one keyed on `pool-debug` or `orders` scores on none.
``incidents`` leaves one call of slack, ``incidents-strict`` none.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

import suite as _suite
from hgi import experiment as _experiment
from suite.faults import FaultProfile
from suite.families import FAMILIES
from suite.families.incidents import CLOTHES, SERVICES, SLACK, redress
from suite.lessons import LESSONS, naive_outcome
from suite.stream import StreamSpec, lessons_of, partition
from suite.tasks import SuiteSpec, build

SCENARIOS = 9
TASKS = SCENARIOS * CLOTHES
EXPERIMENTS = Path(__file__).resolve().parents[1] / "experiments"
RECORDS = FAMILIES["incidents"].records()
DRESSED = [(r["id"], i) for r in RECORDS for i in range(CLOTHES)]


@pytest.fixture(scope="module")
def world():
    return build(SuiteSpec(families=["incidents", "incidents-strict"]))


def _record(scenario: str, i: int) -> dict:
    return redress(next(r for r in RECORDS if r["id"] == scenario), i)


def test_both_families_load_thirty_six_tasks_and_are_pinned_stable(world):
    assert world.families() == {"incidents": TASKS, "incidents-strict": TASKS}
    assert len(world.by_id) == 2 * TASKS, "no duplicate task ids across the pair"
    assert world.hash == build(SuiteSpec(families=["incidents", "incidents-strict"])).hash


@pytest.mark.parametrize("scenario,i", DRESSED)
def test_every_clothing_names_its_readings_its_lesson_and_its_floor(world, scenario, i):
    record = _record(scenario, i)
    task = world.by_id[f"incidents/{scenario}_{i}"]
    assert task.routes["/readings"] == {"readings": sorted(record["readings"])}
    for name in record["readings"]:
        assert name in task.prompt, f"{task.id}: listing must be free — {name} is not in the prompt"
        assert task.routes[f"/readings/{name}"]["text"] == record["readings"][name]
    assert task.lesson == f"decoy-{record['decoy']}" and task.lesson in LESSONS
    assert task.knowing == {"http": len(record["cause_readings"])}


@pytest.mark.parametrize("scenario,i", DRESSED)
def test_the_check_takes_the_gold_answer_and_refuses_the_decoy(world, scenario, i, tmp_path):
    record = _record(scenario, i)
    klass, cause, decoy = record["class"], record["cause_readings"], record["decoy_readings"]
    for fam in SLACK:
        check = world.by_id[f"{fam}/{scenario}_{i}"].check
        assert check({"class": klass, "cause_readings": cause}, tmp_path)
        assert not check({"class": "poison-message" if klass != "poison-message" else "bad-deploy", "cause_readings": cause}, tmp_path)
        assert not check({"class": klass, "cause_readings": decoy[:1]}, tmp_path)
        assert not check({"class": klass, "cause_readings": cause + decoy[:1]}, tmp_path), "the gold class with a decoy cited fails"
        assert not check(f"{klass}: {cause[0]}", tmp_path)
        # `ruled_out` is a disposal, not a citation: the decoy set aside there is what a right answer does with it
        assert check({"class": klass, "cause_readings": cause, "ruled_out": decoy[:1]}, tmp_path)


@pytest.mark.parametrize("fam,slack", SLACK.items())
def test_the_budget_is_the_cause_readings_plus_the_family_slack(world, fam, slack):
    for scenario, i in DRESSED:
        task = world.by_id[f"{fam}/{scenario}_{i}"]
        assert task.http_budget == len(_record(scenario, i)["cause_readings"]) + slack
        assert task.http_budget < len(task.routes) - 1, f"{task.id}: the bundle must hold more readings than the budget"


def test_the_naive_walk_down_every_clothing_dies_on_the_budget():
    """First contact reads every reading in the order the prompt lists them; every bundle holds more than the budget."""
    world = build(SuiteSpec(families=["incidents", "incidents-strict"], faults=FaultProfile(http_fault_fraction=0.0)))
    token = _suite.use(world)
    try:
        for task in world.tasks:
            naive = naive_outcome(task.id)
            assert "call budget" in (naive["error"]["cause"] or ""), f"{task.id}: the naive walk must die on the budget, got {naive}"
    finally:
        _suite.reset(token)


@pytest.mark.parametrize("scenario", [r["id"] for r in RECORDS])
def test_the_four_clothes_of_a_scenario_share_the_shape_and_share_no_name(world, scenario):
    dressed = [_record(scenario, i) for i in range(CLOTHES)]
    source = dressed[0]
    for record, i in zip(dressed, range(CLOTHES)):
        task = world.by_id[f"incidents/{scenario}_{i}"]
        assert record["class"] == source["class"] and record["decoy"] == source["decoy"]
        assert len(record["cause_readings"]) == len(source["cause_readings"])
        assert len(record["decoy_readings"]) == len(source["decoy_readings"])
        assert task.lesson == world.by_id[f"incidents/{scenario}_0"].lesson
        if i:
            for service in SERVICES:
                assert not re.search(rf"\b{service}\b", task.prompt, re.I), f"{task.id}: {service} survived the re-dressing"
    for a in range(CLOTHES):
        for b in range(a + 1, CLOTHES):
            names_a, names_b = set(dressed[a]["readings"]), set(dressed[b]["readings"])
            assert names_a and not (names_a & names_b), f"{scenario}: dressings {a} and {b} share a reading name"
            routes_a, routes_b = set(world.by_id[f"incidents/{scenario}_{a}"].routes), set(world.by_id[f"incidents/{scenario}_{b}"].routes)
            assert routes_a & routes_b == {"/readings"}, f"{scenario}: dressings {a} and {b} share a route"
            named_a, named_b = _services(world, scenario, a), _services(world, scenario, b)
            assert named_a and not (named_a & named_b), f"{scenario}: dressings {a} and {b} share a service name"


def _services(world, scenario: str, i: int) -> set[str]:
    """What a dressing calls the services, read off its prompt: the originals at dressing 0, their replacements after."""
    from suite.families.incidents import _substitution

    prompt = world.by_id[f"incidents/{scenario}_{i}"].prompt
    named = set(SERVICES) if i == 0 else {_substitution(scenario, i)[s] for s in SERVICES}
    return {s for s in named if re.search(rf"\b{re.escape(s)}\b", prompt, re.I)}


def test_the_pool_look_alike_control_stays_the_control_in_every_clothing(world):
    """``upstream-outage-b`` is a timeout storm with a genuinely saturated pool: its pool readings are decoys, and the
    re-dressing must not move one of them into the cause list, in any clothing."""
    source = next(r for r in RECORDS if r["id"] == "upstream-outage-b")
    assert source["class"] == "upstream-outage" and "pool-debug" in source["decoy_readings"]
    for i in range(CLOTHES):
        record = _record("upstream-outage-b", i)
        pool = {n for n in record["decoy_readings"]}
        assert len(pool) == len(source["decoy_readings"]) and not pool & set(record["cause_readings"])
        assert world.by_id[f"incidents/upstream-outage-b_{i}"].lesson == "decoy-saturation"


def test_the_stream_deals_the_whole_pool_over_the_decoy_shapes():
    batches = partition(StreamSpec(families=["incidents"], batch=3, batches=12))
    assert len(batches) == 12 and all(len(b.tasks) == 3 for b in batches)
    assert len({t.id for b in batches for t in b.tasks}) == TASKS, "every task is dealt exactly once"
    dealt = {k for b in batches for k in lessons_of(b)}
    assert dealt == {f"decoy-{r['decoy']}" for r in RECORDS}, "every decoy shape is in the pool"
    for b in batches:  # the deal balances over lessons, not scenarios, so two clothes of one scenario can meet — never four
        worn = [t.id.split("/")[1].rsplit("_", 1)[0] for t in b.tasks]
        assert max(worn.count(s) for s in worn) <= 2, f"a batch holds {worn}"


def test_the_incidents_smoke_runs_both_arms_naively_over_the_three_decoy_lessons(tmp_path, monkeypatch):
    monkeypatch.delenv("HGI_WEAVE_PROJECT", raising=False)
    exp = _experiment.load(EXPERIMENTS / "incidents-smoke.toml")
    record = _experiment.run_arm(exp, "attached", tmp_path, commit=False)
    assert record["sessions"] == [f"S-{n:04d}" for n in range(1, 14)], "twelve stream passes and one revisit"
    log = json.loads((tmp_path / "incidents-smoke" / "attached" / "evolution.json").read_text())
    assert [p["kind"] for p in log["passes"]] == ["stream"] * 12 + ["revisit"]
    assert all(p["symptoms"] == {"naive": 3} for p in log["passes"]), "the stub walks the whole bundle and dies on the budget"
    assert set(log["lessons"]) == {"decoy-dependency", "decoy-saturation", "decoy-state"}
    detached = _experiment.run_arm(exp, "detached", tmp_path, commit=False)
    assert detached["sessions"] == [f"S-{n:04d}" for n in range(1, 13)] and detached["stream"]["revisit"] == []
    _experiment.run_arm(exp, "strict", tmp_path, commit=False)
    strict = json.loads((tmp_path / "incidents-smoke" / "strict" / "evolution.json").read_text())
    assert all(p["symptoms"] == {"naive": 3} for p in strict["passes"]), "zero slack dies on the budget a call sooner"
    assert set(strict["lessons"]) == set(log["lessons"])
