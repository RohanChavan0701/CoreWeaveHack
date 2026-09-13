"""§ 9.2, slice 6a — the lens battery: decoy rejection scored in Weave.

The close lenses each carry a ``counterfactual`` — the overshoot they must
refuse: manufacturing a falsification to have one to report (L-0003), or
grading a pass that recovered as a defect (L-0004). The battery is a fixed
dataset of planted items, half of them **decoys** — a louder, non-causal
signal the counterfactual must reject — and half genuine **signals** the
lens should catch. A lens answered over the battery is scored on two axes,
both derived from the same run and written onto the lens's telemetry:

- ``decoy_rejection`` — the fraction of decoys the lens correctly rejected
  (filed nothing for); the floor gate of the close lenses;
- ``answer_variance`` — the spread of the lens's filings across the whole
  battery; a lens that files the same answer on every item (all or nothing)
  reads zero, the crystallization signal absent — the sub-second "checked"
  the count-and-provenance form guards against.

The battery is a ``weave.Evaluation`` over a ``weave.Dataset``, run the way
:mod:`hgi.evaluate` runs the world: each scorer is a fact series named
``lens-battery-v1/<scorer>`` and every lens answer is a traced ``pass``
call. Absent data reads ``unevaluable``, never zero.
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import weave
from pydantic import PrivateAttr

from hgi import model as _model
from hgi import registry as _registry
from hgi import roles
from hgi import tracing
from hgi.evaluate import Evaluation, _evaluate
from hgi.store import Store, now
from hgi.types import Fact, LensTelemetry

LENS_BATTERY = "lens-battery-v1"


# --- what counts as a filing -------------------------------------------------------------------

def is_filed(finding: Any) -> bool:
    """A finding files only when it cites something: a record id or an anchor. An answer with no id is not filed (§ 6.13)."""
    if not isinstance(finding, dict):
        return False
    if finding.get("record") or finding.get("id"):
        return True
    anchor = finding.get("anchor")
    if isinstance(anchor, dict):
        return any(anchor.get(k) for k in ("call", "path", "uri", "record"))
    return bool(anchor)


def filed_any(findings: Any) -> bool:
    return isinstance(findings, list) and any(is_filed(f) for f in findings)


# --- the planted dataset -----------------------------------------------------------------------

def _l0003_subject(*, consulted: list[dict], rows: list[dict], failed: list[str], scores: dict) -> dict[str, Any]:
    """The whole-pass subject L-0003 reads: what the pass may have made false in the store."""
    return {"consulted": consulted, "rows": rows, "failed": failed, "fires": [], "scores": scores}


def _l0004_subject(row: dict) -> dict[str, Any]:
    """The single-row subject L-0004 reads: one artifact, its output and tool errors."""
    return {"task": row["task"], "prompt": f"the presentation for {row['task']}", "row": row, "consulted": []}


def battery_items(lens_id: str) -> list[dict[str, Any]]:
    """The fixed decoys and signals for a close lens. Two of each so the fractions and the variance are stable."""
    if lens_id == "L-0003":
        premise = [{"id": "D-battery", "decision": "carry the cause on every rethrow",
                    "premises": [{"id": "p1", "statement": "the scorer reads the final error", "status": "supported"}]}]
        return [
            {"kind": "decoy", "why": "scores fell but no store premise reversed — manufacturing a falsification to match the drop",
             "subject": _l0003_subject(consulted=premise, rows=[{"task": "t/a"}, {"task": "t/b"}],
                                       failed=["t/a", "t/b"], scores={"task_pass_rate": 0.20})},
            {"kind": "decoy", "why": "an unfamiliar task appeared — novelty, not a record made false",
             "subject": _l0003_subject(consulted=premise, rows=[{"task": "t/novel"}], failed=["t/novel"],
                                       scores={"task_pass_rate": 0.80})},
            {"kind": "signal", "why": "a consulted premise's falsifier was observed: the scorer now grades exit code only",
             "subject": _l0003_subject(
                 consulted=[{"id": "D-battery", "decision": "carry the cause on every rethrow",
                             "premises": [{"id": "p1", "statement": "the scorer reads the final error",
                                           "falsifier": "a scorer change that grades exit code only",
                                           "status": "reversed", "anchor": "weave:///battery/eval/scorer-change"}]}],
                 rows=[{"task": "t/exitcode"}], failed=[], scores={"error_cause_present": 0.0})},
            {"kind": "signal", "why": "a consulted record's hook now covers a shape it excludes: the payload is false where it fires",
             "subject": _l0003_subject(
                 consulted=[{"id": "D-battery2", "decision": "retry only transient tool faults",
                             "premises": [{"id": "p2", "statement": "the fault is transient",
                                           "falsifier": "a deterministic 400 retried as if transient",
                                           "status": "reversed", "anchor": "weave:///battery/eval/deterministic-400"}]}],
                 rows=[{"task": "t/400"}], failed=["t/400"], scores={"task_pass_rate": 0.50})},
        ]
    if lens_id == "L-0004":
        return [
            {"kind": "decoy", "why": "a transient fault fired mid-run but the task recovered and passed — loud, non-causal",
             "subject": _l0004_subject({"task": "decoy/recovered", "error": None,
                                        "tool_errors": [{"cause": "502 Bad Gateway", "transient": True}],
                                        "scores": {"task_pass_rate": {"value": 1.0}}, "call": "weave:///battery/call/d1"})},
            {"kind": "decoy", "why": "a long, alarming stdout on a task that passed — verbosity, not a defect",
             "subject": _l0004_subject({"task": "decoy/verbose", "error": None, "result": "WARNING " * 40,
                                        "tool_errors": [], "scores": {"task_pass_rate": {"value": 1.0}},
                                        "call": "weave:///battery/call/d2"})},
            {"kind": "signal", "why": "a task failed on a transient fault and the reported error named no cause",
             "subject": _l0004_subject({"task": "signal/uncaused", "error": {"message": "request failed", "cause": None},
                                        "tool_errors": [{"cause": "503 Service Unavailable", "transient": True}],
                                        "scores": {"task_pass_rate": {"value": 0.0}}, "call": "weave:///battery/call/s1"})},
            {"kind": "signal", "why": "a task named the transient cause and still failed: the call was not retried",
             "subject": _l0004_subject({"task": "signal/not-retried", "error": {"message": "timed out", "cause": "timeout"},
                                        "tool_errors": [{"cause": "timeout", "transient": True}],
                                        "scores": {"task_pass_rate": {"value": 0.0}}, "call": "weave:///battery/call/s2"})},
        ]
    return []


def dataset_rows(lenses: list[Any]) -> list[dict[str, Any]]:
    """One row per planted item per lens; each row carries the lens spec it is answered against, so predict is self-contained."""
    rows = []
    for lens in lenses:
        spec = {"id": lens.id, "angle": lens.angle, "counterfactual": lens.counterfactual, "product": lens.product}
        for n, item in enumerate(battery_items(lens.id)):
            rows.append({"item": f"{lens.id}/{item['kind']}/{n}", "lens": lens.id, "lens_spec": spec,
                         "subject": item["subject"], "is_decoy": item["kind"] == "decoy", "kind": item["kind"]})
    return rows


# --- the scorers -------------------------------------------------------------------------------

def _value(v: float | None, reason: str | None = None) -> dict[str, Any]:
    return {"value": v} if v is not None else {"value": None, "unevaluable": reason or "not evaluable"}


class DecoyRejection(weave.Scorer):
    """The floor gate: on a decoy, 1.0 when the lens filed nothing (rejected the plant), 0.0 when it took the bait. Signals are not evaluable here."""

    name: str = "decoy_rejection"

    @weave.op
    def score(self, *, output: dict, is_decoy: bool, **kwargs) -> dict:
        if not is_decoy:
            return _value(None, "not a decoy item")
        return _value(0.0 if output.get("filed") else 1.0)


class SignalCaught(weave.Scorer):
    """The complement: on a genuine signal, 1.0 when the lens filed it, 0.0 when it missed. Decoys are not evaluable here."""

    name: str = "signal_caught"

    @weave.op
    def score(self, *, output: dict, is_decoy: bool, **kwargs) -> dict:
        if is_decoy:
            return _value(None, "not a signal item")
        return _value(1.0 if output.get("filed") else 0.0)


SCORERS = [DecoyRejection, SignalCaught]


# --- the answerer ------------------------------------------------------------------------------

class LensBatteryModel(weave.Model):
    """Answers each battery item with the ``pass`` role, the way the close lenses are walked, and records whether it filed."""

    _outputs: list[dict[str, Any]] = PrivateAttr(default_factory=list)

    @property
    def outputs(self) -> list[dict[str, Any]]:
        return self._outputs

    @weave.op
    def predict(self, item: str, lens: str, lens_spec: dict, subject: dict, is_decoy: bool, kind: str) -> dict[str, Any]:
        payload = roles.request("lens", lens=lens_spec, subject=subject, empty_is_legal=roles.EMPTY_LENS_IS_LEGAL)
        c = _model.complete("pass", payload, records_in_context=[lens])
        out = c.json()
        if not isinstance(out, dict):
            out = {}
        findings = [f for f in out.get("findings", []) if isinstance(f, dict)]
        result = {"item": item, "lens": lens, "is_decoy": is_decoy, "kind": kind,
                  "answer": str(out.get("answer", "")), "findings": findings, "filed": filed_any(findings), "call": c.call}
        self._outputs.append(result)
        return result


# --- telemetry and facts -----------------------------------------------------------------------

def _variance(xs: list[float]) -> float:
    if not xs:
        return 0.0
    mean = sum(xs) / len(xs)
    return sum((x - mean) ** 2 for x in xs) / len(xs)


def telemetry_from(outputs: list[dict[str, Any]]) -> dict[str, LensTelemetry]:
    """Per-lens telemetry, computed from the battery run: the decoy-rejection fraction and the filing variance."""
    by_lens: dict[str, list[dict]] = defaultdict(list)
    for o in outputs:
        by_lens[o["lens"]].append(o)
    telemetry = {}
    for lens_id, rows in by_lens.items():
        decoys = [r for r in rows if r["is_decoy"]]
        rejected = [r for r in decoys if not r["filed"]]
        variance = _variance([1.0 if r["filed"] else 0.0 for r in rows])
        if decoys:
            fraction = len(rejected) / len(decoys)
            decoy = f"{fraction:.2f} — {len(rejected)}/{len(decoys)} planted decoys rejected ({LENS_BATTERY})"
        else:
            decoy = f"unevaluable — no decoy in the battery ({LENS_BATTERY})"
        spread = ("filings vary across" if variance > 0 else "the same filing on all") + f" {len(rows)} battery items"
        telemetry[lens_id] = LensTelemetry(answer_variance=f"{variance:.2f} — {spread} ({LENS_BATTERY})",
                                           decoy_rejection=decoy)
    return telemetry


def facts_from(summary: dict[str, Any], as_of: datetime, source: str | None) -> dict[str, Fact]:
    """The battery's scorer means as fact series ``lens-battery-v1/<scorer>``; a series no row could evaluate reads unevaluable."""
    facts = {}
    for scorer in SCORERS:
        name = scorer.model_fields["name"].default
        block = summary.get(name) or summary.get(scorer.__name__) or {}
        mean = (block.get("value") or {}).get("mean") if isinstance(block, dict) else None
        series = f"{LENS_BATTERY}/{name}"
        facts[name] = Fact(series=series, value=mean, as_of=as_of, source=source) if mean is not None else \
            Fact(series=series, unevaluable="no row was evaluable on this series", as_of=as_of, source=source)
    return facts


