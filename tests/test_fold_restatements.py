"""Fix D: the fold nominator for near-verbatim restatements (stream-run item 33).

Split and fold run on the lineage DAG, so convergence folds records applied together; nothing folded two admitted
records with no lineage edge between them that duplicate a lesson, so a strict arm that admitted several restatements
of one lesson left the store carrying it many times and every boot carried all of them. ``index.restatements`` finds
two accepted, lineage-unrelated records that share a hook and carry payloads shaped alike, and nominates a fold —
behind the same floor and adjudication as any nomination."""

from __future__ import annotations

from hgi import consolidate as _consolidate
from hgi import index as _index
from tests.conftest import adjudicated_entry, adjudicator, decision_body, draft


def _admit(store, name: str, decision: str):
    d = draft(store, name, **decision_body(decision=decision))
    entry = adjudicated_entry(store, d.uid)
    entry.verdict = "admit"
    return store.admit(d, entry, adjudicator())


D1 = "A wrapper that retries a tool call carries the underlying cause on every rethrow."
D2 = "A wrapper that retries a tool call carries the underlying cause on each rethrow."  # near-verbatim
DISTINCT = "A paged endpoint is exhausted by following the next cursor until the page list ends."


def test_two_lineage_unrelated_alike_records_are_nominated_for_a_fold(store):
    a = _admit(store, "P-a", D1)
    b = _admit(store, "P-b", D2)
    pairs = {tuple(r["records"]) for r in _index.restatements(store)}
    assert (a.id, b.id) in pairs or (b.id, a.id) in pairs, "two alike records on the same hook fold"
    row = next(r for r in _index.restatements(store) if set(r["records"]) == {a.id, b.id})
    assert row["payload_overlap"] >= 0.6 and row["identical_hooks"], "the fold is proposed on an alike payload and a shared hook"


def test_two_genuinely_distinct_records_on_the_same_hook_are_not_folded(store):
    a = _admit(store, "P-a", D1)
    c = _admit(store, "P-c", DISTINCT)  # shares the hook (default terms) but says something else
    assert set(a.consultation_terms) & set(c.consultation_terms), "the pool is pairs that share a hook"
    assert {a.id, c.id} not in [set(r["records"]) for r in _index.restatements(store)], "different payloads do not fold"


def test_a_lineage_relation_keeps_two_records_from_being_folded(store):
    a = _admit(store, "P-a", D1)
    b = _admit(store, "P-b", D2)
    # a successor that supersedes both restates the same lesson, but a record and its successor lie in one lineage component.
    succ = draft(store, "P-succ", decision=D2, warrant={**decision_body()["warrant"], "anchors": ["O-0001"]})
    succ.supersedes[:] = [a.id, b.id]
    entry = adjudicated_entry(store, succ.uid)
    entry.verdict = "admit"
    store.admit(succ, entry, adjudicator())
    assert (a.id, b.id) in _index._lineage_related(store), "a and b now share a successor, so they are related"
    assert _index.restatements(store) == [], "no accepted pair is both alike and lineage-unrelated"
