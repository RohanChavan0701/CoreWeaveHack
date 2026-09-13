"""The ladder's rungs and their operators (spec § 10.3): in a decisions-only roster a nomination at a rung with no operator
is carried as a decision — the cheapest available home — with the rung it meant recorded on the nomination, the draft and
the admitted record, never refused and never silently re-labelled."""

from __future__ import annotations

from hgi import consolidate as _consolidate
from hgi import stub
from tests.test_slice3 import FAULTED, NO_CAUSE, _observe, _session


def test_a_rule_shaped_lesson_is_carried_as_a_decision_that_records_its_displacement(store, monkeypatch):
    s1 = _session(store, 1, [FAULTED], {"task_pass_rate": 0.5, "error_cause_present": 0.0})
    s2 = _session(store, 2, [FAULTED], {"task_pass_rate": 0.5, "error_cause_present": 0.0})
    o1, o2 = _observe(store, s1, NO_CAUSE), _observe(store, s2, NO_CAUSE)
    real = stub.HANDLERS["nominate"]

    def as_rule(req):
        out = real(req)
        for n in out["nominations"]:
            n["rung"], n["rung_why"] = "rule-enrollment", "a duty that binds on every tool failure"
        return out

    monkeypatch.setitem(stub.HANDLERS, "nominate", as_rule)
    record = _consolidate.consolidate(store)
    assert record.admitted == ["D-0001"], "the lesson is not lost to the missing tier"
    n = next(n for n in record.nominations if n.subject == "cause")
    assert n.rung == "new-decision" and n.displaced_from == "rule-enrollment" and n.rung_why.startswith("displaced from rule-enrollment")
    d = store.read("decision", "D-0001")
    assert d.admission.rung == "new-decision" and d.admission.displaced_from == "rule-enrollment"
    assert {o.disposition.pointer for o in store.observations(state=None)} == {"D-0001"}


def test_a_nomination_with_no_sketch_is_still_refused_at_parse(store, monkeypatch):
    _session(store, 1, [FAULTED], {"task_pass_rate": 0.5}), _session(store, 2, [FAULTED], {"task_pass_rate": 0.5})
    monkeypatch.setattr(_consolidate, "nominate", lambda store, record, brief: [{"rung": "floor", "rung_why": "x", "subject": "floor", "evidence": [], "supersedes": []}])
    record = _consolidate.consolidate(store)
    n = next(n for n in record.nominations if n.subject == "floor")
    assert n.displaced_from == "floor" and n.outcome.startswith("draft refused at parse") and store.drafts() == []


def test_the_operated_rungs_are_the_case_leg():
    assert _consolidate.displacement("new-decision") is None and _consolidate.displacement("hook-edit") is None
    assert _consolidate.displacement("article") == "article" and _consolidate.displacement("adoption-row") == "adoption-row"


def test_an_edit_rung_with_no_record_to_edit_lands_as_a_new_decision(store, monkeypatch):
    s1 = _session(store, 1, [FAULTED], {"task_pass_rate": 0.5, "error_cause_present": 0.0})
    s2 = _session(store, 2, [FAULTED], {"task_pass_rate": 0.5, "error_cause_present": 0.0})
    _observe(store, s1, NO_CAUSE), _observe(store, s2, NO_CAUSE)
    real = stub.HANDLERS["nominate"]

    def as_orphan_edit(req):  # an edit rung that names no record, on a store that holds none to edit
        out = real(req)
        for n in out["nominations"]:
            n["rung"], n["rung_why"], n["supersedes"] = "counterfactual-edit", "an edit with nothing yet to refine", []
        return out

    monkeypatch.setitem(stub.HANDLERS, "nominate", as_orphan_edit)
    assert store.decisions() == [], "the store holds no record the edit could supersede"
    record = _consolidate.consolidate(store)
    assert record.admitted == ["D-0001"], "the orphan edit is carried as a decision, not refused at parse"
    n = next(n for n in record.nominations if n.subject == "cause")
    assert n.rung == "new-decision" and n.displaced_from == "counterfactual-edit"
    assert "holds none to edit" in n.rung_why and n.rung_why.startswith("displaced from counterfactual-edit")
    d = store.read("decision", "D-0001")
    assert d.admission.rung == "new-decision" and d.admission.displaced_from == "counterfactual-edit"


def test_an_edit_rung_that_names_no_record_when_records_exist_is_refused(store, monkeypatch):
    from tests.conftest import adjudicated_entry, adjudicator, decision_body, draft
    d0 = draft(store, "P", **decision_body(decision="A batched write is flushed on a size threshold, never on a timer."))
    entry0 = adjudicated_entry(store, d0.uid)
    entry0.verdict = "admit"
    store.admit(d0, entry0, adjudicator())  # a record the store holds; the edit still names none
    s1 = _session(store, 1, [FAULTED], {"task_pass_rate": 0.5, "error_cause_present": 0.0})
    s2 = _session(store, 2, [FAULTED], {"task_pass_rate": 0.5, "error_cause_present": 0.0})
    _observe(store, s1, NO_CAUSE), _observe(store, s2, NO_CAUSE)
    real = stub.HANDLERS["nominate"]

    def as_orphan_edit(req):
        out = real(req)
        for n in out["nominations"]:
            n["rung"], n["rung_why"], n["supersedes"] = "counterfactual-edit", "an edit naming nothing", []
        return out

    monkeypatch.setitem(stub.HANDLERS, "nominate", as_orphan_edit)
    record = _consolidate.consolidate(store)
    n = next(n for n in record.nominations if n.subject == "cause")
    assert n.displaced_from is None and n.outcome.startswith("draft refused at parse"), "an edit that names no record when records exist is refused"
