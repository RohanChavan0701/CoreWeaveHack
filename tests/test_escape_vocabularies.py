"""Carry-forward item 12 — escape recurrence across closed vocabularies.

The recurrence counter clustered only the sessions' work-shape escapes. The
escapes of any closed vocabulary are kept where that vocabulary is written —
a latch key-space on the record that carries it, a verdict on the ledger
entry that carries it — and cluster the same way. The review is called for
each of them, not for work-shape alone.
"""

from __future__ import annotations

from hgi import consolidate as _consolidate
from hgi import reviews as _reviews
from hgi.store import now
from hgi.types import Consolidation, LedgerEntry, RoleCall
from tests.conftest import decision_body, draft


def _record(store) -> Consolidation:
    return Consolidation(id=store.mint("consolidation"), started_at=now(), after_pass=2, sessions_read=[])


def _escape_latch(key_space: str) -> dict:
    return {"type": "revisit", "slot": "warrant", "key_space": key_space, "edge": {"kind": "schedule", "at": "consolidation"},
            "guard": {}, "consumer": "the backward pass", "owed_act": {"class": "re-adjudicate", "role": "dispositive"},
            "lifecycle": {"status": "live"}}


def _draft_with_key_space(store, name: str, key_space: str):
    body = decision_body()
    body["latches"].append(_escape_latch(key_space))
    d = draft(store, name=name, latches=body["latches"])
    store.write_draft(d)
    return d


def _verdict_entry(store, verdict: str) -> LedgerEntry:
    entry = LedgerEntry(id=store.mint("hypothesis"), at=now(), species="currency", subject="D-0001",
                        claim="a warrant re-checked against a fire", proposer=RoleCall(role="consolidator", model_id=None, call=None),
                        contradiction={"source": {"role": "adjudicator", "model_id": "stub", "call": "weave:///t/c"}, "coding": {}},
                        verdict=verdict, adjudicator=RoleCall(role="adjudicator", model_id="stub", call="weave:///t/c"))
    store.append(entry)
    return entry


# --- clustering on a second vocabulary --------------------------------------------------------

def test_reviewable_vocabularies_reaches_beyond_work_shape(store):
    vocabs = _reviews.reviewable_vocabularies(store)
    assert "work-shape" in vocabs and "key-space" in vocabs and "currency-verdict" in vocabs


def test_latch_key_space_escapes_cluster_across_records(store):
    d1 = _draft_with_key_space(store, "P-a", "other(diff-tool)")
    d2 = _draft_with_key_space(store, "P-b", "other(Diff Tool)")
    (cluster,) = _reviews.escape_clusters(store, "key-space")
    assert cluster["vocabulary"] == "key-space" and cluster["term"] == "diff-tool"
    idx = len(decision_body()["latches"])  # the appended escape latch's index in all_latches()
    assert cluster["sessions"] == [f"{d1.uid}#{idx}", f"{d2.uid}#{idx}"]
    assert _reviews.escape_clusters(store, "work-shape") == [], "the key-space escape is not a work-shape escape"


def test_verdict_escapes_cluster_across_ledger_entries(store):
    e1 = _verdict_entry(store, "other(partial-reversal)")
    e2 = _verdict_entry(store, "other(partial reversal)")
    (cluster,) = _reviews.escape_clusters(store, "currency-verdict")
    assert cluster["term"] == "partial-reversal" and cluster["sessions"] == [e1.id, e2.id]


# --- the review runs for the second vocabulary ------------------------------------------------

def test_a_recurring_key_space_escape_grows_the_key_space_vocabulary(store):
    _draft_with_key_space(store, "P-a", "other(diff-tool)")
    _draft_with_key_space(store, "P-b", "other(diff-tool)")
    record = _record(store)
    noms = _reviews.vocabulary(store, record, "key-space")
    n = next(n for n in noms if n.subject == "key-space/diff-tool")
    assert n.outcome == "minted key-space/diff-tool" and record.minted == ["key-space/diff-tool"]
    assert "diff-tool" in store.registry.terms("key-space")


def test_a_routed_verdict_vocabulary_is_surfaced_but_not_grown_without_a_route(store):
    _verdict_entry(store, "other(partial-reversal)")
    _verdict_entry(store, "other(partial-reversal)")
    record = _record(store)
    n = next(n for n in _reviews.vocabulary(store, record, "currency-verdict") if n.subject == "currency-verdict/partial-reversal")
    assert "routed" in n.outcome and record.minted == []
    assert "partial-reversal" not in store.registry.terms("currency-verdict")


def test_the_default_review_runs_every_reviewable_vocabulary(store):
    _draft_with_key_space(store, "P-a", "other(diff-tool)")
    _draft_with_key_space(store, "P-b", "other(diff-tool)")
    record = _record(store)
    noms = _reviews.vocabulary(store, record)  # no vocab named: every reviewable one
    assert any(n.subject == "key-space/diff-tool" for n in noms)
    assert record.minted == ["key-space/diff-tool"]
