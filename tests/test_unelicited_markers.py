"""Carry-forward item 57 part 5 — typed ``failure-unelicited`` markers.

A failed row that elicits no observation would vanish: it forms no cluster, never reaches triage, never becomes a reality
entry. Instead it files a typed reality-species marker (:func:`hgi.close.file_unelicited_markers`) carrying its settled
``happened`` and anchor, so non-elicitation is visible telemetry — the recall floor — surfaced in the consolidation brief
(:func:`hgi.consolidate.unelicited_failures`). It never masquerades as an elicited lesson: it files no observation, so
grouping and triage never read it. A forced substantive observation is refused (§7.5); only the miss is recorded.
"""

from __future__ import annotations

from hgi import close as _close
from hgi import consolidate as _consolidate
from hgi import lint as _lint
from hgi.store import now
from hgi.types import Consolidation, Observation, Session

FAILED = {"task": "genesis/sum_numbers", "error": {"message": "hidden test raised", "cause": None}, "tool_errors": [], "applied": [], "call": "weave:///c/1"}
PASSED = {"task": "status_ok", "error": None, "tool_errors": [], "applied": [], "call": "weave:///c/2"}


def _session(store, pass_: int, rows: list[dict]) -> Session:
    facts = {"task_pass_rate": {"series": "suite-v1/task_pass_rate", "value": 0.5, "as_of": now().isoformat()}}
    s = store.parse_as(Session, {"id": store.mint("session"), "pass": pass_, "started_at": now().isoformat(), "closed_at": now().isoformat(),
                                 "attached": True, "model_id": "stub", "evaluation": {"evaluation": "suite-v1", "scores": facts, "rows": rows}})
    store.write(s)
    return s


def test_a_failed_row_with_no_observation_files_a_typed_marker(store):
    s = _session(store, 1, [FAILED])
    (marker,) = _close.file_unelicited_markers(store, s)
    assert marker.species == "reality" and marker.verdict == "pending" and marker.adjudicator is None
    coding = marker.contradiction.coding
    assert coding["marker"] == _close.FAILURE_UNELICITED and coding["task"] == "genesis/sum_numbers"
    assert coding["happened"] and coding["anchor"] == {"call": "weave:///c/1"} and coding["session"] == s.id
    assert marker.proposer.role == "pass" and marker.contradiction.source.role == "oracle"
    assert marker.id in s.ledger_entries


def test_a_failed_row_that_elicited_an_observation_files_no_marker(store):
    s = _session(store, 1, [FAILED])
    o = Observation(uid=store.new_uid(), name=store.next_name("O"), noticed_at=now(), session=s.id,
                    happened="task genesis/sum_numbers named no cause", anchor={"call": "weave:///c/1"})
    store.write(o)
    assert _close.file_unelicited_markers(store, s) == [], "an elicited failure is not a miss"


def test_a_passed_row_files_no_marker(store):
    s = _session(store, 1, [PASSED])
    assert _close.file_unelicited_markers(store, s) == [], "a passed row is not the world voting against the loop"


def test_the_marker_is_not_an_observation_and_never_groups(store):
    s = _session(store, 1, [FAILED])
    _close.file_unelicited_markers(store, s)
    assert store.observations(state=None) == [], "a marker files no observation; it cannot masquerade as an elicited lesson"
    record = Consolidation(id=store.mint("consolidation"), started_at=now(), after_pass=1, sessions_read=[s.id])
    assert _consolidate.group_observations(store, record) == [], "nothing to group: the marker never reaches the coder"


def test_the_marker_surfaces_in_the_brief_scoped_to_the_window(store):
    s = _session(store, 1, [FAILED])
    (marker,) = _close.file_unelicited_markers(store, s)
    rows = _consolidate.unelicited_failures(store, [s])
    assert rows == [{"session": s.id, "task": "genesis/sum_numbers", "happened": marker.contradiction.coding["happened"],
                     "anchor": {"call": "weave:///c/1"}, "ledger_entry": marker.id}]
    assert _consolidate.unelicited_failures(store, []) == [], "a marker outside the window is not surfaced"
    record = Consolidation(id=store.mint("consolidation"), started_at=now(), after_pass=1, sessions_read=[s.id])
    brief = _consolidate.build_brief(store, record, [s])
    assert brief["unelicited"] == rows, "the brief carries the recall-floor telemetry for the human"


def test_the_marker_is_lint_clean(store):
    s = _session(store, 1, [FAILED])
    _close.file_unelicited_markers(store, s)
    failures = _lint.run(store, seams=("write",)).failures
    assert not [f for f in failures if f.check in ("verdict-authority", "role-separation")], "the pass proposes, the oracle contradicts, no verdict without an adjudicator"
