"""The pass's own proposals (close step 6): a draft the pass files reaches the backward pass through the
brief, where the consolidator may adopt it as its nomination — it then goes through attack and verdict
like any other draft, its provenance kept — and a draft no consolidation adopts expires at the bar."""

from __future__ import annotations

from hgi import consolidate as _consolidate
from hgi import index as _index
from hgi import lint as _lint
from hgi import roles
from hgi.stub import sketch
from tests.test_slice3 import FAULTED, NO_CAUSE, _observe, _session


def _pass_draft(store, session, evidence):
    raw = {"rung": "new-decision", "rung_why": "the fork is undecided", "subject": "cause", "evidence": evidence, "sketch": sketch("cause", ["http-tool"], evidence)}
    draft = roles.draft_of(store, raw, proposed_by=session.id, name=store.next_name("P"), model_id="stub")
    store.write_draft(draft)
    session.proposals.append(draft.uid)
    store.write(session)
    return draft


def test_a_pass_proposal_reaches_the_brief_and_an_adopted_one_is_admitted_with_its_provenance(store):
    s1 = _session(store, 1, [FAULTED], {"task_pass_rate": 0.5, "error_cause_present": 0.0})
    s2 = _session(store, 2, [FAULTED], {"task_pass_rate": 0.5, "error_cause_present": 0.0})
    o1, o2 = _observe(store, s1, NO_CAUSE), _observe(store, s2, NO_CAUSE)
    draft = _pass_draft(store, s2, [o1.name, o2.name])
    record = _consolidate.consolidate(store)
    assert [p["uid"] for p in record.brief["proposals"]] == [draft.uid]
    adopted = [n for n in record.nominations if n.adopts == draft.uid]
    assert adopted and adopted[0].draft == draft.uid and record.admitted == ["D-0001"]
    d = store.read("decision", "D-0001")
    assert d.admission.proposed_by == s2.id, "the draft's provenance is the pass that proposed it"
    assert store.drafts() == []
    _index.regenerate(store)
    assert _lint.run(store).green


def test_a_proposal_no_consolidation_adopts_expires_at_the_bar(store, monkeypatch):
    from hgi import stub

    s1 = _session(store, 1, [FAULTED], {"task_pass_rate": 0.5})
    o1 = _observe(store, s1, NO_CAUSE)
    draft = _pass_draft(store, s1, [o1.name])  # one session: below the bar, so the stub adopts nothing
    monkeypatch.setitem(store.registry.bars, "proposal_ttl_consolidations", 2)
    monkeypatch.setitem(stub.HANDLERS, "nominate", lambda req: {"nominations": []})
    k1 = _consolidate.consolidate(store, force=True)
    assert store.drafts() and k1.expired == []
    k2 = _consolidate.consolidate(store, force=True)
    assert k2.expired == [draft.uid] and store.drafts() == []
