"""The recurrence's strength is graded, not only floored. Above the independence floor the distinct-session count N is
banded — modest (small N, under twice the bar) or strong (at or above twice the bar) — and the reading is carried into the
adjudicator's verdict context as corroboration, additional to the binary floor. The floor still refuses N below the bar
whatever the verdict, and a landed premise kill still stands at any N: the graded reading informs reasoning, it never
lowers the floor and never overrides a premise kill."""

from __future__ import annotations

import json

from hgi import consolidate as _consolidate
from hgi import index as _index
from hgi import model as _model
from hgi.store import now
from hgi.types import Consolidation, Nomination
from tests.conftest import decision_body, draft
from tests.test_slice3 import CLEAN, FAULTED, NO_CAUSE, NOT_RETRIED, _observe, _session


def _record(store) -> Consolidation:
    return Consolidation(id=store.mint("consolidation"), started_at=now(), after_pass=2, sessions_read=["S-0001", "S-0002"])


def _nominated_over(store, n_sessions, rows, scores, noticed, **overrides):
    """A draft whose evidence names one observation from each of ``n_sessions`` distinct sessions — N = n_sessions."""
    obs = [_observe(store, _session(store, p, rows, scores), noticed) for p in range(1, n_sessions + 1)]
    names = [o.name for o in obs]
    d = draft(store, **overrides).model_copy(update={"evidence": names})
    store.write_draft(d)
    return d, Nomination(rung="new-decision", rung_why="a test", subject="cause", evidence=names, draft=d.uid)


def _requests(monkeypatch):
    seen = []
    real = _model.complete

    def spy(role, payload, **kw):
        seen.append((role, json.loads(payload)))
        return real(role, payload, **kw)

    monkeypatch.setattr(_model, "complete", spy)
    return seen


def _verdict_recurrence(seen):
    return next(req["recurrence"] for role, req in seen if req.get("request") == "verdict")


def test_a_draft_at_or_above_twice_the_bar_carries_the_strong_reading(store, monkeypatch):
    seen = _requests(monkeypatch)  # bar is 2, so 4 distinct sessions is 2*bar: strong
    d, nomination = _nominated_over(store, 4, [FAULTED], {"task_pass_rate": 0.5, "error_cause_present": 0.0}, NO_CAUSE)
    _consolidate.adjudicate(store, _record(store), nomination, d, {"scores": {}})
    r = _verdict_recurrence(seen)
    assert r["sessions"] == 4 and r["bar"] == 2 and r["reading"].startswith("strong recurrence (N=4 sessions)")


def test_a_draft_at_exactly_the_bar_carries_the_modest_reading(store, monkeypatch):
    seen = _requests(monkeypatch)  # 2 distinct sessions is the bar itself: at the floor, under twice it
    d, nomination = _nominated_over(store, 2, [FAULTED], {"task_pass_rate": 0.5, "error_cause_present": 0.0}, NO_CAUSE)
    _consolidate.adjudicate(store, _record(store), nomination, d, {"scores": {}})
    r = _verdict_recurrence(seen)
    assert r["sessions"] == 2 and r["bar"] == 2 and r["reading"].startswith("modest recurrence (small N=2)")


def test_the_floor_still_refuses_below_the_bar_whatever_the_reading(store, monkeypatch):
    seen = _requests(monkeypatch)  # one session: below the bar. The reading names the floor; the committer refuses regardless
    d, nomination = _nominated_over(store, 1, [FAULTED], {"task_pass_rate": 0.5, "error_cause_present": 0.0}, NO_CAUSE)
    entry = _consolidate.adjudicate(store, _record(store), nomination, d, {"scores": {}})
    r = _verdict_recurrence(seen)
    assert r["sessions"] == 1 and r["reading"].startswith("below the independence floor (N=1")
    assert entry.outcome.startswith("refused by the floor: 1 distinct session(s)")
    assert store.decisions() == [] and store.drafts() == []


def test_a_landed_premise_kill_stands_at_a_strong_recurrence(store, monkeypatch):
    """The graded reading never overrides an upheld premise kill: a strong recurrence at N=4 with a landed premise claim
    still declines and drops the draft."""
    seen = _requests(monkeypatch)
    warrant = decision_body()["warrant"] | {"premises": [{"id": "p1", "statement": "a transient fault clears on the next call",
                                                          "falsifier": "no transient fault in the trace store over the window", "status": "supported"}]}
    d, nomination = _nominated_over(store, 4, [CLEAN], {"task_pass_rate": 1.0}, NOT_RETRIED, warrant=warrant)
    entry = _consolidate.adjudicate(store, _record(store), nomination, d, {"scores": {}})
    r = _verdict_recurrence(seen)
    assert r["reading"].startswith("strong recurrence (N=4 sessions)")
    assert entry.verdict == "premise-killed" and entry.outcome == "declined; draft dropped"
    assert store.drafts() == [] and store.decisions() == [] and _index.attacker(store)["upheld"] == 1
