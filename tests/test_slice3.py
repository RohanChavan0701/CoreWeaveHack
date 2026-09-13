"""Slice 3 acceptance: from two seeded, independent observations of one fork the pipeline admits a decision
whose payload is object-decoupled and whose observations flip to promoted with pointers; an attack that
kills a premise yields decline and drops the draft; an escalate lands on the queue file the dashboard
reads; no context but the adjudicator's ever writes a verdict (the lint proves it on the ledger)."""

from __future__ import annotations

from hgi import consolidate as _consolidate
from hgi import index as _index
from hgi import lint as _lint
from hgi.store import now
from hgi.types import Observation, Session
import suite as _suite

NAMES = [t.id for t in _suite.current().tasks]


def _session(store, pass_: int, rows: list[dict], scores: dict[str, float | None]) -> Session:
    facts = {k: ({"series": f"suite-v1/{k}", "value": v, "as_of": now().isoformat()} if v is not None
                 else {"series": f"suite-v1/{k}", "unevaluable": "no evaluable row", "as_of": now().isoformat()}) for k, v in scores.items()}
    s = store.parse_as(Session, {"id": store.mint("session"), "pass": pass_, "started_at": now().isoformat(), "closed_at": now().isoformat(),
                                 "attached": True, "evaluation": {"evaluation": "suite-v1", "scores": facts, "rows": rows}})
    store.write(s)
    return s


def _observe(store, session: Session, noticed: str) -> Observation:
    o = Observation(uid=store.new_uid(), name=store.next_name("O"), noticed_at=now(), session=session.id, noticed=noticed,
                    anchor={"path": "suite/tools.py:54"})
    store.write(o)
    return o


FAULTED = {"task": "sum_numbers", "error": {"message": "GET /numbers failed", "cause": None}, "applied": [],
           "tool_errors": [{"message": "GET /numbers failed", "cause": "HTTP 502 Bad Gateway from /numbers (transient)", "transient": True}]}
CLEAN = {"task": "sum_numbers", "error": None, "applied": [], "tool_errors": []}
NO_CAUSE = "task sum_numbers failed on a transient fault (HTTP 502) and the reported error named no cause"
NOT_RETRIED = "task sum_numbers named the transient cause (HTTP 502) and still failed: the call was not retried"


def test_two_independent_observations_promote_to_an_abstracted_decision(store):
    s1 = _session(store, 1, [FAULTED], {"task_pass_rate": 0.5, "error_cause_present": 0.0})
    s2 = _session(store, 2, [FAULTED], {"task_pass_rate": 0.5, "error_cause_present": 0.0})
    o1, o2 = _observe(store, s1, NO_CAUSE), _observe(store, s2, NO_CAUSE)
    record = _consolidate.consolidate(store)
    assert record.admitted == ["D-0001"]
    d = store.read("decision", "D-0001")
    assert d.status == "accepted" and "sum_numbers" not in d.decision and d.decision.startswith("Errors that wrap")
    assert d.admission.ledger_entry == "H-0001" and d.admission.adjudicator.role == "adjudicator"
    promoted = {o.name: o for o in store.observations(state=None)}
    assert all(promoted[n].disposition.state == "promoted" and promoted[n].disposition.pointer == "D-0001" for n in (o1.name, o2.name))
    assert all(o.shape for o in promoted.values()), "the consolidation pass filled the shapes, not the noticing session"
    assert store.drafts() == [] and store.queue() == []
    _index.regenerate(store)
    assert _lint.run(store).green
    assert [p for p in _index.paths_to(store, "D-0001") if p[0] == o1.name] == [[o1.name, "D-0001"]]


def test_same_session_observations_do_not_meet_the_bar(store):
    s1 = _session(store, 1, [FAULTED], {"task_pass_rate": 0.5})
    s2 = _session(store, 2, [FAULTED], {"task_pass_rate": 0.5})
    _observe(store, s1, NO_CAUSE), _observe(store, s1, NO_CAUSE)
    record = _consolidate.consolidate(store)
    assert record.admitted == [] and [n for n in record.nominations if n.draft] == []
    assert all(o.disposition.state == "open" for o in store.observations(state=None))


def test_a_killed_premise_declines_and_drops_the_draft(store):
    # the retry lesson's premise "a transient fault clears on the next call" is refuted when the trace store holds no transient fault
    s1 = _session(store, 1, [CLEAN], {"task_pass_rate": 1.0})
    s2 = _session(store, 2, [CLEAN], {"task_pass_rate": 1.0})
    _observe(store, s1, NOT_RETRIED), _observe(store, s2, NOT_RETRIED)
    record = _consolidate.consolidate(store)
    assert record.admitted == [] and store.drafts() == [] and store.queue() == []
    entry = store.all("hypothesis")[0]
    assert entry.verdict == "premise-killed" and entry.outcome == "declined; draft dropped"
    assert any(c.landed and c.target == "premise:p1" for c in entry.contradiction.attack.claims)
    assert all(o.disposition.state == "open" for o in store.observations(state=None))
    assert record.nominations[0].outcome == "declined; draft dropped"


