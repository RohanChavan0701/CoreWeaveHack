"""§ 9.2 — the oracle runs the pass's evaluation.

The task suite is a ``weave.Dataset``; each scorer is a fact series named
``<evaluation>/<scorer>``; the results land on the session as facts with
``as_of`` and the evaluation-run URI as ``source``. Then the watch evaluator
walks every live revisit latch over the last *persistence* attached runs and
emits a fire, naming its disposer, for every predicate that holds.

Absent data reads ``unevaluable``, never zero.
"""

from __future__ import annotations

import asyncio
import operator
from datetime import datetime
from typing import Any

import weave

from hgi import index as _index
from hgi import model as _model
from hgi import tracing
from hgi.store import Store, now
from hgi.types import Decision, EvaluationResult, Fact, Fire, Session
from suite import EVALUATION
from suite.agent import Agent
from suite.scorers import SCORERS
from suite.tasks import TASKS, dataset_name, suite_hash

COMPARATORS = {"<": operator.lt, "<=": operator.le, ">": operator.gt, ">=": operator.ge, "==": operator.eq, "!=": operator.ne}


def context_records(store: Store, session: Session) -> list[dict[str, Any]]:
    """The decisions the boot selected and whose guard passed — what the agent is conditioned on."""
    out = []
    for c in session.considered:
        if c.via == "constitution" or not c.guard_passed:
            continue
        d: Decision = store.read("decision", c.record)  # type: ignore[assignment]
        out.append({"id": d.id, "decision": d.decision, "terms": d.consultation_terms, "scopes": d.scopes, "stakes": d.summary.stakes})
    return out


class Evaluation(weave.Evaluation):
    """A Weave evaluation whose summary is the scorers' alone: task outputs are heterogeneous by design and carry no mean."""

    @weave.op
    async def summarize(self, eval_table) -> dict:
        from weave.flow.scorer import get_scorer_attributes
        from weave.flow.util import transpose

        rows = list(eval_table.rows)
        scores = transpose(transpose(rows).get("scores", []))
        summary = {}
        for scorer in self.scorers or []:
            attrs = get_scorer_attributes(scorer)
            summary[attrs.scorer_name] = attrs.summarize_fn(scores.get(attrs.scorer_name, []))
        return summary


async def _evaluate(evaluation: Evaluation, agent: Agent):
    return await evaluation.evaluate.call(evaluation, agent)


def facts_from(summary: dict[str, Any], as_of: datetime, source: str | None) -> dict[str, Fact]:
    facts = {}
    for scorer in SCORERS:
        name = scorer.model_fields["name"].default
        block = summary.get(name) or summary.get(scorer.__name__) or {}
        mean = (block.get("value") or {}).get("mean") if isinstance(block, dict) else None
        series = f"{EVALUATION}/{name}"
        facts[name] = Fact(series=series, value=mean, as_of=as_of, source=source) if mean is not None else \
            Fact(series=series, unevaluable="no row was evaluable on this series", as_of=as_of, source=source)
    return facts


def run(store: Store, session: Session) -> Session:
    """Run the suite for ``session``, write its facts, and return the session with ``evaluation`` set."""
    tracing.init()
    agent = Agent(session=session.id, pass_=session.pass_, attached=session.attached,
                  records=context_records(store, session) if session.attached else [],
                  articles=[a.article for a in store.articles()] if session.attached else [],
                  policy="stub" if isinstance(_model.backend(), _model.Stub) else "model")
    dataset = weave.Dataset(name=dataset_name(), rows=[t.row() for t in TASKS])
    evaluation = Evaluation(name=EVALUATION, dataset=dataset, scorers=[s() for s in SCORERS],
                                  evaluation_name=f"{EVALUATION} pass {session.pass_} {'attached' if session.attached else 'detached'}")
    with tracing.attributes(session=session.id, pass_=session.pass_, role="pass", attached=session.attached):
        summary, call = asyncio.run(_evaluate(evaluation, agent))
    stamp = now()
    session.model_id = _model.model_id()
    session.evaluation = EvaluationResult(evaluation=EVALUATION, run=tracing.call_uri(call), suite_hash=suite_hash(),
                                          scores=facts_from(summary, stamp, tracing.call_uri(call)), rows=agent.outputs)
    if session.trace_root is None:
        session.trace_root = tracing.call_uri(call)
    return session


