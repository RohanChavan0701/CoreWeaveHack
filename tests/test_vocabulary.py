"""§ 6.14 growth by the route-before-mint ladder: two same-shaped escapes from independent passes nominate a term,
two from one pass are one datum, the blind coder contradicts with the candidate withheld, the adjudicator
verdicts, and the registry — a register — grows in place with git carrying the history."""

from __future__ import annotations

from hgi import consolidate as _consolidate
from hgi import registry as _registry
from hgi import reviews as _reviews
from hgi import stub
from hgi.store import now
from hgi.types import Session


def _escaping(store, pass_: int, *escapes: str) -> Session:
    s = Session(id=store.mint("session"), pass_=pass_, started_at=now(), closed_at=now(), attached=True, work_shape={"terms": ["http-tool"], "escapes": list(escapes)},
                evaluation={"evaluation": "suite-v1", "scores": {"task_pass_rate": {"series": "suite-v1/task_pass_rate", "value": 1.0, "as_of": now()}}, "rows": []})
    store.write(s)
    return s


def test_independent_escapes_nominate_and_the_registry_grows_when_the_coder_agrees(store, monkeypatch):
    _escaping(store, 1, "other(streaming tool)"), _escaping(store, 2, "other(Streaming-Tool)")
    (cluster,) = _reviews.escape_clusters(store)
    assert cluster["term"] == "streaming-tool" and cluster["sessions"] == ["S-0001", "S-0002"]
    monkeypatch.setitem(stub.HANDLERS, "coding", lambda req: {name: ["other(a stream the tool layer does not expose)"] for name in (o["name"] for o in req["observations"])})
    record = _consolidate.consolidate(store)
    assert record.minted == ["work-shape/streaming-tool"]
    n = next(n for n in record.nominations if n.subject == "work-shape/streaming-tool")
    assert n.outcome == "minted work-shape/streaming-tool" and n.evidence == ["S-0001", "S-0002"]
    entry = next(e for e in store.all("hypothesis") if e.id == n.ledger_entry)
    assert entry.species == "coding" and entry.verdict == "agree" and entry.contradiction.source.role == "coder" and entry.adjudicator.role == "adjudicator"
    assert entry.contradiction.coding["covered_by"] == [] and entry.contradiction.coding["after_pass"] == 2
    assert "streaming-tool" in store.registry.terms("work-shape") and "streaming-tool" in _registry.load(store.root).terms("work-shape")
    assert store.registry.vocab("work-shape").terms["streaming-tool"]["since"] == now().date().isoformat()
    assert _reviews.escape_clusters(store) == [], "a minted term no longer escapes"
    store.registry.check("work-shape", "streaming-tool")


def test_two_escapes_from_one_pass_are_one_datum(store):
    _escaping(store, 1, "other(streaming-tool)", "other(streaming-tool)"), _escaping(store, 2)
    record = _consolidate.consolidate(store)
    assert record.minted == [] and not [n for n in record.nominations if n.subject.startswith("work-shape/")]


def test_a_term_the_coder_covers_is_declined_and_recurs_only_on_new_passes(store):
    _escaping(store, 1, "other(http-retry)"), _escaping(store, 2, "other(http-retry)")
    record = _consolidate.consolidate(store)
    n = next(n for n in record.nominations if n.subject == "work-shape/http-retry")
    assert n.outcome.startswith("decline(") and "http-tool" in n.outcome and record.minted == []
    assert "http-retry" not in store.registry.terms("work-shape")
    assert _reviews.escape_clusters(store) == [], "the same two sessions do not nominate again"
    _escaping(store, 3, "other(http-retry)")
    assert [c["sessions"] for c in _reviews.escape_clusters(store)] == [["S-0003"]], "recurrence counts again from the pass after the verdict"


def test_an_escape_that_is_not_a_term_shape_is_ignored(store):
    _escaping(store, 1, "other(a whole sentence, with punctuation!)"), _escaping(store, 2, "other(a whole sentence, with punctuation!)")
    assert _reviews.escape_clusters(store) == [] and _reviews.term_of("other(Tool Budget)") == "tool-budget" and _reviews.term_of("http-tool") is None
