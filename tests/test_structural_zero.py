"""The structural-zero audit nominates, and the slot-local rungs execute: a record keyed only on an escape is reached by
no hook; the consolidator re-keys it as a hook-edit successor derived from the record it supersedes, and a
counterfactual-edit lands the same way — a refinement is a successor record, never a rewrite."""

from __future__ import annotations

import pytest

from hgi import consolidate as _consolidate
from hgi import index as _index
from hgi import lint as _lint
from hgi import stub
from tests.conftest import adjudicated_entry, adjudicator, decision_body, draft
from tests.test_lineage_ops import _observe, _pass


def _admit_on(store, terms: list[str]):
    body = decision_body()
    body["latches"][0]["guard"]["terms"] = terms
    d = draft(store, "Z", **body)
    entry = adjudicated_entry(store, d.uid)
    entry.verdict = "admit"
    return store.admit(d, entry, adjudicator())


def test_an_escape_keyed_record_is_a_structural_zero_and_is_re_keyed(store):
    _observe(store, "O-0001", "S-0001"), _observe(store, "O-0002", "S-0002")
    zero = _admit_on(store, ["other(streaming-tool)"])
    assert _index.hooks(store) == {} and _index.structural_zero(store) == [zero.id]
    for n in (1, 2):
        s = _pass(store, n, {}, {})
        s.work_shape.terms = ["http-tool", "tool-call-retry"]
        store.write(s)
    record = _consolidate.consolidate(store, force=True)
    n = next(x for x in record.nominations if x.rung == "hook-edit")
    assert n.subject == f"zero:{zero.id}" and n.outcome.startswith("admitted")
    successor = store.read("decision", record.admitted[0])
    assert successor.lineage.supersedes == [zero.id] and set(successor.consultation_terms) == {"http-tool", "tool-call-retry"}
    assert successor.decision == zero.decision and successor.counterfactual == zero.counterfactual, "only the activation slot changed"
    assert store.read("decision", zero.id).status == "superseded" and _index.structural_zero(store) == []
    assert successor.id in {c["record"] for c in _index.hooks(store)["http-tool"]}
    _index.regenerate(store)
    assert _lint.run(store).green


def test_a_counterfactual_edit_derives_its_body_from_the_record_it_supersedes(store, monkeypatch):
    _observe(store, "O-0001", "S-0001"), _observe(store, "O-0002", "S-0002")
    original = _admit_on(store, ["http-tool"])
    for n in (1, 2):
        _pass(store, n, {}, {})
    edited = "The overshoot is a wrapper that retries a 404 as if it were transient — observed in O-0002."
    monkeypatch.setitem(stub.HANDLERS, "nominate", lambda req: {"nominations": [
        {"rung": "counterfactual-edit", "rung_why": "the counterfactual was authored from imagination; O-0002 anchors the real overshoot",
         "subject": "cf", "evidence": [], "supersedes": [original.id], "edit": {"counterfactual": edited}, "body": None}]})
    record = _consolidate.consolidate(store, force=True)
    successor = store.read("decision", record.admitted[0])
    assert successor.counterfactual == edited and successor.decision == original.decision and successor.consultation_terms == ["http-tool"]
    assert store.read("decision", original.id).lineage.superseded_by == [successor.id]


def test_an_edit_rung_needs_one_predecessor_and_a_field_it_may_change(store):
    _observe(store, "O-0001", "S-0001"), _observe(store, "O-0002", "S-0002")
    original = _admit_on(store, ["http-tool"])
    with pytest.raises(ValueError, match="exactly one record"):
        _consolidate.edited_body(store, {"rung": "hook-edit", "supersedes": [], "edit": {"terms": ["http-tool"]}})
    with pytest.raises(ValueError, match="at least one of"):
        _consolidate.edited_body(store, {"rung": "hook-edit", "supersedes": [original.id], "edit": {"counterfactual": "not a hook field"}})
    body = _consolidate.edited_body(store, {"rung": "hook-edit", "supersedes": [original.id], "edit": {"terms": ["shell-tool"], "not_this": ["a mocked tool"]}})
    assert body["latches"][0]["guard"] == {**body["latches"][0]["guard"], "terms": ["shell-tool"], "not_this": ["a mocked tool"]} and body["summary"]["not_this"] == ["a mocked tool"]
