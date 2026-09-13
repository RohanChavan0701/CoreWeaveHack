"""Revision routing (doctrine § 7.5): the escape pile nominates growth, and the relation between the axis's partition and the
candidate's routes the move — horizontal (add a member, partition one) is grown; vertical (the axis conflated two
questions) is surfaced and never minted as a member."""

from __future__ import annotations

from hgi import consolidate as _consolidate
from hgi import reviews as _reviews
from tests.test_slice3 import CLEAN, _session


def _escaping(store, pass_: int, terms: list[str], escape: str = "other(streaming-tool)"):
    s = _session(store, pass_, [CLEAN], {"task_pass_rate": 1.0})
    s.work_shape.terms = terms
    s.work_shape.escapes = [escape]
    store.write(s)
    return s


def _cluster(store):
    [c] = _reviews.escape_clusters(store, "work-shape")
    return c


def test_a_missing_peer_is_horizontal(store):
    for n in range(1, 5):
        _escaping(store, n, [])
    route = _reviews.revision_route(store, "work-shape", _cluster(store))
    assert route["breadth"] == 0 and route["route"] == "horizontal" and "missing peer" in route["reading"]


def test_a_value_within_one_member_is_a_partition(store):
    for n in range(1, 5):
        _escaping(store, n, ["http-tool"] + (["tool-budget"] if n % 2 else []))
    route = _reviews.revision_route(store, "work-shape", _cluster(store))
    assert route["breadth"] == 2 and route["dependence"] == 1.0 and route["route"] == "horizontal" and "within http-tool" in route["reading"]


def test_a_cross_cutting_distinction_is_vertical_and_not_minted(store):
    for n, terms in enumerate((["http-tool"], ["shell-tool"], ["file-tool"], ["http-tool", "shell-tool"]), start=1):
        _escaping(store, n, terms)
    route = _reviews.revision_route(store, "work-shape", _cluster(store))
    assert route["breadth"] == 3 and route["dependence"] < 1.0 and route["route"] == "vertical"
    record = _consolidate.consolidate(store, force=True)
    n = next(n for n in record.nominations if n.subject == "work-shape/streaming-tool")
    assert n.outcome.startswith("vertical:") and "surfaced, not minted" in n.outcome and n.ledger_entry is None
    assert "streaming-tool" not in store.registry.terms("work-shape") and record.minted == []


def test_under_twice_the_bar_the_reading_is_ambiguous_and_horizontal(store, monkeypatch):
    from hgi import stub
    for n, terms in enumerate((["http-tool"], ["shell-tool"]), start=1):
        _escaping(store, n, terms)
    route = _reviews.revision_route(store, "work-shape", _cluster(store))
    assert route["route"] == "horizontal" and route["reading"].startswith("ambiguous (small N)")
    monkeypatch.setitem(stub.HANDLERS, "coding", lambda req: {name: ["other(a stream the tool layer does not expose)"] for name in (o["name"] for o in req["observations"])})
    record = _consolidate.consolidate(store)
    assert record.minted == ["work-shape/streaming-tool"], "a small pile still grows horizontally through the coder and the adjudicator"
    entry = next(e for e in store.all("hypothesis") if e.subject == "work-shape/streaming-tool")
    assert entry.contradiction.coding["route"]["reading"].startswith("ambiguous")
