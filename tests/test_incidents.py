"""The incidents family: nine bundles, each a budgeted walk whose decoy readings are the convention."""

from __future__ import annotations

import pytest

from suite.families import FAMILIES
from suite.tasks import SuiteSpec, build

INCIDENT_TASKS = 9


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
