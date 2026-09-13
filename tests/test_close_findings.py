"""A close files an observation per L-0004 finding that has an anchor and a ``noticed``; a finding a reply left without one is
skipped, not raised on — the stream run's strict arm died at pass 7 on a reply that dropped the field."""

from hgi import boot as _boot
from hgi import close as _close
from hgi.types import LensAnswer
from tests.test_slice3 import FAULTED, _session

# A passed row that recovered from a non-transient convention (a 401 the /secure route guards behind a token): L-0009's
# class — the pass learned it, self-corrected on it, and the row scored 1.0, so L-0004's failed-row filter never sees it.
RECOVERED = {"task": "list_users", "error": None, "applied": [], "call": "weave:///t/call/recovered",
             "tool_errors": [{"message": "GET /secure/users failed", "cause": "HTTP 401 Unauthorized: routes under /secure require ?token=", "transient": False}],
             "scores": {"task_pass_rate": {"value": 1.0}}}
# A passed row whose only fault was a 502 that cleared on retry — transient, non-causal: the decoy L-0009 must reject.
TRANSIENT_RECOVERED = {"task": "sum_numbers", "error": None, "applied": [], "call": "weave:///t/call/transient",
                       "tool_errors": [{"cause": "HTTP 502 Bad Gateway from /numbers", "transient": True}],
                       "scores": {"task_pass_rate": {"value": 1.0}}}


def test_a_finding_with_no_noticed_is_not_filed_and_does_not_stop_the_close(store):
    s = _session(store, 1, [FAULTED], {"task_pass_rate": 0.5, "error_cause_present": 0.0})
    s.lens_answers.append(LensAnswer(lens="L-0004", answer="", findings=[
        {"noticed": "the retry was not attempted", "anchor": {"path": "suite/tools.py:54"}},
        {"anchor": {"path": "suite/tools.py:54"}},
        {"noticed": "  ", "anchor": {"path": "suite/tools.py:54"}},
        {"noticed": "no anchor, not filed either"},
    ]))
    filed = _close.file_observations(store, s)
    assert [o.noticed for o in filed] == ["the retry was not attempted"]
    assert s.observations_filed == [filed[0].name]


def test_l0009_files_a_recovered_nontransient_miss_from_a_passed_row(store):
    s = _session(store, 1, [RECOVERED], {"task_pass_rate": 1.0})
    s.lens_answers += _boot.walk_lenses(store, s, "close", lambda lens: _close.lens_subjects(store, s, lens))
    filed = _close.file_observations(store, s)
    # the passed row's non-transient recovery files as one observation, anchored on the row's call
    assert len(filed) == 1 and filed[0].anchor.call == "weave:///t/call/recovered"
    assert "401" in filed[0].noticed or "token" in filed[0].noticed
    assert s.observations_filed == [filed[0].name]
    assert [a.lens for a in s.lens_answers if a.findings] == ["L-0009"], "L-0004 sees no failed row; only L-0009 fires"


def test_l0009_files_nothing_from_a_passed_row_whose_only_fault_was_transient(store):
    s = _session(store, 1, [TRANSIENT_RECOVERED], {"task_pass_rate": 1.0})
    s.lens_answers += _boot.walk_lenses(store, s, "close", lambda lens: _close.lens_subjects(store, s, lens))
    # a 502 that cleared on retry is loud but non-causal — L-0009 is walked over no row and nothing files
    assert _close.file_observations(store, s) == []