def test_unevaluable_oracle_evidence_escalates_to_the_queue_and_a_human_verdict_admits(store):
    s1 = _session(store, 1, [FAULTED], {"task_pass_rate": 0.5, "error_cause_present": None})
    s2 = _session(store, 2, [FAULTED], {"task_pass_rate": 0.5, "error_cause_present": None})
    _observe(store, s1, NO_CAUSE), _observe(store, s2, NO_CAUSE)
    record = _consolidate.consolidate(store)
    assert record.admitted == [] and store.drafts() == []
    queue = store.queue()
    assert len(queue) == 1 and queue[0].why.startswith("escalate(") and (store.queue_dir / f"{queue[0].draft.uid}.json").exists()
    assert record.nominations[0].outcome == "escalated to the human queue"
    outcome = _consolidate.resolve(store, queue[0].draft.uid, "admit")
    assert outcome.startswith("admitted D-0001") and store.queue() == []
    d = store.read("decision", "D-0001")
    assert d.admission.adjudicator.role == "human"
    _index.regenerate(store)
    assert _lint.run(store).green


def test_verdict_authority_and_role_separation_on_the_ledger(store):
    s1 = _session(store, 1, [FAULTED], {"task_pass_rate": 0.5, "error_cause_present": 0.0})
    s2 = _session(store, 2, [FAULTED], {"task_pass_rate": 0.5, "error_cause_present": 0.0})
    _observe(store, s1, NO_CAUSE), _observe(store, s2, NO_CAUSE)
    _consolidate.consolidate(store)
    for entry in (e for e in store.all("hypothesis") if e.species == "attack"):
        assert entry.contradiction.attack.verdict == "pending"
        assert entry.verdict != "pending" and entry.adjudicator is not None and entry.adjudicator.role == "adjudicator"
        assert {entry.proposer.role, entry.contradiction.source.role, entry.adjudicator.role} == {"consolidator", "examiner", "adjudicator"}
    # every species, not the attack alone: a currency entry's contradictor is the oracle — the anchor, the ratio, the
    # fire — never the adjudicator that verdicts it, and no two parties on one entry share a role or a call
    currency = [e for e in store.all("hypothesis") if e.species == "currency"]
    assert currency, "genesis anchoring wrote currency entries"
    for entry in store.all("hypothesis"):
        parties = [entry.proposer, entry.contradiction.source] + ([entry.adjudicator] if entry.adjudicator else [])
        assert len({p.role for p in parties}) == len(parties), entry.id
    assert all(e.contradiction.source.role == "oracle" and e.contradiction.source.call for e in currency)
    failures = _lint.run(store, seams=("write",)).failures
    assert not [f for f in failures if f.check in ("verdict-authority", "role-separation")]


def test_the_lint_names_a_collapsed_pair_on_the_ledger(store):
    from hgi.types import LedgerEntry
    store.append(LedgerEntry(id=store.mint("hypothesis"), at=now(), species="currency", subject="D-0001", claim="x",
                             proposer={"role": "consolidator", "call": None},
                             contradiction={"source": {"role": "adjudicator", "model_id": "stub", "call": "weave:///t/call/1"}},
                             verdict="still-holds", adjudicator={"role": "adjudicator", "model_id": "stub", "call": "weave:///t/call/1"}))
    findings = [f for f in _lint.run(store, seams=("write",)).failures if f.check == "role-separation"]
    assert len(findings) == 1 and "contradictor and adjudicator are both 'adjudicator'" in findings[0].message


def test_a_close_time_contradiction_is_proposed_by_the_records_admitter_and_contradicted_by_the_pass(store):
    from hgi import close as _close
    from hgi.types import LensAnswer
    s1 = _session(store, 1, [FAULTED], {"task_pass_rate": 0.5, "error_cause_present": 0.0})
    s2 = _session(store, 2, [FAULTED], {"task_pass_rate": 0.5, "error_cause_present": 0.0})
    _observe(store, s1, NO_CAUSE), _observe(store, s2, NO_CAUSE)
    _consolidate.consolidate(store)
    s3 = _session(store, 3, [FAULTED], {"task_pass_rate": 0.5})
    s3.model_id = "stub"
    s3.lens_answers = [LensAnswer(lens="L-0003", answer="p1 no longer holds", call="weave:///t/call/pass-lens",
                                  findings=[{"record": "D-0001", "slot": "warrant", "what_changed": "the scorer graded on exit code", "anchor": "weave:///t/eval/3"}])]
    [entry] = _close.file_contradictions(store, s3)
    assert entry.verdict == "pending" and entry.species == "currency" and entry.subject == "D-0001"
    assert entry.proposer.role == "consolidator" and entry.contradiction.source.role == "pass"
    assert entry.contradiction.source.call == "weave:///t/call/pass-lens"


def test_consolidation_keeps_its_schedule(store):
    _session(store, 1, [CLEAN], {"task_pass_rate": 1.0})
    import pytest
    with pytest.raises(SystemExit, match="every 2 passes"):
        _consolidate.consolidate(store)
    assert _consolidate.consolidate(store, force=True).sessions_read == ["S-0001"]


def test_an_invented_applied_id_earns_no_credit_row(store):
    s1 = _session(store, 1, [{**CLEAN, "applied": ["obs-001"]}], {"task_pass_rate": 1.0})
    assert _consolidate.credit_table(store, [s1]) == []
