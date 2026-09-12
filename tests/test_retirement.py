"""The retirement leg: a decision considered but never applied over the review window is nominated by its
ratio, judged moot by the adjudicator, and flipped with its latches settled — the lint stays green."""

from __future__ import annotations

from hgi import consolidate as _consolidate
from hgi import index as _index
from hgi import lint as _lint
from hgi.store import now
from hgi.types import Disposition, Session
from tests.conftest import adjudicated_entry, adjudicator, draft


def test_never_applied_decision_retires_on_telemetry(store):
    d = draft(store)
    entry = adjudicated_entry(store, d.uid)
    entry.verdict = "admit"
    decision = store.admit(d, entry, adjudicator())
    window = store.registry.bars["retirement"]["window_passes"]
    for n in range(1, window + 1):
        s = Session(id=store.mint("session"), pass_=n, started_at=now(), closed_at=now(), attached=True,
                    evaluation={"evaluation": "suite-v1", "scores": {"task_pass_rate": {"series": "suite-v1/task_pass_rate", "value": 0.5, "as_of": now()}}, "rows": []})
        store.write(s)
        store.append(Disposition(id=store.mint("disposition"), session=s.id, record=decision.id, considered=True, guard_passed=True,
                                 disposition="considered-not-applicable", note="hook matched; nothing bore on it"))
    row = next(r for r in _index.competence(store) if r["record"] == decision.id)
    assert row["applied_over_considered"] == 0.0 and row["passes_in_window"] == window
    record = _consolidate.consolidate(store, force=True)
    assert record.flipped == [decision.id]
    n = record.nominations[-1]
    assert n.subject == decision.id and n.outcome == "moot" and n.evidence == ["applied_over_considered=0.0"]
    flipped = store.read("decision", decision.id)
    assert flipped.status == "moot" and all(l.lifecycle.status == "settled" for l in flipped.all_latches())
    _index.regenerate(store)
    assert _lint.run(store).green
    assert decision.id not in {c["record"] for cells in _index.hooks(store).values() for c in cells}
