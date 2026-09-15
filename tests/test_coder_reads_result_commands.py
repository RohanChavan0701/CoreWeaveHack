"""Carry-forward item 49b — the blind coder's coverage question is put to the anchored row's `result` and `commands` (the
query text and output where the wrong literal lives), not to the observation prose alone. `code(..., rows=...)` enriches
each observation from its anchor's row; the live consolidation path (group_observations) builds that row map and passes it."""

from __future__ import annotations

from hgi import coder as _coder
from hgi import consolidate as _consolidate
from hgi import model as _model
from hgi.store import now
from hgi.types import Observation, Session


def test_coding_observations_enriches_result_and_commands_and_drops_the_anchor():
    rows = {"weave:///t/call/a": {"result": [{"amount": 0}], "commands": ["SELECT amount FROM loans WHERE status = 'approved'"]}}
    obs = [{"name": "O-0001", "noticed": "the query matched nothing", "anchor": {"call": "weave:///t/call/a"}}]
    [enriched] = _coder.coding_observations(obs, rows)
    assert enriched["result"] == [{"amount": 0}]
    assert enriched["commands"] == ["SELECT amount FROM loans WHERE status = 'approved'"]
    assert "anchor" not in enriched and enriched["name"] == "O-0001" and enriched["noticed"] == "the query matched nothing"


def test_an_observation_whose_anchor_has_no_row_gets_empty_content():
    [enriched] = _coder.coding_observations([{"name": "O-0002", "noticed": "x", "anchor": {"path": "p"}}], {})
    assert enriched["result"] is None and enriched["commands"] == []


def test_group_observations_puts_result_and_commands_to_the_coder(store, monkeypatch):
    # a session whose evaluation row carries the query text; the observation anchors on that row's call
    call = "weave:///t/call/sql"
    row = {"task": "q117", "call": call, "error": None,
           "result": [{"n": 0}], "commands": ["SELECT * FROM loan WHERE status = 'approved'"]}
    s = store.parse_as(Session, {"id": store.mint("session"), "pass": 1, "started_at": now().isoformat(), "closed_at": now().isoformat(),
                                 "attached": True, "evaluation": {"evaluation": "suite-v1",
                                 "scores": {"task_pass_rate": {"series": "suite-v1/task_pass_rate", "value": 0.0, "as_of": now().isoformat()}},
                                 "rows": [row]}})
    store.write(s)
    store.write(Observation(uid=store.new_uid(), name=store.next_name("O"), noticed_at=now(), session=s.id,
                            happened="the query matched nothing", anchor={"call": call}))

    seen = {}

    def _capture(name, *, session=None, pass_=None, **content):
        seen.update(content)
        return _model.Completion(text="{}", model_id="stub", call=None)

    monkeypatch.setattr(_coder, "_ask", _capture)
    from hgi.types import Consolidation
    record = Consolidation(id=store.mint("consolidation"), started_at=now(), after_pass=1, sessions_read=[s.id])
    _consolidate.group_observations(store, record)
    assert seen["observations"], "the coder was asked"
    o = seen["observations"][0]
    assert o["commands"] == ["SELECT * FROM loan WHERE status = 'approved'"] and o["result"] == [{"n": 0}]
    assert "anchor" not in o, "the anchor is the resolution key, not the coder's evidence"
