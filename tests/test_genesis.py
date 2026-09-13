"""§ 13.4: genesis articles earn an anchor from the loop's own history or are evicted. The consolidator proposes
an instance, the adjudicator says whether it exemplifies the article, the committer appends the anchor; past
the deadline an article still unanchored is evicted, and the cap has a seat again."""

from __future__ import annotations

from hgi import consolidate as _consolidate
from hgi import index as _index
from hgi import lint as _lint
from hgi.registry import read_json, write_json
from tests.test_slice3 import FAULTED, NO_CAUSE, _observe, _session


def _two_passes(store):
    s1 = _session(store, 1, [FAULTED], {"task_pass_rate": 0.5, "error_cause_present": 0.0})
    s2 = _session(store, 2, [FAULTED], {"task_pass_rate": 0.5, "error_cause_present": 0.0})
    _observe(store, s1, NO_CAUSE), _observe(store, s2, NO_CAUSE)


def test_articles_earn_anchors_from_the_history_the_loop_wrote(store):
    _two_passes(store)
    record = _consolidate.consolidate(store)
    assert record.admitted == ["D-0001"]
    anchored = {a.id: a.warrant.anchors for a in store.articles() if a.warrant.anchors}
    assert set(anchored) == set(record.anchored) and {"C-0001", "C-0003", "C-0004", "C-0005", "C-0006", "C-0007"} <= set(anchored)
    assert anchored["C-0003"] == ["O-0001"] and anchored["C-0001"] == ["H-0001"] and anchored["C-0006"] == ["D-0001"]
    assert all(a.warrant.evidence == "genesis" for a in store.articles()), "an anchor is earned; the evidence stays genesis"
    for n in (n for n in record.nominations if n.rung == "article"):
        entry = next(e for e in store.all("hypothesis") if e.id == n.ledger_entry) if n.ledger_entry else None
        assert (entry is None) == (n.outcome == "no instance proposed")
        if entry:
            assert entry.species == "currency" and entry.verdict == "still-holds" and entry.adjudicator.role == "adjudicator" and entry.proposer.role == "consolidator"
    unanchored = [n for n in record.nominations if n.rung == "article" and n.outcome == "no instance proposed"]
    assert [n.subject for n in unanchored] == ["C-0002"], "no pass has reported a consultation yet"
    assert not [f for f in _lint.run(store).findings if f.check == "genesis-anchor"]


def test_an_article_the_history_never_instantiates_is_evicted_at_the_deadline(store):
    path = store.path("constitution", "C-0002")
    raw = read_json(path)
    raw["article"] = "A seed claim no ledger will ever instantiate."
    write_json(path, raw)
    _two_passes(store)
    deadline = store.registry.bars["genesis_anchor_deadline_consolidations"]
    for _ in range(deadline):
        record = _consolidate.consolidate(store, force=True)
        assert "C-0002" not in record.flipped and store.read("constitution", "C-0002").status == "live"
    assert any(f.check == "genesis-anchor" and f.record == "C-0002" for f in _lint.run(store).findings)
    record = _consolidate.consolidate(store, force=True)
    assert record.flipped == ["C-0002"] and store.read("constitution", "C-0002").status == "evicted"
    n = next(n for n in record.nominations if n.subject == "C-0002")
    assert n.outcome == f"no instance proposed; evicted past the {deadline}-consolidation deadline"
    assert [a.id for a in store.articles()] == ["C-0001", "C-0003", "C-0004", "C-0005", "C-0006", "C-0007"]
    assert not [f for f in _lint.run(store).findings if f.check == "genesis-anchor"]
    _index.regenerate(store)
    assert _lint.run(store).green


def test_an_anchor_that_names_nothing_is_refused_before_the_adjudicator(store, monkeypatch):
    from hgi import stub
    _two_passes(store)
    monkeypatch.setitem(stub.HANDLERS, "anchor", lambda req: {"anchors": [{"article": "C-0001", "anchor": "H-9999", "why": "invented"}]})
    record = _consolidate.consolidate(store)
    n = next(n for n in record.nominations if n.subject == "C-0001")
    assert n.outcome == "refused: H-9999 names nothing in the store" and n.ledger_entry is None and record.anchored == []
