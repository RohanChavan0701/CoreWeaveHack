"""Two attack classes are the code's, not a lens's (``hgi.types.MECHANICAL``): the independence of a draft's evidence is
the floor's count against the bar, and a watch that fires on success is dropped from the draft before any context opens.
L-0005 and L-0008 are seeded retired through the crystallization door; an examiner claim on either class that contradicts
the computed reading is discarded."""

from __future__ import annotations

from hgi import consolidate as _consolidate
from hgi import lint as _lint
from hgi.store import now
from hgi.types import MECHANICAL, Consolidation, Nomination
from tests.conftest import draft
from tests.test_slice3 import FAULTED, NO_CAUSE, _observe, _session


def _record(store) -> Consolidation:
    return Consolidation(id=store.mint("consolidation"), started_at=now(), after_pass=2, sessions_read=["S-0001"])


def test_the_crystallized_angles_are_kept_in_the_register_and_walked_by_nothing(store):
    live = {l.id for l in store.registry.lenses("examiner")}
    every = {l.id: l for l in store.registry.lenses(status=None)}
    assert live == {"L-0006", "L-0007"} and {"L-0005", "L-0008"} <= set(every)
    for lens_id in ("L-0005", "L-0008"):
        assert every[lens_id].status == "retired" and every[lens_id].warrant.evidence.startswith("crystallized")
        assert set(every[lens_id].claims) <= set(MECHANICAL)
    assert not any(f.check == "genesis-anchor" and f.record in ("L-0005", "L-0008") for f in _lint.run(store).findings)


def test_evidence_from_one_session_counted_twice_is_refused_by_the_floor_not_by_a_verdict(store):
    s1 = _session(store, 1, [FAULTED], {"task_pass_rate": 0.5, "error_cause_present": 0.0})
    o1, o2 = _observe(store, s1, NO_CAUSE), _observe(store, s1, NO_CAUSE)
    d = draft(store).model_copy(update={"evidence": [o1.name, o2.name]})
    store.write_draft(d)
    nomination = Nomination(rung="new-decision", rung_why="a test", subject="cause", evidence=[o1.name, o2.name], draft=d.uid)
    entry = _consolidate.adjudicate(store, _record(store), nomination, d, {"scores": {}})
    assert entry.outcome == "refused by the floor: 1 distinct session(s) in the evidence (S-0001) against the bar 2"
    assert entry.verdict == "survived-with-attack-named", "the adjudicator admitted; the count is the floor's, never a decline"
    claim = next(c for c in entry.contradiction.attack.claims if c.target == "warrant:independence")
    assert claim.landed is True and claim.lens is None and claim.evidence == ["1 distinct session(s) in the evidence (S-0001) against the bar 2"]
    assert store.drafts() == [] and store.decisions() == []
    assert _lint.independence(store, d).check == "independence"


def test_evidence_from_two_sessions_meets_the_bar_and_the_claim_names_the_sessions(store):
    s1 = _session(store, 1, [FAULTED], {"task_pass_rate": 0.5, "error_cause_present": 0.0})
    s2 = _session(store, 2, [FAULTED], {"task_pass_rate": 0.5, "error_cause_present": 0.0})
    o1, o2 = _observe(store, s1, NO_CAUSE), _observe(store, s2, NO_CAUSE)
    d = draft(store).model_copy(update={"evidence": [o1.name, o2.name]})
    assert _lint.independence(store, d) is None and store.draft_sessions(d) == ["S-0001", "S-0002"]
    claim = _consolidate.independence_claim(store, d, _consolidate.evidence_pack(store, d, {"scores": {}}))
    assert claim["landed"] is False and claim["evidence"] == ["sessions ['S-0001', 'S-0002'] meet the bar 2"]


def test_an_examiner_claim_that_contradicts_the_computed_reading_is_discarded_and_an_agreeing_one_kept():
    mechanical = [{"target": "warrant:independence", "landed": False, "lens": None, "call": None, "reading_taken": True, "refutation": "r", "evidence": ["2 of 2"]},
                  {"target": "warrant:watch-direction", "landed": True, "lens": None, "call": None, "reading_taken": True, "refutation": "r", "evidence": ["dropped"]}]
    examiner = {"claims": [{"target": "warrant:independence", "landed": True, "lens": "L-0005", "call": "c1"},   # contradicts the count: discarded
                           {"target": "warrant:watch-direction", "landed": True, "lens": "L-0008", "call": "c2"},  # agrees: kept, advisory
                           {"target": "premise:p1", "landed": True, "lens": "L-0006", "call": "c3"}], "verdict": "pending"}
    settled = _consolidate.settle(examiner, mechanical)
    assert settled["verdict"] == "pending"
    assert [(c["target"], c.get("lens")) for c in settled["claims"]] == [
        ("warrant:independence", None), ("warrant:watch-direction", None), ("warrant:watch-direction", "L-0008"), ("premise:p1", "L-0006")]
