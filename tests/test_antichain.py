"""The antichain flag (carry-forward leftover 21): two consulted records whose hooks share every term and between which no
lineage edge runs co-apply with no specificity order; the plan prints the conflict on one line, the dispose request carries
the same reading, and nothing ranks or drops one."""

from __future__ import annotations

import json

from hgi import boot as _boot
from hgi import close as _close
from hgi import model as _model
from hgi.store import now
from hgi.types import Considered, Consulted, Session
from tests.conftest import adjudicated_entry, adjudicator, decision_body, draft


def _admit(store, name, terms, **overrides):
    body = decision_body(**overrides)
    body["latches"][0]["guard"]["terms"] = terms
    d = draft(store, name, **body)
    entry = adjudicated_entry(store, d.uid)
    entry.verdict = "admit"
    return store.admit(d, entry, adjudicator())


def test_identical_hooks_with_no_lineage_edge_co_apply(store):
    a = _admit(store, "A", ["http-tool", "tool-call-retry"])
    b = _admit(store, "B", ["tool-call-retry", "http-tool"], decision="A retried call is reported with its cause.")
    c = _admit(store, "C", ["shell-tool"])
    assert _boot.co_applying(store, [a.id, b.id, c.id]) == [[a.id, b.id]]
    assert _boot.co_applying(store, [a.id, c.id]) == []


def test_a_supersedure_is_a_specificity_order_and_is_not_flagged(store):
    a = _admit(store, "A", ["http-tool"])
    d = draft(store, "S", **{**decision_body(), "latches": [{**l, "guard": {**l["guard"], "terms": ["http-tool"]}} if l["type"] == "consultation" else l for l in decision_body()["latches"]]})
    d = d.model_copy(update={"supersedes": [a.id]})
    entry = adjudicated_entry(store, d.uid)
    entry.verdict = "admit"
    s = store.admit(d, entry, adjudicator())
    assert _boot.lineage_edge(store.read("decision", a.id), s) and _boot.co_applying(store, [a.id, s.id]) == []


def test_the_plan_prints_the_conflict_on_one_line_and_keeps_both(store):
    a = _admit(store, "A", ["http-tool"])
    b = _admit(store, "B", ["http-tool"], decision="A retried call is reported with its cause.")
    session = Session(id="S-0001", pass_=1, started_at=now(), work_shape={"terms": ["http-tool"]},
                      considered=[Considered(record=r, terms_matched=["http-tool"], via="index", guard_passed=True, owed_act="apply") for r in (a.id, b.id)])
    text = _boot.plan(store, session, store.articles(), None, [])
    assert f"co-applying: {a.id}, {b.id} — no specificity order; dispose each on its own rows" in text.splitlines()
    assert f"consulting 2: {a.id} (http-tool) owed apply, {b.id} (http-tool) owed apply" in text


def test_the_dispose_request_carries_the_same_reading(store, monkeypatch):
    a = _admit(store, "A", ["http-tool"])
    b = _admit(store, "B", ["http-tool"], decision="A retried call is reported with its cause.")
    seen = []
    real = _model.complete

    def spy(role, payload, **kw):
        seen.append(json.loads(payload))
        return real(role, payload, **kw)

    monkeypatch.setattr(_model, "complete", spy)
    session = Session(id="S-0001", pass_=1, started_at=now(), consulted=[Consulted(record=a.id), Consulted(record=b.id)],
                      evaluation={"evaluation": "suite-v1", "scores": {}, "rows": [{"task": "t", "error": None, "applied": [a.id]}]})
    dispositions = _close.dispose(store, session)
    req = next(r for r in seen if r["request"] == "dispose")
    assert req["co_applying"] == [{"records": [a.id, b.id], "reading": _boot.CO_APPLYING}]
    assert {u.record: u.disposition for u in dispositions} == {a.id: "applied", b.id: "considered-not-applicable"}, "each disposed on its own rows"
