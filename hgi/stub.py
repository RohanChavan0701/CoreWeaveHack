"""The deterministic stand-in for the frozen model.

Every role request is a JSON object with a ``request`` field; the handler for
that field answers by fixed rules stated here. The stub exists so the loop's
mechanics — boot, evaluate, close, consolidate, the four-role adjudication —
run and are testable without an inference endpoint. Its answers are keyword
rules over the same inputs the model would read; they are not evidence that
anything learned.
"""

from __future__ import annotations

import json
import re
from typing import Any, Callable

HANDLERS: dict[str, Callable[[dict[str, Any]], Any]] = {}


def handles(name: str):
    def deco(fn):
        HANDLERS[name] = fn
        return fn
    return deco


def answer(messages: list[dict[str, Any]], tools: list[dict] | None = None) -> str:
    user = messages[-1]["content"]
    try:
        req = json.loads(user)
    except (json.JSONDecodeError, TypeError):
        req = {"request": "free"}
    handler = HANDLERS.get(req.get("request"), HANDLERS["free"])
    return json.dumps(handler(req))


@handles("free")
def _free(req):
    return {}


# --- the pass ---------------------------------------------------------------------

KEYWORDS: dict[str, tuple[str, ...]] = {
    "http-tool": ("get /", "http", "api", "502"),
    "shell-tool": ("shell", "wc -l"),
    "tool-budget": ("budget",),
    "file-tool": ("read config", "write report", "file"),
    "output-schema": ("schema", "exactly", "object"),
    "error-wrapping": ("error", "fail", "cause"),
    "tool-call-retry": ("retr", "transient"),
    "test-failure-triage": ("failing test",),
    "task-planning": ("plan",),
}


def terms_for(text: str, allowed: list[str]) -> list[str]:
    text = text.lower()
    return [t for t in allowed if any(k in text for k in KEYWORDS.get(t, ()))]


@handles("classify")
def _classify(req):
    text = " ".join(p["prompt"] for p in req["presentations"])
    return {"terms": terms_for(text, req["terms"]), "escapes": []}


@handles("guard")
def _guard(req):
    hook, shape = req["hook"], req["work_shape"]
    text = " ".join(p["prompt"] for p in req.get("presentations", [])).lower()
    overlap = sorted(set(hook["terms"]) & set(shape["terms"]))
    excluded = [n for n in hook.get("not_this", []) if n.lower() in text]
    passed = bool(overlap) and not excluded
    return {"passed": passed, "why": f"terms {overlap} matched" + (f"; excluded by {excluded}" if excluded else "")}


@handles("lens")
def _lens(req):
    lens, subject = req["lens"], req["subject"]
    if lens["id"] == "L-0004":
        return {"answer": "read from the rows' tool errors", "findings": _noticings(subject.get("rows", []))}
    return {"answer": "nothing found on this reading", "findings": []}


