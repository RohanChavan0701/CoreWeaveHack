"""Every verdict a vocabulary admits has an act at every seam that reads it: the route tables are closed, a term with no
route is a test failure, and a verdict reaching a seam without one is refused loud rather than falling through."""

from __future__ import annotations

import pytest

from hgi import consolidate as _consolidate
from hgi import registry as _registry
from hgi import reviews as _reviews
from hgi import stub
from tests.test_slice3 import FAULTED, NO_CAUSE, _observe, _session


def test_every_route_table_covers_its_vocabulary_and_the_escape(store):
    assert {seam for seam, _, _ in _registry.ROUTE_TABLES} >= {"adjudication", "attack-ledger", "human-queue", "currency", "genesis-anchor", "vocabulary"}
    for seam, vocab, table in _registry.ROUTE_TABLES:
        assert store.registry.unrouted(vocab, table) == [], f"{seam} leaves {store.registry.unrouted(vocab, table)} of {vocab} without an act"
        assert "other" in table, f"{seam} routes the escape"


def test_a_term_added_without_a_route_is_named_and_refused(store):
    store.registry.add_term("currency-verdict", "void", "the reading could not be taken", since="2026-09-12")
    assert store.registry.unrouted("currency-verdict", _consolidate.CURRENCY) == ["void"]
    with pytest.raises(_registry.Unrouted, match="'void' has no route"):
        store.registry.route("currency-verdict", "void", _consolidate.CURRENCY)
    assert store.registry.route("currency-verdict", "other(unreadable)", _consolidate.CURRENCY) == "stand"
    with pytest.raises(ValueError, match="closed vocabulary"):
        store.registry.route("currency-verdict", "admit", _consolidate.CURRENCY)


def test_a_human_deferral_requeues_and_a_human_escalation_keeps_the_entry(store, monkeypatch):
    s1 = _session(store, 1, [FAULTED], {"task_pass_rate": 0.5, "error_cause_present": None})
    s2 = _session(store, 2, [FAULTED], {"task_pass_rate": 0.5, "error_cause_present": None})
    _observe(store, s1, NO_CAUSE), _observe(store, s2, NO_CAUSE)
    _consolidate.consolidate(store)
    (q,) = store.queue()
    assert _consolidate.resolve(store, q.draft.uid, "escalate(still unsure)").startswith("kept on the queue") and len(store.queue()) == 1
    assert store.all("hypothesis")[-1].verdict == "pending" and store.all("hypothesis")[-1].adjudicator.role == "human"
    outcome = _consolidate.resolve(store, q.draft.uid, "defer(until the scorer runs)")
    assert outcome.startswith("deferred; re-queued with its condition as a latch") and store.queue() == []
    (p,) = store.drafts()
    assert p.deferral and p.deferral.until.edge.kind == "schedule" and p.deferral.after_pass == 2


def test_the_vocabulary_seam_waits_on_a_deferred_term(store, monkeypatch):
    from tests.test_vocabulary import _escaping
    _escaping(store, 1, "other(streaming-tool)"), _escaping(store, 2, "other(streaming-tool)")
    monkeypatch.setitem(stub.HANDLERS, "vocabulary", lambda req: {"verdict": "defer(until a third pass escapes)", "means": None})
    record = _consolidate.consolidate(store)
    n = next(n for n in record.nominations if n.subject == "work-shape/streaming-tool")
    assert n.outcome.endswith("; waits for new recurrence") and record.minted == [] and _reviews.escape_clusters(store) == []
