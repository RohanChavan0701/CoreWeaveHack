"""Should-have-fired (§ 10.5, activation — recall): the boot recall lens's probes have a consumer — the brief's recall rows
nominate a hook-edit that re-keys the record on what the probing passes presented."""

from __future__ import annotations

from hgi import consolidate as _consolidate
from hgi import index as _index
from hgi.types import Consulted, LensAnswer
from tests.test_slice3 import CLEAN, FAULTED, NO_CAUSE, _observe, _session


def _admit_d1(store):
    s1 = _session(store, 1, [FAULTED], {"task_pass_rate": 0.5, "error_cause_present": 0.0})
    s2 = _session(store, 2, [FAULTED], {"task_pass_rate": 0.5, "error_cause_present": 0.0})
    _observe(store, s1, NO_CAUSE), _observe(store, s2, NO_CAUSE)
    assert _consolidate.consolidate(store).admitted == ["D-0001"]


def _probe(store, pass_: int, terms: list[str]):
    s = _session(store, pass_, [CLEAN], {"task_pass_rate": 1.0, "error_cause_present": 0.5})
    s.work_shape.terms = terms
    s.lens_answers = [LensAnswer(lens="L-0002", answer="D-0001 bears and no hook reached it", call=f"weave:///t/call/probe-{pass_}",
                                 findings=[{"record": "D-0001", "why": "the task wraps a shell failure and D-0001 says what to carry"}])]
    store.write(s)
    return s


def test_probes_from_independent_passes_row_the_recall_stream_and_are_re_keyed(store):
    _admit_d1(store)
    hook = store.read("decision", "D-0001").consultation_terms
    assert "shell-tool" not in hook
    _probe(store, 3, ["shell-tool", "error-wrapping"])
    _probe(store, 4, ["shell-tool"])
    [row] = _index.recall(store)
    assert row["record"] == "D-0001" and row["sessions"] == ["S-0003", "S-0004"] and row["missing"] == ["shell-tool"]
    record = _consolidate.consolidate(store)
    n = next(n for n in record.nominations if n.subject == "recall:D-0001")
    assert n.rung == "hook-edit" and n.outcome.startswith("admitted")
    successor = store.read("decision", n.outcome.split()[-1])
    assert set(successor.consultation_terms) == set(hook) | {"shell-tool"} and successor.lineage.supersedes == ["D-0001"]
    assert store.read("decision", "D-0001").status == "superseded"
    assert _index.recall(store) == [], "the probed record is retired into its re-keyed successor"


def test_a_probe_from_one_pass_is_one_datum(store):
    _admit_d1(store)
    _probe(store, 3, ["shell-tool"])
    _session(store, 4, [CLEAN], {"task_pass_rate": 1.0})
    [row] = _index.recall(store)
    assert row["sessions"] == ["S-0003"]
    record = _consolidate.consolidate(store)
    assert not [n for n in record.nominations if n.subject.startswith("recall:")]


def test_a_probe_for_a_record_the_pass_consulted_is_not_a_miss(store):
    _admit_d1(store)
    s = _probe(store, 3, ["tool-call-retry"])
    s.consulted = [Consulted(record="D-0001")]
    store.write(s)
    assert _index.recall(store) == []
