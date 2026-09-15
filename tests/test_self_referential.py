"""Carry-forward item 48 — a lens answer about the store's own machinery must not become an observation of the world, nor
a decision. Two places: the close excludes a self-referential finding from a world-fact lens (L-0004/L-0009), and the
consolidation noise filter drops a group whose every anchor is self-referential. Both are conservative: a mixed finding
(a store record named beside a world convention) is kept, and the off-map coverage lens (L-0010) is exempt at close."""

from __future__ import annotations

from hgi import close as _close
from hgi import consolidate as _consolidate
from hgi import index as _index
from hgi import lint as _lint
from hgi.types import LensAnswer, Observation
from hgi.store import now
from tests.test_slice3 import FAULTED, _session


# --- the predicate ---------------------------------------------------------------------------

def test_self_referential_predicate():
    # anchored on a store record → self-referential
    assert _index.self_referential("the check record should have fired", {"record": "D-0004"})
    # loop-machinery subject, anchored on a task row → self-referential
    assert _index.self_referential("no store records consulted for this task", {"call": "weave:///t/call/x"})
    assert _index.self_referential("no rule matched the presentation", {"call": "weave:///t/call/x"})
    # a world convention → not self-referential
    assert not _index.self_referential("status is coded 'A' not 'approved'", {"call": "weave:///t/call/x"})
    assert not _index.self_referential("the /secure route wants a token", {"path": "suite/tools.py:1"})
    # L-0010's off-map coverage signal — subject is the work, not a record
    assert not _index.self_referential("work failed and matched no hook: the store holds no rule for mbpp/1", {"call": "weave:///t/call/x"})
    # mixed: a record named beside a world convention (a quoted literal) is kept
    assert not _index.self_referential("D-0004 should have fired: status is 'A' not 'approved'", {"record": "D-0004"})


# --- the close filter (item 48a) -------------------------------------------------------------

def _finding(noticed, **anchor):
    return {"happened": noticed, "anchor": anchor}


def test_close_excludes_a_self_referential_finding_and_keeps_a_mixed_one(store):
    s = _session(store, 1, [FAULTED], {"task_pass_rate": 0.5})
    s.lens_answers.append(LensAnswer(lens="L-0004", answer="", findings=[
        _finding("no store records consulted; the check record should have fired", call="weave:///t/call/a"),
        _finding("status is coded 'A' not 'approved'", call="weave:///t/call/b"),
        _finding("D-0004 should have fired because status is 'A' not 'approved'", record="D-0004", call="weave:///t/call/c"),
    ]))
    filed = _close.file_observations(store, s)
    kept = [o.happened for o in filed]
    assert "status is coded 'A' not 'approved'" in kept
    assert any(n.startswith("D-0004 should have fired") for n in kept), "a mixed finding is kept"
    assert not any("no store records consulted" in n for n in kept), "the purely self-referential finding is excluded"
    assert len(filed) == 2


def test_close_does_not_filter_the_off_map_lens(store):
    # L-0010's coverage signal mentions "no rule / no hook" but its subject is the work; it must still file.
    s = _session(store, 1, [FAULTED], {"task_pass_rate": 0.0})
    s.lens_answers.append(LensAnswer(lens="L-0010", answer="", findings=[
        _finding("work failed and matched no hook: the store holds no rule for sum_numbers", call="weave:///t/call/off"),
    ]))
    filed = _close.file_observations(store, s)
    assert len(filed) == 1 and "no hook" in filed[0].happened


# --- the noise filter (item 48b) -------------------------------------------------------------

def _obs(store, session, noticed, **anchor):
    o = Observation(uid=store.new_uid(), name=store.next_name("O"), noticed_at=now(), session=session, happened=noticed, anchor=anchor)
    store.write(o)
    return o


def test_triage_drops_a_fully_self_referential_group(store):
    o1 = _obs(store, "S-0001", "no rule matched; no store records consulted", call="weave:///t/call/a")
    o2 = _obs(store, "S-0002", "the check record should have fired", record="D-0004")
    brief = {"groups": [{"shape": ["output-schema"], "observations": [o1.name, o2.name], "sessions": ["S-0001", "S-0002"]}]}
    from hgi.types import Consolidation
    record = Consolidation(id=store.mint("consolidation"), started_at=now(), after_pass=2, sessions_read=["S-0001", "S-0002"])
    rows = _consolidate.triage(store, record, brief)
    assert brief["groups"] == [], "the self-referential group left the brief and is not nominated"
    assert rows and rows[0]["act"] == "dropped-self-referential"
    assert set(record.dismissed) == {o1.name, o2.name}
    assert all(store.observation(n).disposition.state == "dismissed" for n in (o1.name, o2.name))


def test_triage_keeps_a_mixed_group(store):
    o1 = _obs(store, "S-0001", "no store records consulted", call="weave:///t/call/a")
    o2 = _obs(store, "S-0002", "status is coded 'A' not 'approved'", call="weave:///t/call/b")
    brief = {"groups": [{"shape": ["output-schema"], "observations": [o1.name, o2.name], "sessions": ["S-0001", "S-0002"]}]}
    from hgi.types import Consolidation
    record = Consolidation(id=store.mint("consolidation"), started_at=now(), after_pass=2, sessions_read=["S-0001", "S-0002"])
    _consolidate.triage(store, record, brief)
    assert len(brief["groups"]) == 1, "a group with one non-self-referential anchor is kept"
    assert record.dismissed == []
