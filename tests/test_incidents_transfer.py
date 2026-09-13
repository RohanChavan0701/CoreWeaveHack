"""The incidents-transfer family: the nine bundles re-dressed — same convention, different clothes.

Each pair (``incidents/X``, ``incidents-transfer/X``) is proven to share the
graded shape — the class, the count of cause and decoy readings, the budget —
and to share no names: the reading names and the API surface are disjoint and
no service the original brief names survives into the re-dressed prompt. That
disjointness is the transfer point: a record keyed on the convention scores on
both, one keyed on `pool-debug` or `orders` scores on neither.
"""

from __future__ import annotations

import re

import pytest

from suite.families import FAMILIES
from suite.families.incidents_transfer import READINGS, SERVICES, record_of
from suite.tasks import SuiteSpec, build

INCIDENT_TASKS = 9


@pytest.fixture
def world():
    return build(SuiteSpec(families=["incidents", "incidents-transfer"]))


def test_the_family_loads_nine_tasks_and_the_pair_is_pinned_stable(world):
    assert world.families() == {"incidents": INCIDENT_TASKS, "incidents-transfer": INCIDENT_TASKS}
    assert len(world.by_id) == 2 * INCIDENT_TASKS, "no duplicate task ids across the pair"
    assert world.hash == build(SuiteSpec(families=["incidents", "incidents-transfer"])).hash


@pytest.mark.parametrize("scenario", [r["id"] for r in FAMILIES["incidents"].records()])
def test_each_pair_shares_its_shape_and_shares_no_names(world, scenario, tmp_path):
    original, redressed = world.by_id[f"incidents/{scenario}"], world.by_id[f"incidents-transfer/{scenario}"]
    record = next(r for r in FAMILIES["incidents"].records() if r["id"] == scenario)
    klass = record["class"]

    # The same graded shape: the class, the counts, the budget, the presentation.
    gold = [READINGS[n] for n in record["cause_readings"]]
    assert redressed.check({"class": klass, "cause_readings": gold}, tmp_path), "the re-dressed gold answer must pass"
    assert original.check({"class": klass, "cause_readings": record["cause_readings"]}, tmp_path)
    assert redressed.shapes == original.shapes and redressed.http_budget == original.http_budget
    assert len(gold) == len(record["cause_readings"])
    assert len(record_of(record)["decoy_readings"]) == len(record["decoy_readings"])
    assert len(redressed.routes) == len(original.routes)  # one reading each, plus the free listing

    # But no name: the readings, the API surface and the services are disjoint.
    names, redressed_names = set(record["readings"]), set(redressed.routes["/readings"]["readings"])
    assert names and not (names & redressed_names), "the reading names must be re-dressed"
    assert set(original.routes) & set(redressed.routes) == {"/readings"}, "the API surface must be re-dressed"
    for service in SERVICES:
        assert not re.search(rf"\b{service}\b", redressed.prompt, re.I), f"{scenario}: {service} survived the re-dressing"

    # And the memorised names do not transfer: citing the original readings fails the re-dressed task.
    assert not redressed.check({"class": klass, "cause_readings": record["cause_readings"]}, tmp_path)
    assert not redressed.check({"class": klass, "cause_readings": [READINGS[n] for n in record["decoy_readings"][:1]]}, tmp_path)
