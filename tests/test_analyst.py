"""The programmatic ARIA surface: the analyst's report, recorded by URI, is the consolidation brief's primary input.

``hgi mirror`` publishes the runs the analyst reads; the report it drafts is resolved back through
:func:`hgi.mirror.read_report` and read by the backward pass as the nominator's rows, replacing the local
derivation. A URI that resolves to no machine-readable report falls back gracefully to that derivation, and the
interactive path — the URI recorded as provenance only — keeps working.
"""

from __future__ import annotations

import json

from hgi import consolidate as _consolidate
from hgi import mirror as _mirror
from hgi.store import now
from hgi.types import Observation, Session
import suite as _suite

NO_CAUSE = "task sum_numbers failed on a transient fault (HTTP 502) and the reported error named no cause"
FAULTED = {"task": "sum_numbers", "error": {"message": "GET /numbers failed", "cause": None}, "applied": [],
           "tool_errors": [{"message": "GET /numbers failed", "cause": "HTTP 502 (transient)", "transient": True}]}


def _session(store, pass_: int) -> Session:
    facts = {k: {"series": f"suite-v1/{k}", "value": v, "as_of": now().isoformat()}
             for k, v in {"task_pass_rate": 0.5, "error_cause_present": 0.0}.items()}
    s = store.parse_as(Session, {"id": store.mint("session"), "pass": pass_, "started_at": now().isoformat(), "closed_at": now().isoformat(),
                                 "attached": True, "evaluation": {"evaluation": "suite-v1", "scores": facts, "rows": [FAULTED]}})
    store.write(s)
    return s


def _observe(store, session: Session) -> Observation:
    o = Observation(uid=store.new_uid(), name=store.next_name("O"), noticed_at=now(), session=session.id, happened=NO_CAUSE,
                    anchor={"path": "suite/tools.py:54"})
    store.write(o)
    return o


def _two_independent(store) -> tuple[Observation, Observation]:
    s1, s2 = _session(store, 1), _session(store, 2)
    return _observe(store, s1), _observe(store, s2)


def _report_path(tmp_path, report: dict) -> str:
    p = tmp_path / "aria-report.json"
    p.write_text(json.dumps(report))
    return str(p)


# --- mirror.read_report -----------------------------------------------------------------------

def test_read_report_reads_a_json_file(tmp_path):
    p = tmp_path / "r.json"
    p.write_text(json.dumps({"groups": [], "credit": []}))
    assert _mirror.read_report(str(p)) == {"groups": [], "credit": []}
    assert _mirror.read_report(f"file://{p}") == {"groups": [], "credit": []}


def test_read_report_returns_none_when_the_uri_resolves_to_no_report(tmp_path):
    assert _mirror.read_report(None) is None
    assert _mirror.read_report("") is None
    assert _mirror.read_report(str(tmp_path / "absent.json")) is None       # no such file
    assert _mirror.read_report("weave:///does/not/resolve/offline") is None  # a ref that cannot be fetched
    not_json = tmp_path / "chat.txt"
    not_json.write_text("an interactive report, prose, not a brief")
    assert _mirror.read_report(str(not_json)) is None
    a_list = tmp_path / "list.json"
    a_list.write_text(json.dumps(["not", "a", "brief"]))
    assert _mirror.read_report(str(a_list)) is None                         # resolves, but not a brief object


# --- the report as the brief's primary input --------------------------------------------------

def test_the_analyst_report_is_the_primary_input_and_drives_the_nomination(tmp_path, store):
    """The analyst's groups — not the local coder — become the nominator's rows, and admit the decision they carry."""
    o1, o2 = _two_independent(store)
    report = {"groups": [{"shape": ["other(no-cause)"],
                          "observations": [{"name": o1.name, "session": o1.session, "happened": NO_CAUSE},
                                           {"name": o2.name, "session": o2.session, "happened": NO_CAUSE}]}]}
    record = _consolidate.consolidate(store, analyst_report=_report_path(tmp_path, report))
    assert record.admitted == ["D-0001"]
    assert record.analyst_report and record.analyst_report.endswith("aria-report.json")
    promoted = {o.name: o for o in store.observations(state=None)}
    assert promoted[o1.name].shape == ["other(no-cause)"], "the analyst's coding was stamped onto the observation"


def test_the_analyst_bare_out_of_vocab_label_lands_as_an_escape_not_a_crash(tmp_path, store):
    """A convention label the analyst proposes outside the closed ``convention`` vocabulary — a way of working it coded
    onto the grouping axis, e.g. ``call-budget-exceeded`` — runs through the same escape→mint wrap the local coder's does,
    landing as ``other(<what>)`` on both the observation and the brief group. Without the wrap the ``Term('convention')``
    validator refuses the bare term and the whole consolidation crashes (carry-forward item 59: the reasoning-core-hard
    endpoint's DeepSeek consolidator proposed exactly this bare term)."""
    o1, o2 = _two_independent(store)
    report = {"groups": [{"shape": ["call-budget-exceeded"], "convention": "call-budget-exceeded",
                          "observations": [{"name": o1.name, "session": o1.session, "happened": NO_CAUSE},
                                           {"name": o2.name, "session": o2.session, "happened": NO_CAUSE}]}]}
    record = _consolidate.consolidate(store, analyst_report=_report_path(tmp_path, report))
    promoted = {o.name: o for o in store.observations(state=None)}
    assert promoted[o1.name].shape == ["other(call-budget-exceeded)"], "the bare label was escape-wrapped onto the observation"
    group = record.brief["groups"][0]
    assert group["shape"] == ["other(call-budget-exceeded)"] and group["convention"] == "other(call-budget-exceeded)", \
        "the brief group carries the same wrapped label the observation does"


def test_an_empty_analyst_report_replaces_the_local_derivation_and_nominates_nothing(tmp_path, store):
    """With the analyst report as primary input, its empty groups mean no nomination — the local coder never runs."""
    o1, o2 = _two_independent(store)
    record = _consolidate.consolidate(store, analyst_report=_report_path(tmp_path, {"groups": [], "credit": []}))
    assert record.admitted == []
    assert store.drafts() == [] and store.queue() == []
    assert all(o.disposition.state == "open" and not o.shape for o in store.observations(state=None)), \
        "no report row grouped these; the local grouping was replaced, so nothing coded or nominated them"


def test_no_analyst_report_falls_back_to_the_local_derivation(store):
    """The fallback: with no report URI the same two observations group locally and admit the decision."""
    _two_independent(store)
    record = _consolidate.consolidate(store)
    assert record.admitted == ["D-0001"]
    assert record.analyst_report is None
    assert all(o.shape for o in store.observations(state=None)), "the local grouping filled the shapes"


def test_an_unresolvable_report_uri_falls_back_gracefully_and_keeps_the_provenance(store):
    """The interactive path: a URI that resolves to no brief still records as provenance, and the brief is local."""
    _two_independent(store)
    record = _consolidate.consolidate(store, analyst_report="weave:///interactive/chat/report", force=True)
    assert record.admitted == ["D-0001"], "the derivation ran because the URI resolved to no machine-readable report"
    assert record.analyst_report == "weave:///interactive/chat/report", "the URI is recorded as provenance either way"
