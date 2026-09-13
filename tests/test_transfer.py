"""The transfer family: the same conventions the `conventions` family carries, worn in different clothes.

Each convention is proven the way `conventions` proves its own — the naive
policy trips over it, a policy that knows it passes within budget — and the
clothes are proven different: the files, the API paths and the moved
endpoints this family names are disjoint from `conventions`', while the
work-shape terms a boot would classify are shared. That disjointness is the
transfer point: a record keyed on a path or a filename cannot score here,
one keyed on the convention can.
"""

from __future__ import annotations

import pytest

import suite as _suite
from suite.faults import FaultProfile
from suite.families import FAMILIES
from suite.tasks import SuiteSpec, build
from suite.tools import ToolError, Tools

TRANSFER_TASKS = 6


def test_the_transfer_family_loads_six_tasks_with_unique_ids_and_composes():
    tasks = FAMILIES["transfer"].tasks()
    assert len(tasks) == TRANSFER_TASKS
    assert len({t.id for t in tasks}) == TRANSFER_TASKS
    world = build(SuiteSpec(families=["conventions", "api", "transfer"]))
    assert world.families() == {"conventions": 10, "api": 100, "transfer": TRANSFER_TASKS}
    assert len(world.by_id) == 10 + 100 + TRANSFER_TASKS


def test_transfer_re_dresses_conventions_shared_shapes_disjoint_clothes():
    """The lessons are shared (the work-shape terms overlap); the clothes are not (files, paths, endpoints differ)."""
    conv = FAMILIES["conventions"].tasks()
    trans = FAMILIES["transfer"].tasks()

    # The presentations a boot classifies are drawn from the same closed vocabulary.
    conv_shapes = {s for t in conv for s in t.shapes}
    trans_shapes = {s for t in trans for s in t.shapes}
    assert trans_shapes <= conv_shapes, "a transfer task must present as a convention already does"

    # But the clothes — the file names and the API paths — are disjoint, so nothing keyed on a name transfers.
    conv_files = {name for t in conv for name in t.files}
    trans_files = {name for t in trans for name in t.files}
    assert conv_files and trans_files and not (conv_files & trans_files), "the file names must be re-dressed"

    conv_routes = {path for t in conv for path in t.routes}
    trans_routes = {path for t in trans for path in t.routes}
    assert conv_routes and trans_routes and not (conv_routes & trans_routes), "the API surface must be re-dressed"


def test_a_paged_transfer_task_walks_its_whole_collection_within_budget(tmp_path):
    """The paging convention re-dressed: follow `next` until it is null; the budget leaves room and no more."""
    world = build(SuiteSpec(families=["transfer"], faults=FaultProfile(http_fault_fraction=0.0)))
    for tid, first, gold, budget in [("transfer/paged_total", "/records", 27, 4), ("transfer/paged_active", "/accounts", 3, 5)]:
        spec = world.by_id[tid]
        assert spec.shapes == ("http-tool", "error-wrapping") and not spec.files and spec.http_budget == budget
        path, seen, pages = first, [], 0
        while path is not None:
            body = spec.routes[path]
            seen += body["items"]
            path, pages = body["next"], pages + 1
        assert pages > 1, f"{tid}: a single-page collection is not a paging convention"
        assert len(spec.routes) == pages, f"{tid}: the API serves its pages, nothing else"
        assert spec.check(gold, tmp_path) is True  # the gold answer passes the hidden check


def test_a_moved_transfer_endpoint_answers_410_then_serves_under_v2(tmp_path):
    """The /v2 convention re-dressed: the original endpoint is 410 Gone naming its /v2 successor."""
    world = build(SuiteSpec(families=["transfer"], faults=FaultProfile(http_fault_fraction=0.0)))
    for tid, gone, moved in [("transfer/moved_account", "/account/42", "/v2/account/42"),
                             ("transfer/moved_health", "/health", "/v2/health")]:
        spec = world.by_id[tid]
        tools = Tools(task=spec.id, workdir=tmp_path, profile=world.faults, routes=spec.routes, http_budget=spec.http_budget)
        with pytest.raises(ToolError) as e:
            tools.http_get(gone)
        assert "410" in e.value.cause and moved in e.value.cause and not e.value.transient
        assert tools.http_get(moved) is not None
        assert tools.budget_respected()


# The knowing policy for each convention — reached the way `conventions`' knowing policies are, but on this
# family's clothes: the no-newline files counted per record (not undercounted by wc -l), the pages walked to
# the end, the /v2 endpoint fetched directly.
KNOWING = {
    "transfer/report_lines": lambda t: int(t.shell("awk 'END{print NR}' part-1.tsv part-2.tsv part-3.tsv part-4.tsv").strip()),
    "transfer/chunk_lines": lambda t: int(t.shell("awk 'END{print NR}' chunk_00.dat chunk_01.dat").strip()),
    "transfer/paged_total": lambda t: sum(t.http_get("/records")["items"]) + sum(t.http_get("/records?page=2")["items"]),
    "transfer/paged_active": lambda t: sum(1 for p in ("/accounts", "/accounts?page=2", "/accounts?page=3") for a in t.http_get(p)["items"] if a["active"]),
    "transfer/moved_account": lambda t: t.http_get("/v2/account/42")["name"],
    "transfer/moved_health": lambda t: "ok" if t.http_get("/v2/health")["ok"] else "down",
}


@pytest.mark.parametrize("task_id", sorted(KNOWING))
def test_each_transfer_convention_fails_naively_and_passes_when_known(tmp_path, task_id):
    from suite.agent import Script

    world = build(SuiteSpec(families=["transfer"], faults=FaultProfile(http_fault_fraction=0.0)))
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