@dataclass
class BatteryResult:
    telemetry: dict[str, LensTelemetry]
    facts: dict[str, Fact]
    run: str | None
    outputs: list[dict[str, Any]] = field(default_factory=list)


# --- the run -----------------------------------------------------------------------------------

def run_battery(store: Store, lenses: list[Any] | None = None) -> BatteryResult:
    """Run the battery over the store's close lenses and return the per-lens telemetry and the scorer facts."""
    tracing.init()
    lenses = lenses if lenses is not None else store.registry.lenses("close")
    rows = dataset_rows(lenses)
    if not rows:
        return BatteryResult(telemetry={}, facts={}, run=None, outputs=[])
    model = LensBatteryModel()
    dataset = weave.Dataset(name=f"{LENS_BATTERY}-{len(rows)}", rows=rows)
    evaluation = Evaluation(name=LENS_BATTERY, dataset=dataset, scorers=[s() for s in SCORERS],
                            evaluation_name=f"{tracing.run_label()}{LENS_BATTERY}")
    with tracing.attributes(role="lens-battery", records_in_context=[l.id for l in lenses]):
        summary, call = asyncio.run(_evaluate(evaluation, model))
    stamp = now()
    uri = tracing.call_uri(call)
    return BatteryResult(telemetry=telemetry_from(model.outputs), facts=facts_from(summary, stamp, uri),
                         run=uri, outputs=model.outputs)


