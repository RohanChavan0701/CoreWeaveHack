"""Fix B: a record's consultation hook is seeded with the tasks' own declared work-shape terms, so a record learned
from an http-tool task is retrievable by the boot index for the next http-tool task — not scoped to the blind coder's
work-shape coding of how the failure presented (economy-run item 39)."""

from __future__ import annotations

from hgi import consolidate as _consolidate
from hgi import index as _index
from hgi import stub
from hgi.store import now
from hgi.types import Observation, Session

NO_CAUSE = "task genesis/sum_numbers failed on a transient fault (HTTP 502) and the reported error named no cause"


def _session_with_call(store, pass_: int, call: str, task: str = "genesis/sum_numbers") -> Session:
    row = {"task": task, "error": {"message": "GET /numbers failed", "cause": None}, "applied": [],
           "tool_errors": [{"message": "GET /numbers failed", "cause": "HTTP 502 (transient)", "transient": True}], "call": call}
    facts = {k: {"series": f"suite-v1/{k}", "value": v, "as_of": now().isoformat()} for k, v in {"task_pass_rate": 0.5, "error_cause_present": 0.0}.items()}
    s = store.parse_as(Session, {"id": store.mint("session"), "pass": pass_, "started_at": now().isoformat(), "closed_at": now().isoformat(),
                                 "attached": True, "evaluation": {"evaluation": "suite-v1", "scores": facts, "rows": [row]}})
    store.write(s)
    return s


def _observe_call(store, session: Session, call: str, noticed: str) -> Observation:
    o = Observation(uid=store.new_uid(), name=store.next_name("O"), noticed_at=now(), session=session.id, happened=noticed, anchor={"call": call})
    store.write(o)
    return o


def test_anchor_terms_reads_the_tasks_own_shapes_from_the_evidence(store):
    s = _session_with_call(store, 1, "weave:///c/1")
    o = _observe_call(store, s, "weave:///c/1", NO_CAUSE)
    # genesis/sum_numbers declares shapes ("http-tool", "error-wrapping"); the anchor call resolves the observation to its row.
    assert _consolidate.anchor_terms(store, [o.name]) == ["error-wrapping", "http-tool"]
    assert _consolidate.anchor_terms(store, []) == [], "no evidence, no seed"
    assert _consolidate.anchor_terms(store, ["O-9999"]) == [], "an observation the store lacks contributes nothing"


def test_a_record_learned_from_http_tool_observations_is_hooked_on_http_tool(store, monkeypatch):
    s1 = _session_with_call(store, 1, "weave:///c/1")
    s2 = _session_with_call(store, 2, "weave:///c/2")
    _observe_call(store, s1, "weave:///c/1", NO_CAUSE)
    _observe_call(store, s2, "weave:///c/2", NO_CAUSE)
    real = stub.HANDLERS["nominate"]

    def coder_misses_http(req):  # the drafter hooks on the coder's shape and omits the task's own term
        out = real(req)
        for n in out["nominations"]:
            if n.get("sketch"):
                n["sketch"]["terms"] = ["error-wrapping"]
        return out

    monkeypatch.setitem(stub.HANDLERS, "nominate", coder_misses_http)
    record = _consolidate.consolidate(store)
    assert record.admitted == ["D-0001"]
    d = store.read("decision", "D-0001")
    assert "http-tool" in d.consultation_terms, "the task's own term seeds the hook even when the drafter omitted it"
    assert "error-wrapping" in d.consultation_terms, "the drafter's own choice is kept, not replaced"
    assert "D-0001" in {cell["record"] for cell in _index.hooks(store).get("http-tool", [])}, "the boot index matches an http-tool task to it"
