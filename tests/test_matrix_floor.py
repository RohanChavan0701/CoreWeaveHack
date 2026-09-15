"""The true-miss floor (§ 10.1, the bottom-right cell): a task that failed in a pass that consulted nothing and filed no
observation from the row is the case nothing caught — counted by session and task, as a floor, never a fixed zero."""

from __future__ import annotations

from hgi import index as _index
from hgi.types import Consulted, Observation
from tests.conftest import NOW
from tests.test_slice3 import CLEAN, FAULTED, _session


def test_a_failed_row_nothing_caught_lands_in_the_true_miss_cell(store):
    s1 = _session(store, 1, [FAULTED, CLEAN], {"task_pass_rate": 0.5})
    s2 = _session(store, 2, [{**FAULTED, "task": "fetch_user_name", "call": "weave:///t/call/2"}], {"task_pass_rate": 0.0})
    # s2 filed an observation from its failed row: that row was noticed, so it is not a miss nothing caught
    store.write(Observation(uid=store.new_uid(), name="O-0001", noticed_at=NOW, session=s2.id,
                            happened="task fetch_user_name failed on a transient fault and named no cause", anchor={"call": "weave:///t/call/2"}))
    m = _index.matrix(store)
    assert m["system-misses/none-catches"] == [f"{s1.id}/sum_numbers"]
    assert "floor" in m["note"]


def test_a_pass_that_consulted_a_record_is_not_a_true_miss(store):
    s = _session(store, 1, [FAULTED], {"task_pass_rate": 0.0})
    s.consulted = [Consulted(record="D-0001")]
    store.write(s)
    assert _index.true_misses(store) == []


def test_a_row_without_a_call_is_matched_by_the_task_the_noticing_names(store):
    s = _session(store, 1, [FAULTED], {"task_pass_rate": 0.0})
    store.write(Observation(uid=store.new_uid(), name="O-0001", noticed_at=NOW, session=s.id,
                            happened="task sum_numbers failed and named no cause", anchor={"path": "suite/tools.py:54"}))
    assert _index.true_misses(store) == []


def test_an_open_or_detached_session_does_not_count(store):
    s = _session(store, 1, [FAULTED], {"task_pass_rate": 0.0})
    s.closed_at = None
    store.write(s)
    d = _session(store, 2, [FAULTED], {"task_pass_rate": 0.0})
    d.attached = False
    store.write(d)
    assert _index.true_misses(store) == []
