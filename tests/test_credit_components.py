"""Itemized, never net (doctrine § 13): a computed aggregate ships its components, and they sum to it."""

from __future__ import annotations

from hgi import consolidate as _consolidate
from tests.test_slice3 import CLEAN, FAULTED, _session


def test_credit_rows_carry_the_counts_their_fractions_are_computed_from(store):
    _session(store, 1, [FAULTED, {**CLEAN, "task": "other_task"}], {"task_pass_rate": 0.5})
    s2 = _session(store, 2, [{**FAULTED, "applied": ["D-0001"]}, {**CLEAN, "applied": ["D-0001"]}], {"task_pass_rate": 0.5})
    from tests.conftest import adjudicated_entry, adjudicator, draft
    d = draft(store)
    entry = adjudicated_entry(store, d.uid)
    entry.verdict = "admit"
    store.admit(d, entry, adjudicator())
    [row] = _consolidate.credit_table(store, [s2])
    assert row["after_rows"] == 2 and row["after_passed"] == 1 and row["after"] == row["after_passed"] / row["after_rows"]
    assert row["before_rows"] == 1 and row["before_passed"] == 0 and row["before"] == 0.0
