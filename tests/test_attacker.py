"""I16 — the instruments are instrumented: attacker precision as a tracked floor, the attacker's misses as a stream."""

from __future__ import annotations

from hgi import consolidate as _consolidate
from hgi import index as _index
from hgi import lint as _lint
from hgi.store import now
from hgi.types import Steer
from tests.test_slice3 import CLEAN, FAULTED, NO_CAUSE, NOT_RETRIED, _observe, _session


def test_precision_reads_landings_upheld_and_names_the_ceiling(store):
    s1 = _session(store, 1, [CLEAN], {"task_pass_rate": 1.0})
    s2 = _session(store, 2, [CLEAN], {"task_pass_rate": 1.0})
    _observe(store, s1, NOT_RETRIED), _observe(store, s2, NOT_RETRIED)
    _consolidate.consolidate(store)  # the premise kill lands and is upheld: decline
    a = _index.attacker(store)
    assert a["dispatched"] == 1 and a["landed"] >= 1 and a["entries_with_landing"] == 1 and a["upheld"] == 1 and a["overruled"] == 0
    assert a["precision"] == 1.0 and a["per_angle"]["L-0006"]["landed"] >= 1 and set(a["per_angle"]) == {"L-0006", "L-0007", "mechanical"}
    assert any("ceiling artifact" in n for n in a["notes"])


def test_zero_landings_interrogate_the_dispatch_bar_and_a_later_steer_is_a_miss(store):
    s1 = _session(store, 1, [FAULTED], {"task_pass_rate": 0.5, "error_cause_present": 0.0})
    s2 = _session(store, 2, [FAULTED], {"task_pass_rate": 0.5, "error_cause_present": 0.0})
    _observe(store, s1, NO_CAUSE), _observe(store, s2, NO_CAUSE)
    record = _consolidate.consolidate(store)
    assert record.admitted == ["D-0001"]
    a = _index.attacker(store)
    assert a["landed"] == 0 and a["precision"] is None and any("dispatch bar" in n for n in a["notes"]) and a["misses"] == []
    store.append(Steer(id=store.mint("steer"), at=now(), source={"kind": "oracle", "anchor": None}, correction="applied and still regressed",
                       indicts={"record": "D-0001", "slot": "payload", "signature": "recalled-applied-still-corrected"}, matrix_cell="system-misses/oracle-catches"))
    a = _index.attacker(store)
    assert a["misses"] == [{"record": "D-0001", "survived": [a["misses"][0]["survived"][0]], "caught_by": ["T-0001"]}]
    _index.regenerate(store)
    assert _lint.run(store).green, "the projection's cells carry counts and ids, nothing compliable"