def _noticings(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        err = row.get("error")
        if not err:
            continue
        tool_errors = row.get("tool_errors", [])
        transient = next((e for e in tool_errors if e.get("transient")), None)
        anchor = {"call": row.get("call"), "path": "suite/tools.py:54"}
        if transient and not err.get("cause"):
            out.append({"noticed": f"task {row['task']} failed on a transient fault ({transient['cause']}) and the reported error named no cause",
                        "anchor": anchor, "recheck_when": "any tool call that can fail transiently"})
        elif transient and err.get("cause"):
            out.append({"noticed": f"task {row['task']} named the transient cause ({transient['cause']}) and still failed: the call was not retried",
                        "anchor": anchor, "recheck_when": "a transient fault reported without a retry"})
        elif any("budget" in (e.get("cause") or "") for e in tool_errors):
            out.append({"noticed": f"task {row['task']} exceeded its shell budget: independent calls were issued one per input instead of batched",
                        "anchor": anchor, "recheck_when": "a budgeted tool over several independent inputs"})
    return out


@handles("dispose")
def _dispose(req):
    applied_in = {rid for row in req["rows"] for rid in row.get("applied", [])}
    passed = sum(1 for row in req["rows"] if not row.get("error"))
    fires = [{"fire": f["id"], "outcome": f"{f['disposition']['act']}: {f['latch']['record']} read against the pass's rows; {passed}/{len(req['rows'])} tasks passed with it in context"}
             for f in req.get("fires_owed", [])]
    return {"fires": fires, "dispositions": [
        {"record": c["record"], "disposition": "applied" if c["record"] in applied_in else "considered-not-applicable",
         "note": "applied on " + ", ".join(r["task"] for r in req["rows"] if c["record"] in r.get("applied", [])) if c["record"] in applied_in else "hook matched the pass's presentation; no task bore on it"}
        for c in req["consulted"]
    ]}


@handles("propose")
def _propose(req):
    return {"drafts": []}


# --- the coder --------------------------------------------------------------------------

@handles("coding")
def _coding(req):
    return {o["name"]: terms_for(o["noticed"], req["terms"]) or ["other(unclassified)"] for o in req["observations"]}


# --- the consolidator ---------------------------------------------------------------------

LESSONS: dict[str, dict[str, Any]] = {
    "cause": {
        "decision": "Errors that wrap a failed tool call carry the underlying cause.",
        "latch": "a tool call that fails; an error reported from a tool failure; a wrapper that rethrows",
        "not_this": ["a failure inside the model's own reasoning, with no tool call behind it"],
        "stakes": "a silent failure hides the cause the oracle scores on; passes score green while the fault persists",
        "options": [("A — report the cause on every error", "chosen", "the scorer reads the final error's cause"),
                    ("B — report only the message", "rejected", "the cause is lost at the first rethrow")],
        "premises": [("p1", "the oracle's error_cause_present scorer reads the final error's cause", "a scorer change that grades on exit code only"),
                     ("p2", "tool failures recur across the suite", "two consecutive consolidation passes with no tool failure in the trace store")],
        "counterfactual": "The overshoot is a wrapper that reports the cause but never recovers — observed in {anchors}, where the task still failed.",
        "watch": ("error_cause_present", "<", 0.5),
        "residue": ["whether the cause named is the right one is judgment; the floor checks shape only"],
        "moot_when": "no tool in the layer can fail",
    },
    "retry": {
        "decision": "A transient tool failure is retried once before it is reported, and the report carries the cause.",
        "latch": "a tool call that can fail transiently; a 5xx from the HTTP tool; a wrapper around a flaky call",
        "not_this": ["a non-transient failure such as a 404, which a retry cannot repair"],
        "stakes": "a task that fails on a transient fault scores zero while one retry would pass",
        "options": [("A — retry once, cause preserved", "chosen", "clears the transient fault and keeps the scorer's signal"),
                    ("B — report the cause without retrying", "rejected", "the cause was named and the task still failed")],
        "premises": [("p1", "a transient fault clears on the next call", "a second consecutive 5xx on the same path in the trace store"),
                     ("p2", "task_pass_rate on faulted tasks is bounded by whether the call is retried", "faulted tasks failing after a retry")],
        "counterfactual": "The overshoot is retrying every failure including the non-transient — a retry storm — bounded by {anchors}.",
        "watch": ("task_pass_rate", "<", 0.7),
        "residue": ["whether one retry is the right number is judgment"],
        "moot_when": "the tool layer stops exposing transient failures",
    },
    "batch": {
        "decision": "Under a call budget, independent calls over known inputs are issued as one batched call.",
        "latch": "a shell tool under a call budget; several files or inputs to inspect",
        "not_this": ["calls whose inputs depend on a previous call's output"],
        "stakes": "a budget exceeded fails the task outright",
        "options": [("A — one batched call", "chosen", "fits any budget of one or more"),
                    ("B — one call per input", "rejected", "exceeds the budget whenever inputs outnumber it")],
        "premises": [("p1", "the budget is smaller than the number of independent inputs", "a budget at or above the input count")],
        "counterfactual": "The overshoot is batching dependent calls whose later inputs are unknown — bounded by {anchors}.",
        "watch": ("tool_budget_respected", "<", 0.5),
        "residue": ["whether the inputs are truly independent is judgment"],
        "moot_when": "no tool runs under a budget",
    },
}


def lesson_key(texts: list[str]) -> str | None:
    joined = " ".join(texts).lower()
    if "named no cause" in joined or "carry the underlying cause" in joined:
        return "cause"
    if "not retried" in joined or "retried once" in joined:
        return "retry"
    if "budget" in joined:
        return "batch"
    return None


def sketch(key: str, terms: list[str], anchors: list[str]) -> dict[str, Any]:
    """The lesson as a drafting reply's sketch — the judgment; the body is derived by :mod:`hgi.drafting`."""
    L = LESSONS[key]
    scorer, cmp, value = L["watch"]
    return {
        "decision": L["decision"], "counterfactual": L["counterfactual"].format(anchors=", ".join(anchors)),
        "latch": L["latch"], "terms": terms, "not_this": L["not_this"], "stakes": L["stakes"],
        "context": "the same fork was observed in independent passes: " + ", ".join(anchors),
        "options": [{"name": n, "judged": j, "why": w} for n, j, w in L["options"]],
        "premises": [{"id": i, "statement": st, "falsifier": f} for i, st, f in L["premises"]],
        "watch": {"scorer": scorer, "comparator": cmp, "value": value, "persistence": 2},
        "residue": L["residue"], "moot_when": L["moot_when"], "scopes": ["suite/tools"],
    }


def _leaf(parent: dict[str, Any], terms: list[str], context: str) -> dict[str, Any]:
    """A draft body derived from an accepted record's body with its consultation hook replaced — never a second copy."""
    body = json.loads(json.dumps(parent["body"]))
    for latch in body["latches"]:
        if latch["type"] == "consultation":
            latch["guard"]["terms"] = terms
    body["context"] = context
    return body


@handles("nominate")
def _nominate(req):
    brief, bars = req["brief"], req["bars"]
    accepted = brief.get("accepted", [])
    bodies = {d["id"]: d for d in accepted if d.get("body")}
    nominations = []
    for row in brief.get("fusion", []):  # § 10.6 split: one leaf per sub-shape, the parent retiring by coverage migration
        parent = bodies.get(row["record"])
        if parent is None:
            continue
        for terms in (row["applied_on"], row["never_on"]):
            nominations.append({"rung": "new-decision", "rung_why": f"dispositions on {row['record']} are bimodal across sub-shapes: applied on {row['applied_on']}, never on {row['never_on']}; a fused record splits into leaves",
                                "subject": f"split:{row['record']}", "evidence": [], "supersedes": [], "split_from": row["record"], "folded_from": [],
                                "body": _leaf(parent, terms, f"leaf of {row['record']} on the sub-shape {terms}")})
    for row in brief.get("structural_zero", []):  # activation — recall: re-key the record no registered hook reaches
        terms = terms_for(row["latch"], [t for t in row["presented"] if not t.startswith("other(")]) or [t for t in row["presented"] if not t.startswith("other(")][:1]
        if not terms:
            continue
        nominations.append({"rung": "hook-edit", "rung_why": f"{row['record']} is a structural zero: its consultation hook names {row['terms']}, which no boot classifies into; its cue names {terms}, which the window presented",
                            "subject": f"zero:{row['record']}", "evidence": [], "supersedes": [row["record"]], "split_from": None, "folded_from": [],
                            "edit": {"terms": terms}, "body": None})
    for row in brief.get("convergence", []):  # § 10.6 fold: identical hooks applied together contract into one successor
        a, b = (bodies.get(r) for r in row["records"])
        if not (row["identical_hooks"] and a and b):
            continue
        body = _leaf(a, a["terms"], f"fold of {row['records'][0]} and {row['records'][1]}: applied together in {row['co_applied']} passes on {row['shared_terms']}")
        body["decision"] = f"{a['decision'].rstrip('.')}; {b['decision'][0].lower()}{b['decision'][1:]}"
        nominations.append({"rung": "new-decision", "rung_why": f"{row['records']} were applied together in {row['co_applied']} passes on the same hook; their payloads entail one another and one record carries both",
                            "subject": "fold:" + "+".join(row["records"]), "evidence": [], "supersedes": [], "split_from": None, "folded_from": list(row["records"]),
                            "body": body})
    for group in brief.get("groups", []):
        obs = group["observations"]
        sessions = {o["session"] for o in obs}
        if len(sessions) < bars["decision"]["independent_observations"]:
            continue
        key = lesson_key([o["noticed"] for o in obs])
        if key is None:
            continue
        covered = [d for d in accepted if key in d["decision"].lower() or (key == "batch" and "batched" in d["decision"].lower())]
        if covered:
            continue
        terms = [t for t in group["shape"] if not t.startswith("other(")] or ["error-wrapping"]
        names = [o["name"] for o in obs]
        supersedes = [d["id"] for d in accepted if key == "retry" and "cause" in d["decision"].lower()]
        proposal = next((p for p in brief.get("proposals", []) if lesson_key([p["decision"]]) == key and set(p["evidence"]) & set(names)), None)
        nominations.append({
            "rung": "new-decision",
            "rung_why": ("payload indicted: the superseded record was recalled and applied and the oracle still regressed on task_pass_rate; a re-derived payload supersedes it"
                         if supersedes else "no existing record's counterfactual, hook or register absorbs this fork; the fork is undecided"),
            "subject": key, "evidence": names, "supersedes": supersedes, "split_from": None, "folded_from": [],
            "adopts": proposal["uid"] if proposal else None,
            "sketch": None if proposal else sketch(key, terms, names),
        })
    return {"nominations": nominations}


ARTICLE_INSTANCES: list[tuple[str, Callable[[dict[str, Any]], str | None]]] = [
    ("backward pass admits", lambda i: next((h["id"] for h in i["hypotheses"] if (h.get("outcome") or "").startswith("admitted")), None)),
    ("count with ids", lambda i: next((u["id"] for u in i["dispositions"]), None)),
    ("hypothesis with an anchor", lambda i: next((o["name"] for o in i["observations"] if o["anchor"]), None)),
    ("no context holds two roles", lambda i: next((h["id"] for h in i["hypotheses"] if len(h["roles"]) >= 3), None)),
    ("raises abstraction", lambda i: next((h["id"] for h in i["hypotheses"] if "payload:abstraction" in h["attack_targets"]), None)),
    ("discloses its residue", lambda i: next((d["id"] for d in i["decisions"] if d["residue"]), None) or next((f["session"] for f in i["unevaluable_facts"]), None)),
    ("retirement leg", lambda i: next((d["id"] for d in i["decisions"] if d["status"] == "superseded"), None) or next((d["id"] for d in i["decisions"] if d["retirement_guard"]), None)),
]
"""What the stub consolidator reads an article's words as asking for, and where in the instances it looks."""


@handles("anchor")
def _anchor(req):
    out = []
    for article in req["articles"]:
        for cue, pick in ARTICLE_INSTANCES:
            if cue in article["article"]:
                anchor = pick(req["instances"])
                if anchor:
                    out.append({"article": article["id"], "anchor": anchor, "why": f"the instance {anchor} is what the article's words '{cue}' name"})
                break
    return {"anchors": out}


@handles("exemplifies")
def _exemplifies(req):
    if req.get("instance"):
        return {"verdict": "still-holds", "why": f"{req['anchor']} exists in the store and is of the kind the article names"}
    return {"verdict": "moot", "why": "the anchor names nothing"}


# --- the examiner ---------------------------------------------------------------------------

@handles("attack")
def _attack(req):
    draft, ev = req["draft"], req["evidence"]
    claims = []
    sessions = ev.get("observation_sessions", [])
    independent = len(set(sessions)) >= ev.get("bar_independent", 2)
    claims.append({"target": "warrant:independence", "refutation": "the anchored observations come from one pass, which is one datum",
                   "reading_taken": True, "landed": not independent, "evidence": [f"sessions {sorted(set(sessions))}"]})
    for p in draft["body"]["warrant"]["premises"]:
        landed = ("transient" in p["statement"] or "fault" in p["statement"]) and ev.get("fault_rate") == 0
        claims.append({"target": f"premise:{p['id']}", "refutation": p["falsifier"], "reading_taken": True, "landed": landed,
                       "evidence": [f"fault_rate={ev.get('fault_rate')}"]})
    decision = draft["body"]["decision"].lower()
    copied = any(t in decision for t in ev.get("task_ids", []))
    claims.append({"target": "payload:abstraction", "refutation": "the payload names a task instead of the transferable shape",
                   "reading_taken": True, "landed": copied, "evidence": ["the payload text"]})
    return {"claims": claims}


# --- the adjudicator ----------------------------------------------------------------------------

@handles("verdict")
def _verdict(req):
    attack, oracle = req["attack"], req.get("oracle", {})
    for c in attack["claims"]:
        if c["landed"] and c["target"].startswith("premise:"):
            return {"verdict": f"decline(premise killed: {c['target']})", "amendment": None}
        if c["landed"] and c["target"] == "warrant:independence":
            return {"verdict": "decline(bar unmet: observations are not independent)", "amendment": None}
        if c["landed"] and c["target"] == "payload:abstraction":
            return {"verdict": "decline(payload is a copied instance; promotion raises abstraction)", "amendment": None}
    scorer = req.get("watch_scorer")
    series = oracle.get("series", {}).get(scorer, [])
    if scorer and series and all(v is None for v in series):
        return {"verdict": f"escalate(oracle evidence unevaluable for {scorer})", "amendment": None, "until": None}
    if scorer and series and any(v is None for v in series):  # evidence partly missing and forthcoming: wait for two evaluable runs
        return {"verdict": f"defer(until {scorer} is evaluable on two consecutive runs)", "amendment": None,
                "until": {"scorer": scorer, "comparator": ">=", "value": 0.0, "persistence": 2, "passes": None}}
    return {"verdict": "admit", "amendment": None, "until": None}


@handles("credit")
def _credit(req):
    steers = []
    for a in req["applied"]:
        before, after = a.get("before"), a.get("after")
        if a["applied_count"] > 0 and before is not None and after is not None and after <= before:
            steers.append({"record": a["record"], "slot": "payload", "signature": "recalled-applied-still-corrected",
                           "correction": f"{a['record']} was applied in {a['applied_count']} dispositions and {a['scorer']} did not improve ({before} → {after})",
                           "why_not_caught": "no floor reads the payload's content; residue as disclosed"})
    return {"steers": steers}


@handles("vocabulary")
def _vocabulary(req):
    covered = [t for t in req.get("coder", []) if not t.startswith("other(")]
    if covered:
        return {"verdict": f"decline(the blind coder read the presentations as {covered}; an existing term covers the shape)", "means": None}
    return {"verdict": "admit", "means": f"the presentation {len(req['escapes'])} independent passes escaped to as other({req['term']}); minted by recurrence"}


@handles("currency")
def _currency(req):
    if req.get("rotted"):
        if req.get("successor"):
            return {"verdict": "still-holds", "why": f"the anchors {req['rotted']} retired into {req['successor']}, which stands for them", "premise": None}
        return {"verdict": "reversed", "why": f"the anchors {req['rotted']} retired with no successor; the warrant cites nothing that stands", "premise": None}
    if req.get("successor"):
        return {"verdict": "reversed", "why": f"the premise is superseded by {req['successor']}", "premise": None}
    ratio = req.get("applied_over_considered")
    if ratio is not None and ratio < req.get("threshold", 0.1) and req.get("moot_evidence"):
        return {"verdict": "moot", "why": "the domain is no longer entered"}
    return {"verdict": "still-holds", "why": "the premise stands; the fire is corroborating evidence against the payload, not the warrant", "premise": None}
