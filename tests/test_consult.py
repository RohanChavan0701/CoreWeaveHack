"""``hgi consult`` — the store read from outside the loop. The surface withholds the payload (the settlement test), the
registered-term route reaches what the boot's hook-major index reaches, the lexical route only nominates, a superseded
record is a tombstone pointing at its successor, an unknown term or id is refused by name, and nothing under the store
changes: no session, no disposition, no regenerated projection."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from hgi import consult as _consult
from hgi import index as _index
from hgi.cli import main
from tests.conftest import adjudicated_entry, adjudicator, decision_body, draft


def _admit(store, name="D-draft", **overrides):
    d = draft(store, name, **overrides)
    entry = adjudicated_entry(store, d.uid)
    entry.verdict = "admit"
    return store.admit(d, entry, adjudicator())


def _budget_body():
    body = decision_body()
    body["summary"] = {"latch": "a shell tool under a call budget; several files or inputs to inspect",
                       "not_this": ["calls whose inputs depend on a previous call's output"],
                       "stakes": "a budget exceeded fails the task outright"}
    body["decision"] = "Under a call budget, independent calls over known inputs are issued as one batched call."
    body["latches"][0]["guard"] = {"terms": ["shell-tool", "tool-budget"], "not_this": ["calls whose inputs depend on a previous call's output"]}
    return body


def _tree(root: Path) -> dict[str, str]:
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.rglob("*")) if p.is_file()}


def test_the_surface_carries_activation_and_withholds_the_payload(store):
    retry = _admit(store)
    cells = _consult.surface(store)
    cell = next(c for c in cells if c["record"] == retry.id)
    assert cell["status"] == "accepted" and cell["latch"] == retry.summary.latch and cell["stakes"] == retry.summary.stakes
    assert cell["terms"] == ["http-tool", "tool-call-retry"] and cell["not_this"] == retry.summary.not_this
    assert "decision" not in cell and retry.decision not in json.dumps(cells), "a cell a reader could obey is evicted to the record"
    assert retry.decision not in _consult.render_surface(cells, store.registry.terms("work-shape"))


def test_a_superseded_record_is_a_tombstone_pointing_at_its_successor(store):
    old = _admit(store, "old")
    d = draft(store, "new", decision="A retried call carries its cause, and the retry is logged.")
    d.supersedes = [old.id]
    entry = adjudicated_entry(store, d.uid)
    entry.verdict = "admit"
    new = store.admit(d, entry, adjudicator())  # the committer writes the reciprocal pointer the lineage projection reads
    _index.regenerate(store)
    cell = next(c for c in _consult.surface(store) if c["record"] == old.id)
    assert cell["status"] == "superseded" and "latch" not in cell and cell["successors"] == [new.id]
    projected = _consult.project(store, [old.id])[0]
    assert projected["note"] == _consult.TOMBSTONE and projected["successors"] == [new.id]


def test_registered_terms_route_through_the_hook_index_as_the_boot_does(store):
    retry, budget = _admit(store), _admit(store, "budget", **_budget_body())
    _index.regenerate(store)
    hits = _consult.latch(store, terms=["http-tool"])
    assert [h["record"] for h in hits] == [retry.id] and hits[0]["via"] == "index" and hits[0]["terms_matched"] == ["http-tool"]
    assert {c["record"] for c in _index.read(store, "hooks")["http-tool"]} == {retry.id}
    both = _consult.latch(store, terms=["http-tool", "tool-budget"])
    assert {h["record"] for h in both} == {retry.id, budget.id} and all(h["via"] == "index" for h in both)


def test_an_unregistered_term_is_refused_by_name_with_the_registry_listed(store):
    with pytest.raises(SystemExit, match="streaming-tool.*http-tool"):
        _consult.latch(store, terms=["streaming-tool"])


def test_a_problem_infers_the_terms_it_names_and_nominates_by_hook_prose(store):
    retry, budget = _admit(store), _admit(store, "budget", **_budget_body())
    _index.regenerate(store)
    hits = _consult.latch(store, problem="my shell tool has a call budget and I need to inspect several files")
    by_id = {h["record"]: h for h in hits}
    assert by_id[budget.id]["via"] == "index" and by_id[budget.id]["terms_matched"] == ["shell-tool", "tool-budget"]
    assert by_id[retry.id]["via"] == "lexical" and by_id[retry.id]["note"] == _consult.NOMINATED
    assert hits[0]["record"] == budget.id, "the exact route sorts before a nomination"
    excluded = _consult.latch(store, problem="a shell tool under a call budget, with calls whose inputs depend on a previous call's output")
    assert next(h for h in excluded if h["record"] == budget.id)["excluded_by"] == budget.summary.not_this


def test_the_projection_carries_the_payload_and_refuses_an_unknown_id(store):
    retry = _admit(store)
    cell = _consult.project(store, [retry.id])[0]
    assert cell["decision"] == retry.decision and cell["counterfactual"] == retry.counterfactual
    assert cell["premises"][0]["status"] == "supported" and cell["residue"] == retry.enforcement.residue
    assert retry.decision in _consult.render_projection([cell])
    with pytest.raises(SystemExit, match="D-9999"):
        _consult.project(store, ["D-9999"])


def test_nothing_latched_falls_back_to_the_surface(store):
    _admit(store)
    _index.regenerate(store)
    out = _consult.consult(store, problem="rotate a pdf")
    assert out["latched"] == [] and "surface" in out and "records" not in out
    assert _consult.NOTHING in _consult.render(out, store.registry.terms("work-shape"))


def test_consult_reads_and_never_writes(store):
    _admit(store)
    _index.regenerate(store)
    before = _tree(store.root)
    _consult.consult(store, problem="a shell tool under a call budget")
    _consult.consult(store, terms=["http-tool"], with_articles=True)
    _consult.consult(store, everything=True)
    assert _tree(store.root) == before
    assert store.all("session") == [] and store.all("disposition") == []


def test_the_command_prints_the_structure_as_json(store, capsys):
    retry = _admit(store)
    _index.regenerate(store)
    assert main(["consult", "--store", str(store.root), "--terms", "http-tool", "--json"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert [h["record"] for h in out["latched"]] == [retry.id] and out["records"][0]["decision"] == retry.decision
    assert main(["--store", str(store.root), "consult"]) == 0
    assert retry.summary.latch in capsys.readouterr().out