def populate_telemetry(store: Store, telemetry: dict[str, LensTelemetry]) -> list[str]:
    """Write the computed telemetry onto the lens register, moving each battered lens off ``design-stage``; returns the ids updated."""
    path = store.registry.path("lenses")
    raw = _registry.read_json(path)
    updated = []
    for item in raw:
        t = telemetry.get(item.get("id"))
        if t is not None:
            item["telemetry"] = t.model_dump()
            updated.append(item["id"])
    _registry.write_json(path, raw)
    return updated


# --- the command --------------------------------------------------------------------------------

def _cmd(args, store_of, finish) -> int:
    store = store_of(args)
    result = run_battery(store)
    updated = populate_telemetry(store, result.telemetry)
    for lens_id in updated:
        t = result.telemetry[lens_id]
        print(f"{lens_id}: decoy_rejection {t.decoy_rejection}; answer_variance {t.answer_variance}")
    scores = ", ".join(f"{k}={'unevaluable' if f.value is None else f'{f.value:.2f}'}" for k, f in result.facts.items())
    print(f"{LENS_BATTERY}: {scores}" + (f"; run {result.run}" if result.run else "; untraced (no Weave project)"))
    finish(store, args, f"Lens battery: score decoy rejection and populate telemetry for {', '.join(updated) or 'no lens'}")
    return 0


def register(add, store_of, finish) -> None:
    p = add("lens-battery", "run the lens battery: score decoy rejection and populate lens telemetry")
    p.set_defaults(fn=lambda args: _cmd(args, store_of, finish))
