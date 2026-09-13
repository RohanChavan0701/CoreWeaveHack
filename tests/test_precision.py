"""The first slot signature (§ 10.5, activation — precision): fired-but-not-applicable dominating a record's considered
count is its own competence column and a brief row; the consolidator grows ``not_this`` by the presentations the
dispositions' notes name, as a ``counterfactual-edit`` successor — the hook stays, the guard tightens."""

from __future__ import annotations

from hgi import consolidate as _consolidate
from hgi import index as _index
from hgi import lint as _lint
from hgi.store import now
from hgi.types import Consulted, Disposition, Session
from tests.conftest import adjudicated_entry, adjudicator, decision_body, draft
from tests.test_lineage_ops import _observe


def _admit(store):
    d = draft(store, "P", **decision_body())
    entry = adjudicated_entry(store, d.uid)
    entry.verdict = "admit"
    return store.admit(d, entry, adjudicator())


def _pass(store, n: int, record: str, disposition: str, note: str) -> Session:
    s = Session(id=store.mint("session"), pass_=n, started_at=now(), closed_at=now(), attached=True,
                considered=[{"record": record, "terms_matched": ["http-tool"], "via": "index", "guard_passed": True, "owed_act": "apply"}],
                evaluation={"evaluation": "suite-v1", "scores": {k: {"series": f"suite-v1/{k}", "value": 1.0, "as_of": now()} for k in ("task_pass_rate", "error_cause_present")}, "rows": []})
    u = Disposition(id=store.mint("disposition"), session=s.id, record=record, considered=True, guard_passed=True, disposition=disposition, note=note)
    store.append(u)
    s.consulted = [Consulted(record=record, disposition=u.id)]
    store.write(s)
    return s


def test_not_applicable_is_its_own_competence_column_and_seeds_the_precision_row(store):
    _observe(store, "O-0001", "S-0001"), _observe(store, "O-0002", "S-0002")
    d = _admit(store)
    _pass(store, 1, d.id, "considered-not-applicable", "hook matched the pass's presentation and no task bore on it: status_ok, schema_answer")
    _pass(store, 2, d.id, "applied", "applied on fetch_user_name")
    _pass(store, 3, d.id, "considered-not-applicable", "hook matched the pass's presentation and no task bore on it: status_ok")
    [row] = _index.competence(store)
    assert row["considered"] == 3 and row["applied"] == 1 and row["not_applicable"] == 2 and row["guard_failed"] == 0
    [p] = _index.precision(store)
    assert p["record"] == d.id and p["not_applicable_over_considered"] == 2 / 3 and p["bar"] == 0.5
    assert [n["session"] for n in p["notes"]] == ["S-0001", "S-0003"] and p["not_this"] == ["reasoning-loop-retry"]
    assert store.registry.bars["precision"]["not_applicable_over_considered_above"] == 0.5


def test_below_the_bar_no_precision_row(store):
    _observe(store, "O-0001", "S-0001"), _observe(store, "O-0002", "S-0002")
    d = _admit(store)
    _pass(store, 1, d.id, "applied", "applied on fetch_user_name")
    _pass(store, 2, d.id, "applied", "applied on fetch_user_name")
    _pass(store, 3, d.id, "considered-not-applicable", "hook matched the pass's presentation and no task bore on it: status_ok")
    assert _index.precision(store) == []


def test_the_consolidator_grows_not_this_as_a_counterfactual_edit_successor(store):
    _observe(store, "O-0001", "S-0001"), _observe(store, "O-0002", "S-0002")
    d = _admit(store)
    _pass(store, 1, d.id, "considered-not-applicable", "hook matched the pass's presentation and no task bore on it: status_ok, schema_answer")
    _pass(store, 2, d.id, "considered-not-applicable", "hook matched the pass's presentation and no task bore on it: status_ok")
    record = _consolidate.consolidate(store, force=True)
    assert [r["record"] for r in record.brief["precision"]] == [d.id]
    n = next(x for x in record.nominations if x.subject == f"precision:{d.id}")
    assert n.rung == "counterfactual-edit" and n.evidence == ["S-0001", "S-0002"] and n.outcome.startswith("admitted")
    successor = store.read("decision", record.admitted[0])
    assert successor.lineage.supersedes == [d.id] and successor.consultation_terms == d.consultation_terms, "the hook stays"
    assert successor.consultation_not_this == ["reasoning-loop-retry", "status_ok", "schema_answer"]
    assert successor.summary.not_this == successor.consultation_not_this and successor.decision == d.decision
    assert store.read("decision", d.id).status == "superseded"
    _index.regenerate(store)
    assert _lint.run(store).green


def test_one_pass_of_not_applicable_is_one_datum(store):
    _observe(store, "O-0001", "S-0001"), _observe(store, "O-0002", "S-0002")
    d = _admit(store)
    _pass(store, 1, d.id, "considered-not-applicable", "hook matched the pass's presentation and no task bore on it: status_ok")
    record = _consolidate.consolidate(store, force=True)
    assert not [x for x in record.nominations if x.subject.startswith("precision:")]


def test_a_record_at_its_retirement_door_is_the_retirement_legs_not_precisions(store):
    _observe(store, "O-0001", "S-0001"), _observe(store, "O-0002", "S-0002")
    d = _admit(store)
    for n in range(1, store.registry.bars["retirement"]["window_passes"] + 1):
        _pass(store, n, d.id, "considered-not-applicable", "hook matched the pass's presentation and no task bore on it: status_ok")
    assert _index.precision(store) == []