# --- the watch evaluator -----------------------------------------------------------------------

def series_values(store: Store, scorer: str, upto: Session, persistence: int) -> list[float | None]:
    """The last ``persistence`` attached runs' values on a scorer, ending at ``upto`` (``None`` where unevaluable)."""
    runs = [s for s in store.all("session") if s.attached and s.evaluation is not None and s.pass_ <= upto.pass_ and s.id != upto.id]  # type: ignore[attr-defined]
    runs = sorted(runs, key=lambda s: s.pass_)[-(persistence - 1):] if persistence > 1 else []
    runs.append(upto)
    return [r.evaluation.scores[scorer].value if scorer in r.evaluation.scores else None for r in runs]


def emit_fires(store: Store, session: Session) -> list[Fire]:
    """Walk every live revisit latch; emit a fire, naming its disposer, where the predicate holds over its persistence window."""
    fires = []
    pending = {(f["record"], f["latch_index"]) for f in _index.undischarged_fires(store)}
    for trigger in _index.triggers(store):
        pred = trigger["predicate"]
        if pred["evaluation"] != EVALUATION or (trigger["record"], trigger["latch_index"]) in pending:
            continue
        values = series_values(store, pred["scorer"], session, pred["persistence"])
        if len(values) < pred["persistence"] or any(v is None for v in values):
            continue  # unevaluable never fires; it reads unevaluable, loudly, on the projection
        if all(COMPARATORS[pred["comparator"]](v, pred["value"]) for v in values):
            fire = Fire(id=store.mint("fire"), fired_at=now(), latch={"record": trigger["record"], "index": trigger["latch_index"]},
                        edge_event={"evaluation": EVALUATION, "pass": session.pass_, "scorer": pred["scorer"], "observed": values[-1],
                                    "source": session.evaluation.run if session.evaluation else None},
                        guard_result=True, disposer=trigger["disposer"], disposition={"act": trigger["owed_act"]})
            store.write(fire)
            fires.append(fire)
            session.fires_seen.append(fire.id)
    return fires


# --- the command --------------------------------------------------------------------------------

def evaluate_session(store: Store, session_id: str | None, pass_: int | None, detached: bool) -> Session:
    if detached:
        if pass_ is None:
            raise SystemExit("a detached pass names its pass number")
        session = Session(id=store.mint("session"), pass_=pass_, started_at=now(), attached=False)
    else:
        if session_id is None:
            raise SystemExit("--session names the booted session")
        session = store.read("session", session_id)  # type: ignore[assignment]
        if session.closed_at is not None:
            raise SystemExit(f"{session_id} is closed")
    session = run(store, session)
    fires = emit_fires(store, session) if session.attached else []
    if detached:
        session.closed_at = now()
        session.carry_forward = "detached pass: no boot, no close; the evaluation is the whole record"
    store.write(session)
    scores = ", ".join(f"{k}={'unevaluable' if f.value is None else f'{f.value:.2f}'}" for k, f in session.evaluation.scores.items())
    print(f"{session.id} pass {session.pass_} {'attached' if session.attached else 'detached'}: {scores}")
    for f in fires:
        print(f"  fire {f.id}: {f.latch.record} latch {f.latch.index} on {f.edge_event.scorer}={f.edge_event.observed}; owed {f.disposition.act} by {f.disposer}")
    return session


def register(add, store_of, finish) -> None:
    p = add("evaluate", "run the oracle; write facts; emit fires")
    p.add_argument("--session", help="the booted session to evaluate")
    p.add_argument("--pass", dest="pass_", type=int, help="the pass number (detached runs)")
    p.add_argument("--detached", action="store_true", help="an ablation pass: same agent, same suite, no boot or close")
    p.set_defaults(fn=lambda args: _cmd(args, store_of, finish))


def _cmd(args, store_of, finish) -> int:
    store = store_of(args)
    session = evaluate_session(store, args.session, args.pass_, args.detached)
    fired = " ".join(session.fires_seen)
    finish(store, args, f"Evaluate {session.id} pass {session.pass_}" + (f": fired {fired}" if fired else ""))
    return 0
