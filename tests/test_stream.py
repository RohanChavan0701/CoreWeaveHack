"""The stream: lessons in many clothes, dealt into batches met at first sight, with the evolution log read back.

The curriculum is proven the way `conventions` and `transfer` are — every clothing of a lesson trips the naive policy
and passes a knowing one within budget — and its clothes are disjoint from the hand-written families'. The deal is
balanced over lessons and deterministic; the symptom of a failed row is derived from the naive outcome; the stub
smoke experiment runs a stream arm end to end and writes its evolution log.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

import suite as _suite
from hgi import evolution as _evolution
from hgi import experiment as _experiment
from hgi import model as _model
from suite import lessons as _lessons
from suite.families import FAMILIES
from suite.faults import FaultProfile
from suite.families.curriculum import CLOTHES
from suite.stream import StreamSpec, key_of, lessons_of, partition
from suite.tasks import SuiteSpec, build
from suite.tools import Tools

EXPERIMENTS = Path(__file__).resolve().parents[1] / "experiments"


@pytest.fixture(autouse=True)
def clean_backends():
    _model.reset()
    yield
    _model.reset()


def test_the_curriculum_wears_every_lesson_in_disjoint_clothes():
    tasks = FAMILIES["curriculum"].tasks()
    assert len(tasks) == CLOTHES * len(_lessons.LESSONS) and len({t.id for t in tasks}) == len(tasks)
    assert {t.lesson for t in tasks} == set(_lessons.LESSONS)
    hand = FAMILIES["conventions"].tasks() + FAMILIES["transfer"].tasks()
    assert {t.lesson for t in hand} <= set(_lessons.LESSONS), "the hand-written families name lessons the register knows"
    assert not ({n for t in tasks for n in t.files} & {n for t in hand for n in t.files}), "file names re-dressed"
    assert not ({p for t in tasks for p in t.routes} & {p for t in hand for p in t.routes}), "routes re-dressed"
    assert {s for t in tasks for s in t.shapes} <= {s for t in hand for s in t.shapes} | {"output-schema"}, "presentations from the registered vocabulary"
    strict = FAMILIES["curriculum-strict"].tasks()
    assert [t.id.split("/")[1] for t in strict] == [t.id.split("/")[1] for t in tasks], "the strict family wears the same clothes"
    assert all(a.files == b.files and a.routes == b.routes and a.lesson == b.lesson for a, b in zip(tasks, strict))
    assert all((b.shell_budget or 0) <= (a.shell_budget or 0) and (b.http_budget or 0) <= (a.http_budget or 0) for a, b in zip(tasks, strict))
    assert any(b.shell_budget == 1 for b in strict) and any(b.http_budget == 1 for b in strict), "strict budgets hold exactly the knowing policy's calls"


# The knowing policy per lesson, on any clothing: derived from the task's own world, one budgeted call each.
def _knowing(task, tools: Tools):
    if task.lesson == "trailing-newline":
        return int(tools.shell("awk 'END{print NR}' " + " ".join(task.files)).strip())
    if task.lesson == "paged-api":
        path, total, count = next(p for p in task.routes if "?" not in p), 0, 0
        while path is not None:
            body = tools.http_get(path)
            total += sum(x for x in body["items"] if isinstance(x, int))
            count += sum(1 for x in body["items"] if isinstance(x, dict) and x["active"])
            path = body["next"]
        return count if "active" in task.prompt else total
    if task.lesson == "moved-v2":
        body = tools.http_get(next(p for p in task.routes if p.startswith("/v2/")))
        return body["name"] if "name" in body else ("ok" if body["ok"] else "down")
    if task.lesson == "csv-quoted":
        name = next(iter(task.files))
        if m := re.search(r"city is (\w+)", task.prompt):
            return int(tools.shell(f"python3 -c \"import csv;print(sum(1 for r in csv.DictReader(open('{name}')) if r['city']=='{m.group(1)}'))\"").strip())
        firm = re.search(r'customer is "([^"]+)"', task.prompt).group(1)
        return float(tools.shell(f"python3 -c \"import csv;print(round(sum(float(r['total']) for r in csv.DictReader(open('{name}')) if r['customer']=='{firm}'),2))\"").strip())
    if task.lesson == "footer-row":
        name = next(iter(task.files))
        if "sum of the amount" in task.prompt:
            return int(tools.shell(f"awk -F, 'NR>1 && $1!=\"TOTAL\" {{t+=$3}} END {{print t+0}}' {name}").strip())
        return int(tools.shell(f"awk -F, 'NR>1 && $1!=\"TOTAL\"' {name} | wc -l").strip())
    if task.lesson == "token-route":
        token = tools.read_file("token.txt").strip()
        path = next(p for p in task.routes if "?" not in p)
        return tools.http_get(f"{path}?token={token}")[path.rsplit("/", 1)[-1]]
    if task.lesson == "bom":
        name = next(iter(task.files))
        data = json.loads(tools.read_file(name).lstrip("﻿"))
        key = next(k for k in task.schema["properties"]["result"]["required"] if k != "count")
        items = next(v for v in data.values() if isinstance(v, list))
        return {key: data[key], "count": len(items)}
    raise AssertionError(task.lesson)


@pytest.mark.parametrize("task_id", [t.id for fam in ("curriculum", "curriculum-strict") for t in FAMILIES[fam].tasks()])
def test_each_clothing_fails_naively_and_passes_when_known(tmp_path, task_id):
    world = build(SuiteSpec(families=[task_id.split("/")[0]], faults=FaultProfile(http_fault_fraction=0.0)))
    token = _suite.use(world)
    try:
        spec = world.by_id[task_id]
        naive = _lessons.naive_outcome(task_id)
        assert naive is not None and ("error" in naive or not spec.check(naive["result"], tmp_path)), f"{task_id}: the naive policy must trip"
        spec.setup(tmp_path)
        tools = Tools(task=spec.id, workdir=tmp_path, profile=world.faults, routes=spec.routes, shell_budget=spec.shell_budget, http_budget=spec.http_budget)
        result = _knowing(spec, tools)
        assert spec.check(result, tmp_path), f"{task_id}: the knowing policy must pass; got {result!r}"
        assert tools.budget_respected(), f"{task_id}: the knowing policy must fit the budget"
    finally:
        _suite.reset(token)


def test_the_deal_is_balanced_over_lessons_and_deterministic():
    spec = StreamSpec(batch=8, batches=10, seed=3, revisit=[2])
    batches = partition(spec)
    assert len(batches) == 10 and all(len(b.tasks) == 8 for b in batches)
    assert len({t.id for b in batches for t in b.tasks}) == 80, "no task is dealt twice"
    for b in batches:
        assert set(lessons_of(b)) == set(_lessons.LESSONS) and max(lessons_of(b).values()) <= 2, "every batch holds every lesson, none more than twice"
    assert [b.hash for b in partition(spec)] == [b.hash for b in batches]
    assert [b.hash for b in partition(StreamSpec(batch=8, batches=10, seed=4))] != [b.hash for b in batches]
    with pytest.raises(SystemExit, match="holds 84"):
        partition(StreamSpec(batch=9, batches=10))
    with pytest.raises(SystemExit, match="revisits batch 11"):
        partition(StreamSpec(batch=8, batches=10, revisit=[11]))
    mixed = partition(StreamSpec(families=["curriculum", "genesis"], batch=8, batches=1))
    assert "genesis" in lessons_of(mixed[0]), "a task with no lesson is dealt under its family"
    assert key_of(mixed[0].tasks[0]) in set(_lessons.LESSONS) | {"genesis"}


def test_a_symptom_is_derived_from_the_naive_outcome():
    world = build(SuiteSpec(families=["curriculum"]))
    token = _suite.use(world)
    try:
        newline = next(t for t in world.tasks if t.lesson == "trailing-newline")
        naive = _lessons.naive_outcome(newline.id)["result"]
        passed = {"task": newline.id, "result": naive + len(newline.files), "error": None, "scores": {"task_pass_rate": {"value": 1.0}}}
        assert _lessons.symptom(newline, passed) == "pass"
        assert _lessons.symptom(newline, {"task": newline.id, "result": naive, "error": None, "scores": {"task_pass_rate": {"value": 0.0}}}) == "naive"
        assert _lessons.symptom(newline, {"task": newline.id, "result": naive + 1, "error": None, "scores": {"task_pass_rate": {"value": 0.0}}}) == "wrong"
        assert _lessons.symptom(newline, {"task": newline.id, "result": None, "error": {"message": "turn limit reached", "cause": "8 turns"}, "scores": {"task_pass_rate": {"value": 0.0}}}) == "error:turn-limit"
        moved = next(t for t in world.tasks if t.lesson == "moved-v2")
        gone = {"message": "GET failed", "cause": "HTTP 410 Gone: this API serves /v2/x"}
        assert _lessons.symptom(moved, {"task": moved.id, "result": None, "error": gone, "scores": {"task_pass_rate": {"value": 0.0}}}) == "naive"
        # reported without its cause, but the trace shows the 410 was met: still the naive shape
        assert _lessons.symptom(moved, {"task": moved.id, "result": None, "error": {"message": "GET failed", "cause": None}, "tool_errors": [gone],
                                        "scores": {"task_pass_rate": {"value": 0.0}}}) == "naive"
        assert _lessons.symptom(moved, {"task": moved.id, "result": None, "error": {"message": "GET failed", "cause": "HTTP 404 Not Found for /v3/x"},
                                        "scores": {"task_pass_rate": {"value": 0.0}}}) == "error:http-404"
        mbpp = build(SuiteSpec(families=["genesis"])).tasks[0]  # a task with a stub that passes: no naive outcome to reproduce
    finally:
        _suite.reset(token)
    token = _suite.use(build(SuiteSpec(families=["genesis"])))
    try:
        assert _lessons.symptom(mbpp, {"task": mbpp.id, "result": 1, "error": None, "scores": {"task_pass_rate": {"value": 0.0}}}) == "wrong"
    finally:
        _suite.reset(token)


def test_the_stream_smoke_runs_each_pass_on_its_own_batch_and_writes_the_evolution_log(tmp_path, monkeypatch):
    monkeypatch.delenv("HGI_WEAVE_PROJECT", raising=False)
    exp = _experiment.load(EXPERIMENTS / "stream-smoke.toml")
    spec = exp.resolve("attached")
    assert (spec.rounds, spec.passes, spec.revisits) == (2, 4, [1])
    record = _experiment.run_arm(exp, "attached", tmp_path, commit=False)
    assert record["sessions"] == [f"S-000{n}" for n in range(1, 6)], "four stream passes and one revisit"
    hashes = [b["hash"] for b in record["stream"]["batches"]]
    assert len(set(hashes)) == 4 and record["stream"]["passes"] == {n: n for n in range(1, 5)} | {5: 1}
    where = tmp_path / "stream-smoke" / "attached"
    assert (where / "store" / "consolidations" / "K-0002.json").exists() and not (where / "store" / "consolidations" / "K-0003.json").exists(), "no consolidation after the revisit"
    log = json.loads((where / "evolution.json").read_text())
    assert [p["hash"] for p in log["passes"]] == hashes + [hashes[0]]
    assert [p["kind"] for p in log["passes"]] == ["stream"] * 4 + ["revisit"]
    assert all(p["symptoms"] == {"naive": 4} for p in log["passes"]), "the stub is the naive policy: every failure is naive-shape"
    assert all(p["quality"]["economy"] == 0.0 and p["quality"]["transfer"] is None for p in log["passes"]), "quality is zero on failed rows and transfer unevaluable"
    assert set(log["lessons"]) == set(_lessons.LESSONS) and all(s["first_mention_pass"] is None for s in log["lessons"].values())
    md = (where / "evolution.md").read_text()
    assert "| 5 (revisit) | 1 |" in md and "| trailing-newline | invisible |" in md

    detached = _experiment.run_arm(exp, "detached", tmp_path, commit=False)
    assert detached["sessions"] == [f"S-000{n}" for n in range(1, 5)] and detached["stream"]["revisit"] == []
    text = _evolution.write_experiment(exp, tmp_path)
    assert "| batch | attached | detached | attached quality | detached quality |" in text
    assert "Over the stream: attached 0.00 (0/16), quality 0.00 / 0.00 / —; detached 0.00 (0/16), quality 0.00 / 0.00 / —." in text
    assert (tmp_path / "stream-smoke" / "evolution.md").exists()
    table = _experiment.report(exp, tmp_path)
    assert "| attached | stub | attached | 2×2 stream ×4 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | nothing |" in table


def test_every_clothing_declares_its_knowing_floor_and_carries_a_twin(tmp_path):
    """The twin wears the same names, columns and routes over different data; its own naive policy trips on it and the
    knowing policy passes it — so a method replayed there is graded on the convention, not the instance."""
    world = build(SuiteSpec(families=["curriculum"], faults=FaultProfile(http_fault_fraction=0.0)))
    token = _suite.use(world)
    try:
        differ = 0
        for t in world.tasks:
            assert (t.knowing is None) == (t.lesson == "bom"), f"{t.id}: every budgeted lesson declares the knowing policy's calls"
            if t.knowing:
                assert sum(t.knowing.values()) + 1 == sum(b for b in (t.shell_budget, t.http_budget) if b), f"{t.id}: the budget is the floor plus one"
            tw = t.twin
            assert tw is not None and tw.id == t.id and tw.lesson == t.lesson and set(tw.files) == set(t.files) and set(tw.routes) == set(t.routes)
            differ += tw.files != t.files or tw.routes != t.routes
            twin_dir = tmp_path / t.id.replace("/", "-")
            tw.setup(twin_dir)
            tools = Tools(task=tw.id, workdir=twin_dir, profile=world.faults, routes=tw.routes, shell_budget=tw.shell_budget, http_budget=tw.http_budget)
            assert tw.check(_knowing(tw, tools), twin_dir), f"{t.id}: the knowing policy must pass the twin"
        assert differ >= 70, "the twins differ in their data (a route with no data to vary is the same)"
    finally:
        _suite.reset(token)


def test_the_quality_scorers_grade_a_passed_solution_by_its_cost_and_its_method(tmp_path):
    from suite.scorers import MethodTransfer, SolutionEconomy, TurnEconomy

    world = build(SuiteSpec(families=["curriculum"], faults=FaultProfile(http_fault_fraction=0.0)))
    token = _suite.use(world)
    try:
        t = next(t for t in world.tasks if t.lesson == "trailing-newline")
        gold = sum(len(c.splitlines()) for c in t.files.values())
        knew = {"task": t.id, "result": gold, "error": None, "shell_calls": 1, "http_calls": 0, "turns": 2, "workdir": str(tmp_path),
                "commands": ["awk 'END{print NR}' " + " ".join(t.files)]}
        found = {**knew, "shell_calls": 2, "turns": 3, "commands": ["cat " + next(iter(t.files)), knew["commands"][0]]}
        fitted = {**knew, "commands": ["echo " + str(gold)]}
        failed = {**knew, "result": gold - 1}
        assert SolutionEconomy().score(output=knew, task=t.id)["value"] == 1.0
        assert SolutionEconomy().score(output=found, task=t.id)["value"] == 0.5
        assert SolutionEconomy().score(output=failed, task=t.id)["value"] == 0.0, "a failed row has no solution to be economical about"
        assert TurnEconomy().score(output=knew, task=t.id)["value"] == 1.0 and abs(TurnEconomy().score(output=found, task=t.id)["value"] - 2 / 3) < 1e-9
        assert MethodTransfer().score(output=knew, task=t.id)["value"] == 1.0, "the knowing command gives the twin's answer"
        assert MethodTransfer().score(output=fitted, task=t.id)["value"] == 0.0, "an answer echoed for this instance does not"
        assert MethodTransfer().score(output=failed, task=t.id)["value"] is None and MethodTransfer().score(output={**knew, "commands": []}, task=t.id)["value"] is None
        bom = next(t for t in world.tasks if t.lesson == "bom")
        assert SolutionEconomy().score(output={**knew, "task": bom.id}, task=bom.id)["value"] is None, "no budget, no floor"
        paged = next(t for t in world.tasks if t.lesson == "paged-api")
        assert MethodTransfer().score(output={**knew, "task": paged.id, "result": 0}, task=paged.id)["value"] is None, "a failed walk has no method to transfer"
    finally:
        _suite.reset(token)
