"""The retirement leg: a decision considered but never applied over the review window is nominated by its
ratio, judged moot by the adjudicator, and flipped with its latches settled — the lint stays green."""

from __future__ import annotations

from hgi import consolidate as _consolidate
from hgi import index as _index
from hgi import lint as _lint
from hgi.store import now
from hgi.types import Disposition, Session
from tests.conftest import adjudicated_entry, adjudicator, draft


def test_never_applied_decision_retires_on_telemetry(store):
    d = draft(store)
    entry = adjudicated_entry(store, d.uid)
    entry.verdict = "admit"
    decision = store.admit(d, entry, adjudicator())
    window = store.registry.bars["retirement"]["window_passes"]
    for n in range(1, window + 1):
        s = Session(id=store.mint("session"), pass_=n, started_at=now(), closed_at=now(), attached=True,
                    evaluation={"evaluation": "suite-v1", "scores": {"task_pass_rate": {"series": "suite-v1/task_pass_rate", "value": 0.5, "as_of": now()}}, "rows": []})
        store.write(s)
        store.append(Disposition(id=store.mint("disposition"), session=s.id, record=decision.id, considered=True, guard_passed=True,
                                 disposition="considered-not-applicable", note="hook matched; nothing bore on it"))
    row = next(r for r in _index.competence(store) if r["record"] == decision.id)
    assert row["applied_over_considered"] == 0.0 and row["passes_in_window"] == window
    record = _consolidate.consolidate(store, force=True)
    assert record.flipped == [decision.id]
    n = next(n for n in record.nominations if n.subject == decision.id)
    assert n.outcome == "moot" and n.evidence == ["applied_over_considered=0.0"]
    flipped = store.read("decision", decision.id)
    assert flipped.status == "moot" and all(l.lifecycle.status == "settled" for l in flipped.all_latches())
    _index.regenerate(store)
    assert _lint.run(store).green
    assert decision.id not in {c["record"] for cells in _index.hooks(store).values() for c in cells}


# --- the second retirement key: the domain no longer entered ---------------------------------------

def _window_of_passes(store, n_passes: int, fault_rate_zero: bool, terms: list[str] | None = None):
    row = {"task": "count_lines", "error": None, "applied": [], "tool_errors": []} if fault_rate_zero else \
          {"task": "sum_numbers", "error": None, "applied": [], "tool_errors": [{"message": "GET /numbers failed", "cause": "HTTP 502 (transient)", "transient": True}]}
    for n in range(1, n_passes + 1):
        s = Session(id=store.mint("session"), pass_=n, started_at=now(), closed_at=now(), attached=True,
                    evaluation={"evaluation": "suite-v1", "scores": {"task_pass_rate": {"series": "suite-v1/task_pass_rate", "value": 1.0, "as_of": now()}}, "rows": [row]})
        s.work_shape.terms = terms or ["shell-tool"]
        store.write(s)


def _admit_with_moot_when(store, moot_when: str):
    d = draft(store, lifecycle={**draft(store).body.lifecycle.model_dump(by_alias=True), "moot_when": moot_when})
    entry = adjudicated_entry(store, d.uid)
    entry.verdict = "admit"
    return store.admit(d, entry, adjudicator())


def test_a_record_never_considered_over_the_window_is_nominated_and_kept_by_the_killer_item_check(store):
    decision = _admit_with_moot_when(store, "the tool layer stops exposing transient failures")
    window = store.registry.bars["retirement"]["window_passes"]
    _window_of_passes(store, window, fault_rate_zero=False)
    row = next(r for r in _index.competence(store) if r["record"] == decision.id)
    assert row["considered"] == 0 and row["applied_over_considered"] is None and row["passes_in_window"] == window
    record = _consolidate.consolidate(store, force=True)
    n = next(n for n in record.nominations if n.subject == decision.id)
    assert n.evidence == [f"considered=0 over {window} passes"] and n.outcome == "still-holds" and "not entered" in n.rung_why
    entry = next(e for e in store.all("hypothesis") if e.id == n.ledger_entry)
    assert entry.species == "currency" and entry.adjudicator.role == "adjudicator" and entry.contradiction.source.role == "oracle"
    assert entry.contradiction.coding["domain"]["fault_rate"] > 0 and "killer-item" in entry.outcome
    assert store.read("decision", decision.id).status == "accepted" and record.flipped == []


def test_a_never_considered_record_whose_moot_condition_the_window_meets_retires_on_the_verdict(store):
    decision = _admit_with_moot_when(store, "the tool layer stops exposing transient failures")
    window = store.registry.bars["retirement"]["window_passes"]
    _window_of_passes(store, window, fault_rate_zero=True)
    record = _consolidate.consolidate(store, force=True)
    n = next(n for n in record.nominations if n.subject == decision.id)
    assert n.outcome == "moot" and record.flipped == [decision.id]
    flipped = store.read("decision", decision.id)
    assert flipped.status == "moot" and all(l.lifecycle.status == "settled" for l in flipped.all_latches())
    _index.regenerate(store)
    assert _lint.run(store).green


def test_the_window_must_be_full_and_the_record_older_than_it(store):
    window = store.registry.bars["retirement"]["window_passes"]
    decision = _admit_with_moot_when(store, "the tool layer stops exposing transient failures")
    _window_of_passes(store, window - 1, fault_rate_zero=True)
    assert not [n for n in _consolidate.consolidate(store, force=True).nominations if n.subject == decision.id], "the window is not full"
    # a record admitted inside the window could not have been considered across it
    _window_of_passes(store, window, fault_rate_zero=True)
    young = _admit_with_moot_when(store, "no tool in the layer can fail")
    record = _consolidate.consolidate(store, force=True)
    assert not [n for n in record.nominations if n.subject == young.id]
