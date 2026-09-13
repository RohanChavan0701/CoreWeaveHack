"""A consolidation names a record once in ``flipped`` however many currency verdicts reverse it: five fires on one
premise of one decision are five ledger entries and one flip, not five entries in the list and a commit message that
repeats the id (seen on runs/reasoning-core/qwen-strict, K-0003)."""

from __future__ import annotations

from hgi import consolidate as _consolidate
from hgi.store import now
from hgi.types import Consolidation
from tests.conftest import adjudicated_entry
from tests.test_settlement import _admit


def _entry(store, d, verdict: str):
    """A currency entry on the ledger with the adjudicator's verdict stamped, as ask_currency leaves it."""
    entry = adjudicated_entry(store, d.id).model_copy(update={"species": "currency", "verdict": verdict})
    store.append(entry)
    return entry


def test_two_reversed_verdicts_on_one_record_leave_one_entry_in_flipped(store):
    d = _admit(store)
    record = Consolidation(id=store.mint("consolidation"), started_at=now(), after_pass=2, sessions_read=[])
    for _ in range(2):
        outcome = _consolidate.settle_currency(store, record, d, {"premise": "p1"}, _entry(store, d, "reversed"))
        assert outcome == f"reversed: premise p1 of {d.id} reversed"
    assert record.flipped == [d.id]
    assert next(p for p in store.read("decision", d.id).warrant.premises if p.id == "p1").status == "reversed"


def test_a_moot_verdict_does_not_repeat_a_record_the_consolidation_already_names(store):
    d = _admit(store)
    record = Consolidation(id=store.mint("consolidation"), started_at=now(), after_pass=2, sessions_read=[], flipped=[d.id])
    assert _consolidate.settle_currency(store, record, d, {}, _entry(store, d, "moot")) == f"moot: {d.id} flipped moot"
    assert record.flipped == [d.id] and store.read("decision", d.id).status == "moot"
