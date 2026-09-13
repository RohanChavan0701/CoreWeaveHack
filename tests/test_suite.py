"""The suite as an object: composed from families under one fault profile, pinned by hash; the world's
conventions are checkable — the naive policy fails each and a policy that knows the convention passes."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import suite as _suite
from suite.faults import FaultProfile
from suite.families import FAMILIES
from suite.tasks import SuiteSpec, build
from suite.tools import ToolError, Tools


def test_the_default_suite_is_the_genesis_family_and_the_hash_covers_the_profile():
    world = build(SuiteSpec())
    assert [t.id for t in world.tasks] == sorted(t.id for t in FAMILIES["genesis"].tasks()) and world.hash == build(SuiteSpec()).hash
    harder = build(SuiteSpec(faults=FaultProfile(http_fault_calls=2)))
    assert harder.hash != world.hash and [t.id for t in harder.tasks] == [t.id for t in world.tasks]


def test_families_compose_and_a_seeded_sample_is_stable():
    world = build(SuiteSpec(families=["genesis", "conventions"]))
    assert world.families() == {"genesis": 6, "conventions": 10} and len(world.by_id) == 16
    a = build(SuiteSpec(families=["conventions"], size=4, seed=1))
    b = build(SuiteSpec(families=["conventions"], size=4, seed=1))
    c = build(SuiteSpec(families=["conventions"], size=4, seed=2))
    assert [t.id for t in a.tasks] == [t.id for t in b.tasks] and len(a.tasks) == 4
    assert [t.id for t in a.tasks] != [t.id for t in c.tasks]
    with pytest.raises(SystemExit, match="no task family"):
        build(SuiteSpec(families=["nowhere"]))


def test_faults_are_fixed_per_task_name_and_the_profile_says_how_many_calls_fail(tmp_path):
    world = build(SuiteSpec(faults=FaultProfile(http_fault_calls=2)))
    spec = world.by_id["genesis/sum_numbers"]
    assert world.faults.faulted(spec.id) and world.faults.faulted("elsewhere/sum_numbers")
    tools = Tools(task=spec.id, workdir=tmp_path, profile=world.faults, routes=spec.routes)
    for _ in range(2):
        with pytest.raises(ToolError) as e:
            tools.http_get("/numbers")
        assert e.value.transient
    assert tools.http_get("/numbers") == [3, 5, 8, 13, 21]


def test_the_http_budget_and_a_route_that_answers_with_an_error(tmp_path):
    world = build(SuiteSpec(families=["conventions"], faults=FaultProfile(http_fault_fraction=0.0)))
    spec = world.by_id["conventions/versioned_user"]
    tools = Tools(task=spec.id, workdir=tmp_path, profile=world.faults, routes=spec.routes, http_budget=spec.http_budget)
    with pytest.raises(ToolError) as e:
        tools.http_get("/users/7")
    assert "410" in e.value.cause and "/v2/users/7" in e.value.cause and not e.value.transient
    assert tools.http_get("/v2/users/7")["name"] == "Ada"
    with pytest.raises(ToolError, match="refused"):
        tools.http_get("/v2/users/7")
    assert not tools.budget_respected()


KNOWING = {
    "conventions/lines_without_newline": lambda t: sum(int(t.shell("awk 'END{print NR}' " + n).strip()) for n in ["a.txt"]) and int(t.shell("cat a.txt b.txt c.txt d.txt e.txt | awk 'END{print NR}'").strip()) + 4,
    "conventions/log_lines": lambda t: int(t.shell("awk 'END{print NR}' x.log y.log z.log").strip()),
    "conventions/paged_sum": lambda t: sum(t.http_get("/items")["items"]) + sum(t.http_get("/items?page=2")["items"]),
    "conventions/paged_count": lambda t: sum(1 for p in ("/users", "/users?page=2", "/users?page=3") for u in t.http_get(p)["items"] if u["active"]),
    "conventions/versioned_user": lambda t: t.http_get("/v2/users/7")["name"],
    "conventions/versioned_status": lambda t: "ok" if t.http_get("/v2/status")["ok"] else "not ok",
    "conventions/csv_quoted_city": lambda t: int(t.shell("python3 -c \"import csv;print(sum(1 for r in csv.DictReader(open('people.csv')) if r['city']=='Berlin'))\"").strip()),
    "conventions/csv_quoted_total": lambda t: float(t.shell("python3 -c \"import csv;print(sum(float(r['total']) for r in csv.DictReader(open('orders.csv')) if r['customer']=='Acme, Inc.'))\"").strip()),
    "conventions/bom_config": lambda t: _report(t, json.loads(t.read_file("config.json").lstrip("﻿"))),
    "conventions/bom_settings": lambda t: {"name": (s := json.loads(t.read_file("settings.json").lstrip("﻿")))["name"], "enabled": sum(1 for v in s["features"].values() if v)},
}


def _report(t: Tools, config: dict) -> dict:
    report = {"title": config["title"], "count": len(config["items"])}
    t.write_file("report.json", json.dumps(report))
    return report


@pytest.mark.parametrize("task_id", sorted(KNOWING))
def test_each_convention_fails_naively_and_passes_when_known(tmp_path, task_id):
    from suite.agent import Script

    world = build(SuiteSpec(families=["conventions"], faults=FaultProfile(http_fault_fraction=0.0)))
    token = _suite.use(world)
    try:
        spec = world.by_id[task_id]
        naive_dir = tmp_path / "naive"
        spec.setup(naive_dir)
        naive = Tools(task=spec.id, workdir=naive_dir, profile=world.faults, routes=spec.routes, shell_budget=spec.shell_budget, http_budget=spec.http_budget)
        try:
            naive_result = spec.stub(Script(naive, []))
            naive_ok = spec.check(naive_result, naive_dir)
        except Exception:
            naive_ok = False
        assert not naive_ok, f"{task_id}: the naive policy must trip over the convention"

        known_dir = tmp_path / "known"
        spec.setup(known_dir)
        known = Tools(task=spec.id, workdir=known_dir, profile=world.faults, routes=spec.routes, shell_budget=spec.shell_budget, http_budget=spec.http_budget)
        result = KNOWING[task_id](known)
        assert spec.check(result, known_dir), f"{task_id}: the knowing policy must pass; got {result!r}"
        assert known.budget_respected(), f"{task_id}: the knowing policy must fit the budget"
    finally:
        _suite.reset(token)


def test_a_task_without_a_scripted_policy_fails_on_the_stub_and_rows_carry_their_scores(store):
    from hgi import evaluate as _evaluate
    from hgi.store import now
    from hgi.types import Session
    from suite.tasks import Task

    plain = FAMILIES["genesis"].tasks()[0]
    world = build(SuiteSpec())
    world.tasks.append(Task("genesis/unscripted", "Return 1.", ("output-schema",), plain.schema, lambda r, w: r == 1))
    world.__dict__.pop("by_id", None)
    world.__dict__.pop("hash", None)
    token = _suite.use(world)
    try:
        s = Session(id=store.mint("session"), pass_=1, started_at=now(), attached=True)
        s = _evaluate.run(store, s)
        rows = {r["task"]: r for r in s.evaluation.rows}
        assert rows["genesis/unscripted"]["error"]["message"].startswith("no scripted policy")
        assert rows["genesis/unscripted"]["scores"]["task_pass_rate"]["value"] == 0.0
        assert rows["genesis/schema_answer"]["scores"]["task_pass_rate"]["value"] == 1.0
        assert s.evaluation.suite_hash == world.hash and s.evaluation.scores["suite_hash"].value == 1.0
    finally:
        _suite.reset(token)


def test_a_spec_file_and_the_environment_name_the_suite(tmp_path, monkeypatch):
    from suite.tasks import from_env, load_spec

    path = tmp_path / "world.toml"
    path.write_text('[suite]\nfamilies = ["conventions"]\nsize = 3\n[suite.faults]\nhttp_fault_calls = 2\n')
    spec = load_spec(path)
    assert spec.families == ["conventions"] and spec.size == 3 and spec.faults.http_fault_calls == 2
    monkeypatch.setenv("HGI_SUITE", str(path))
    assert len(from_env().tasks) == 3
    monkeypatch.delenv("HGI_SUITE")
    assert from_env().families() == {"genesis": 6}
