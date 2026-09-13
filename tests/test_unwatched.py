"""A record whose dispositive world-state latches are absent has a join over nothing: its grammar reads ``unwatched``,
loudly, on the summaries projection and the consultation plan (doctrine § 16.17; spec § 9.1)."""

from __future__ import annotations

from hgi import boot as _boot
from hgi import index as _index
from tests.conftest import adjudicated_entry, adjudicator, decision_body, draft


def _admit(store, name, **overrides):
    d = draft(store, name, **overrides)
    entry = adjudicated_entry(store, d.uid)
    entry.verdict = "admit"
    return store.admit(d, entry, adjudicator())


def test_the_summaries_cell_reads_the_watch_or_unwatched(store):
    watched = _admit(store, "P-w")
    body = decision_body()
    body["latches"] = [l for l in body["latches"] if l["type"] != "revisit"]
    unwatched = _admit(store, "P-u", latches=body["latches"])
    cells = {row["record"]: row["watch"] for row in _index.summaries(store)}
    assert cells[watched.id] == "error_cause_present < 0.5 over 2"
    assert cells[unwatched.id] == _index.UNWATCHED
    assert _index.watch_of(unwatched) == "unwatched"


def test_the_consultation_plan_names_the_unwatched_records(store):
    from hgi.types import Considered, Session
    from hgi.store import now
    body = decision_body()
    body["latches"] = [l for l in body["latches"] if l["type"] != "revisit"]
    d = _admit(store, "P-u", latches=body["latches"])
    s = Session(id="S-0001", pass_=1, started_at=now(), considered=[Considered(record=d.id, via="index", guard_passed=True, owed_act="apply", terms_matched=["http-tool"])])
    plan = _boot.plan(store, s, store.articles(), None, [])
    assert f"unwatched 1: {d.id}" in plan
