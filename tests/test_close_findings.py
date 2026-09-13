"""A close files an observation per L-0004 finding that has an anchor and a ``noticed``; a finding a reply left without one is
skipped, not raised on — the stream run's strict arm died at pass 7 on a reply that dropped the field."""

from hgi import close as _close
from hgi.types import LensAnswer
from tests.test_slice3 import FAULTED, _session


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
