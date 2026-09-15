"""§ 10.6 as executed operators: a fold contracts two records into one successor, a split leaves a fused record
into heirs — each a move on the lineage DAG written by the committer with reciprocal pointers, the retirees'
latches settled, and the path query reading the history back."""

from __future__ import annotations

from hgi import consolidate as _consolidate
from hgi import index as _index
from hgi import lint as _lint
from hgi.store import now
from hgi.types import Consulted, Disposition, Observation, Session
from tests.conftest import NOW, adjudicated_entry, adjudicator, decision_body, draft


def _observe(store, name: str, session: str):
    store.write(Observation(uid=store.new_uid(), name=name, noticed_at=NOW, session=session,
                            happened="the http tool's retry wrapper drops the 502 body", anchor={"path": "suite/tools.py:41"}))


def _admit(store, name: str, **overrides):
    d = draft(store, name, **overrides)
    entry = adjudicated_entry(store, d.uid)
    entry.verdict = "admit"
    return store.admit(d, entry, adjudicator())


def _pass(store, n: int, matched: dict[str, list[str]], applied: dict[str, bool]) -> Session:
    """A closed attached pass that considered each record on the given terms and disposed it applied or not."""
    s = Session(id=store.mint("session"), pass_=n, started_at=now(), closed_at=now(), attached=True,
                considered=[{"record": r, "terms_matched": t, "via": "index", "guard_passed": True, "owed_act": "apply"} for r, t in matched.items()],
                evaluation={"evaluation": "suite-v1", "scores": {k: {"series": f"suite-v1/{k}", "value": 1.0, "as_of": now()} for k in ("task_pass_rate", "error_cause_present")}, "rows": []})
    for r in matched:
        u = Disposition(id=store.mint("disposition"), session=s.id, record=r, considered=True, guard_passed=True,
                        disposition="applied" if applied[r] else "considered-not-applicable")
        store.append(u)
        s.consulted.append(Consulted(record=r, disposition=u.id))
    store.write(s)
    return s


def test_a_fold_contracts_two_records_into_one_successor(store):
    _observe(store, "O-0001", "S-0001"), _observe(store, "O-0002", "S-0002")
    a = _admit(store, "A")
    b = _admit(store, "B", decision="A retried tool call is reported with its cause when it fails again.")
    for n in range(1, 3):
        _pass(store, n, {a.id: ["http-tool"], b.id: ["http-tool"]}, {a.id: True, b.id: True})
    row = next(r for r in _index.convergence(store) if r["records"] == [a.id, b.id])
    assert row["identical_hooks"] and row["co_applied"] == 2
    record = _consolidate.consolidate(store, force=True)
    assert len(record.admitted) == 1 and sorted(record.flipped) == [a.id, b.id]
    fold = store.read("decision", record.admitted[0])
    assert fold.lineage.folded_from == [a.id, b.id] and fold.status == "accepted"
    assert "carries the underlying cause" in fold.decision and "reported with its cause" in fold.decision
    for retiree in (a, b):
        r = store.read("decision", retiree.id)
        assert r.status == "superseded" and r.lineage.superseded_by == [fold.id]
        assert all(l.lifecycle.status == "settled" for l in r.all_latches() if l.type != "wiring")
        assert [l.guard.records for l in r.latches if l.type == "wiring"] == [[fold.id]]
    paths = _index.paths_to(store, fold.id)
    assert {tuple(p[-2:]) for p in paths} == {(a.id, fold.id), (b.id, fold.id), (fold.admission.ledger_entry, fold.id)}
    assert ["O-0001", a.id, fold.id] in paths, "the history of being wrong reads back through the fold"
    _index.regenerate(store)
    assert _lint.run(store).green


def test_a_split_leaves_a_fused_record_into_heirs(store):
    _observe(store, "O-0001", "S-0001"), _observe(store, "O-0002", "S-0002")
    parent = _admit(store, "P")
    for n in range(1, 3):
        _pass(store, n, {parent.id: ["http-tool"]}, {parent.id: True})
    for n in range(3, 5):
        _pass(store, n, {parent.id: ["tool-call-retry"]}, {parent.id: False})
    row = next(r for r in _index.fusion(store) if r["record"] == parent.id)
    assert row["bimodal"] and row["applied_on"] == ["http-tool"] and row["never_on"] == ["tool-call-retry"]
    record = _consolidate.consolidate(store, force=True)
    assert len(record.admitted) == 2
    heirs = [store.read("decision", h) for h in record.admitted]
    assert all(h.lineage.split_from == parent.id and h.status == "accepted" for h in heirs)
    assert sorted(h.consultation_terms for h in heirs) == [["http-tool"], ["tool-call-retry"]]
    tombstone = store.read("decision", parent.id)
    assert tombstone.status == "superseded" and tombstone.lineage.superseded_by == record.admitted
    assert [l.guard.records for l in tombstone.latches if l.type == "wiring"] == [[h] for h in record.admitted]
    assert record.flipped == [parent.id]
    for h in heirs:
        assert any(p[-2:] == [parent.id, h.id] for p in _index.paths_to(store, h.id))
    hooks = _index.hooks(store)
    assert parent.id not in {c["record"] for cells in hooks.values() for c in cells}
    _index.regenerate(store)
    assert _lint.run(store).green


def test_a_scalar_back_pointer_reads_as_the_list_it_means(store):
    from hgi.types import Lineage
    assert Lineage(superseded_by=None).superseded_by == [] and Lineage(superseded_by="D-0003").superseded_by == ["D-0003"]


def test_a_one_record_fold_is_refused(store):
    import pytest
    with pytest.raises(ValueError, match="at least two"):
        draft(store).model_copy(update={"folded_from": ["D-0001"]}).model_validate(draft(store).model_dump(by_alias=True) | {"folded_from": ["D-0001"]})
