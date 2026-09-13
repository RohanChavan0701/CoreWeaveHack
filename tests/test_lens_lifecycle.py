"""The lens tier's lifecycle (doctrine § 7.4, the crystallization law; § 14.1's lens column): a lens's warrant is its effect
evidence, derived from the products that reached a consumer; a seed lens unanchored past the deadline, or a lens whose
product stopped varying, is nominated to the adjudicator and retired on ``moot``."""

from __future__ import annotations

from hgi import boot as _boot
from hgi import consolidate as _consolidate
from hgi import lint as _lint
from hgi import reviews as _reviews
from hgi.types import LensAnswer, Observation
from hgi.store import now
from tests.test_slice3 import CLEAN, FAULTED, NO_CAUSE, NOT_RETRIED, _observe, _session


def _lens_of(store, lens_id):
    return next(l for l in store.registry.lenses(status=None) if l.id == lens_id)


def _walk(store, s, lens_id, findings, call=None):
    s.lens_answers.append(LensAnswer(lens=lens_id, answer="", findings=findings, call=call))
    store.write(s)


def test_a_close_lens_is_anchored_to_the_observation_it_filed_once_the_backward_pass_consumed_it(store):
    s1 = _session(store, 1, [FAULTED], {"task_pass_rate": 0.5, "error_cause_present": 0.0})
    s2 = _session(store, 2, [FAULTED], {"task_pass_rate": 0.5, "error_cause_present": 0.0})
    for s in (s1, s2):
        o = _observe(store, s, NO_CAUSE)
        _walk(store, s, "L-0004", [{"noticed": o.noticed, "anchor": {"path": "suite/tools.py:54"}}])
    assert _lens_of(store, "L-0004").warrant.anchors == []
    record = _consolidate.consolidate(store)
    assert record.admitted == ["D-0001"] and "L-0004" in record.anchored
    assert set(_lens_of(store, "L-0004").warrant.anchors) == {o.name for o in store.observations(state=None)}
    assert _lens_of(store, "L-0004").warrant.evidence == "genesis", "an anchor is earned; the evidence stays genesis"
    assert not [n for n in record.nominations if n.subject.startswith("L-")], "an anchored lens before the deadline is not at a door"


def test_an_examiner_lens_is_anchored_to_the_attack_entry_whose_landing_the_adjudicator_upheld(store):
    s1 = _session(store, 1, [CLEAN], {"task_pass_rate": 1.0})
    s2 = _session(store, 2, [CLEAN], {"task_pass_rate": 1.0})
    _observe(store, s1, NOT_RETRIED), _observe(store, s2, NOT_RETRIED)
    record = _consolidate.consolidate(store)
    attack = next(e for e in store.all("hypothesis") if e.species == "attack")
    assert attack.verdict == "premise-killed"
    assert _lens_of(store, "L-0006").warrant.anchors == [attack.id] and "L-0006" in record.anchored
    assert _lens_of(store, "L-0005").warrant.anchors == [], "an angle that did not land earned nothing here"


def test_a_seed_lens_walked_to_the_deadline_with_nothing_consumed_is_retired_and_no_longer_walked(store):
    deadline = store.registry.bars["genesis_anchor_deadline_consolidations"]
    for n in range(1, 2 * deadline + 1):
        s = _session(store, n, [CLEAN], {"task_pass_rate": 1.0})
        _walk(store, s, "L-0003", [])
    for _ in range(deadline):
        record = _consolidate.consolidate(store, force=True)
        assert record.retired == []
    record = _consolidate.consolidate(store, force=True)
    assert "L-0003" in record.retired and _lens_of(store, "L-0003").status == "retired"
    n = next(n for n in record.nominations if n.subject == "L-0003")
    assert n.outcome.startswith("moot: retired through the genesis-deadline door")
    entry = next(e for e in store.all("hypothesis") if e.id == n.ledger_entry)
    assert entry.species == "currency" and entry.contradiction.source.role == "oracle" and entry.adjudicator.role == "adjudicator"
    assert "L-0003" not in {l.id for l in store.registry.lenses("close")}, "a retired lens is walked by nothing"
    assert "L-0001" not in record.retired, "an unwalked seed is no signal: kept, and the lint still warns"
    assert any(f.check == "genesis-anchor" and f.record == "L-0001" for f in _lint.run(store).findings)
    assert not any(f.check == "genesis-anchor" and f.record == "L-0003" for f in _lint.run(store).findings)


def test_a_lens_whose_product_stopped_varying_is_retired_with_its_cacheable_answer(store):
    window = store.registry.bars["retirement"]["window_passes"]
    same = [{"record": "D-0001", "disposition": "considered-not-applicable", "why": "the hook fired on the http term alone"}]
    for n in range(1, window + 1):
        s = _session(store, n, [CLEAN], {"task_pass_rate": 1.0})
        _walk(store, s, "L-0001", same)
    walks = _reviews.lens_walks(store)
    assert len(walks["L-0001"]) == window and _reviews.collapsed(walks["L-0001"], window)["product"] == same
    assert _reviews.collapsed(walks["L-0001"][:-1], window) is None, "below the window the stream has not been read long enough"
    record = _consolidate.consolidate(store, force=True)
    assert "L-0001" in record.retired
    n = next(n for n in record.nominations if n.subject == "L-0001")
    assert "variance-collapse" in n.outcome and "cacheable answer" in n.outcome


def test_an_always_empty_stream_is_no_signal(store):
    window = store.registry.bars["retirement"]["window_passes"]
    for n in range(1, window + 1):
        s = _session(store, n, [CLEAN], {"task_pass_rate": 1.0})
        _walk(store, s, "L-0003", [])
    assert _reviews.collapsed(_reviews.lens_walks(store)["L-0003"], window) is None
