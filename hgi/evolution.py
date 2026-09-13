"""The evolution log: what a stream arm learned, batch by batch, read back from its store.

A stream arm (:mod:`suite.stream`) meets a new batch every pass, so its
curve is first-sight performance on unseen tasks as the store grows. This
module derives, from the arm's store and its recorded deal, the log that
makes that curve legible — nothing here is written during the run:

- per pass: the batch, its tasks and their lessons, each row's **symptom**
  (:func:`suite.lessons.symptom` — ``pass``, ``naive`` when the row
  reproduces the task's naive first-contact outcome, ``wrong``, or
  ``error:<class>``), the records the pass had in context and which lessons
  they mention (a keyword heuristic over the record's text, logged as such),
  the observations it filed, and what the consolidation after it admitted,
  declined, retired or dismissed;
- per pass and per lesson, the **quality** of the solutions beside their
  correctness: ``economy`` (the knowing policy's calls over the calls
  spent, zero on a failed row — derived here from the row's call counts and
  the task's knowing floor, so it reads on runs the oracle scored before
  the series existed), ``turns`` (the same over model turns) and
  ``transfer`` (the last shell command replayed in the task's twin), the
  latter two read off the oracle's scores where the run recorded them;
- per lesson: the first-sight series over the stream, the naive-shape
  failures before and after the first pass that had a record mentioning
  the lesson in context — the same-shape recurrence the memory is supposed
  to stop — and the revisit outcome where a batch was met again;
- per experiment: the attached arm against the detached arm on the same
  batches, paired per batch and per lesson.

Every count is a floor from one run: a lesson met once a batch is one
sample a batch, and a record that mentions a lesson is not thereby the
record that taught it.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

import suite as _suite
from hgi import registry as _registry
from hgi.index import row_passed
from suite import lessons as _lessons
from suite.stream import key_of

SYMBOL = {"pass": "✓", "naive": "N", "wrong": "W"}
"""One character per symptom in the lesson grid; an ``error:<class>`` symptom prints as ``E``."""


def _symbol(symptom: str) -> str:
    return SYMBOL.get(symptom, "E")


def economy_of(task, row: dict[str, Any]) -> float | None:
    """The row's solution economy from its call counts and the task's knowing floor: ``None`` where the task declares none."""
    if not task.knowing:
        return None
    if not row_passed(row):
        return 0.0
    used = sum(row.get(f"{tool}_calls", 0) for tool in task.knowing)
    return min(1.0, sum(task.knowing.values()) / used) if used else 1.0


def _score(row: dict[str, Any], series: str) -> float | None:
    return ((row.get("scores") or {}).get(series) or {}).get("value")


def _mean(values: list[float | None]) -> float | None:
    xs = [v for v in values if v is not None]
    return sum(xs) / len(xs) if xs else None


def _record_text(store, record: str) -> str:
    d = store.read("decision", record)
    return " ".join([d.decision, d.summary.latch, d.context, " ".join(d.summary.not_this)])


def arm_log(exp, arm: str, root: Path | None = None) -> dict[str, Any] | None:
    """The arm's evolution log, or ``None`` when the arm is not a stream arm or has not run."""
    from hgi import experiment as _experiment
    from hgi.store import Store

    spec = exp.resolve(arm)
    where = _experiment.arm_dir(exp, arm, root)
    if spec.stream is None or not (where / "arm.json").exists() or not (where / "store" / "registry").exists():
        return None
    record = json.loads((where / "arm.json").read_text())
    batches = spec.batches()
    recorded = {b["batch"]: b["hash"] for b in record["stream"]["batches"]}
    dealt = {n: b.hash for n, b in enumerate(batches, 1)}
    warning = None
    if recorded != dealt:
        # the pool changed since the arm ran (a budget, a prompt): the batches are rebuilt from the task ids the arm recorded, so the
        # log still reads the arm that ran, and says so
        from suite.tasks import Suite, build

        pool = build(spec.stream.pool_spec).by_id
        missing = sorted({t for b in record["stream"]["batches"] for t in b["tasks"] if t not in pool})
        if missing:
            raise SystemExit(f"{exp.name}/{arm}: the pool has changed since the arm ran and no longer holds {', '.join(missing[:5])}")
        batches = [Suite(spec=spec.stream.pool_spec, tasks=[pool[t] for t in b["tasks"]]) for b in record["stream"]["batches"]]
        warning = "the pool has changed since the arm ran; batches rebuilt from the recorded task ids, hashes differ"
    batch_of = {int(k): v for k, v in record["stream"]["passes"].items()}
    reg = _registry.load(where / "store")
    token = _registry.use(reg)
    try:
        store = Store(where / "store", registry=reg)
        sessions = sorted((s for s in store.all("session") if s.attached == (spec.mode == "attached") and s.evaluation is not None), key=lambda s: s.pass_)
        consolidations = {k.after_pass: k for k in store.all("consolidation")}
        accepted = {d.id: d for d in store.all("decision")}
        bar = int(store.registry.bars.get("decision", {}).get("independent_observations", 2))
        passes = [_pass_entry(store, s, batch_of[s.pass_], batches[batch_of[s.pass_] - 1], s.pass_ > spec.passes, consolidations.get(s.pass_), accepted, bar)
                  for s in sessions if s.pass_ in batch_of]
    finally:
        _registry.reset(token)
    log = {"experiment": exp.name, "arm": arm, "mode": spec.mode, "model": record["roster"]["pass"], "roster": record["roster"], "warning": warning,
           "stream": spec.stream.model_dump(mode="json"), "passes": passes, "lessons": _lesson_series(passes),
           "records": [{"id": d.id, "admitted_after_pass": _admitted_after(consolidations, d.id), "decision": d.decision, "hook": d.consultation_terms,
                        "mentions": [l for l in _lessons.LESSONS if _lessons.mentions(l, " ".join([d.decision, d.summary.latch, d.context]))],
                        "status": d.lifecycle.status if hasattr(d.lifecycle, "status") else None}
                       for d in sorted(accepted.values(), key=lambda d: d.id)]}
    return log


def _admitted_after(consolidations: dict[int, Any], record: str) -> int | None:
    return next((n for n, k in sorted(consolidations.items()) if record in k.admitted), None)


def _pass_entry(store, session, batch: int, suite, revisit: bool, consolidation, accepted: dict[str, Any], bar: int) -> dict[str, Any]:
    token = _suite.use(suite)
    try:
        rows = []
        for row in session.evaluation.rows:
            task = suite.by_id.get(row["task"])
            if task is None:
                continue
            rows.append({"task": task.id, "lesson": key_of(task), "symptom": _lessons.symptom(task, row), "applied": row.get("applied", []),
                         "error": row.get("error"), "result": row.get("result"), "call": row.get("call"),
                         "economy": economy_of(task, row), "turns": _score(row, "turn_economy"), "transfer": _score(row, "method_transfer"),
                         "calls": {"shell": row.get("shell_calls"), "http": row.get("http_calls"), "turns": row.get("turns")}, "commands": row.get("commands")})
    finally:
        _suite.reset(token)
    in_context = [c.record for c in session.considered if c.guard_passed and c.via != "constitution" and c.record in accepted]
    mentions = {l: [r for r in in_context if _lessons.mentions(l, _record_text(store, r))] for l in _lessons.LESSONS}
    scored = [r for r in rows if r["symptom"] != "unevaluable"]
    entry = {"pass": session.pass_, "session": session.id, "batch": batch, "kind": "revisit" if revisit else "stream", "hash": suite.hash,
             "pass_rate": (sum(r["symptom"] == "pass" for r in scored) / len(scored)) if scored else None,
             "quality": {q: _mean([r[q] for r in rows]) for q in ("economy", "turns", "transfer")},
             "symptoms": dict(Counter(r["symptom"] for r in rows)), "rows": rows,
             "in_context": in_context, "mentions": {l: ids for l, ids in mentions.items() if ids},
             "work_shape": session.work_shape.terms, "proposals": len(session.proposals),
             "observations": [{"name": o.name, "noticed": o.noticed, "shape": o.shape, "state": o.disposition.state}
                              for o in store.observations(state=None) if o.name in session.observations_filed],
             "consolidation": None}
    if consolidation is not None:
        outcomes = Counter((n.outcome or "pending").split("(")[0] for n in consolidation.nominations if not n.subject.startswith("C-"))
        anchoring = Counter((n.outcome or "pending").split("(")[0] for n in consolidation.nominations if n.subject.startswith("C-"))
        groups = [{"shape": g.get("shape"), "sessions": g.get("sessions", []), "observations": g.get("observations", []),
                   "at_bar": len(g.get("sessions", [])) >= bar} for g in consolidation.brief.get("groups", []) if isinstance(g, dict)]
        entry["consolidation"] = {"id": consolidation.id, "admitted": consolidation.admitted, "flipped": consolidation.flipped,
                                  "nominations": [{"subject": n.subject, "rung": n.rung, "outcome": n.outcome} for n in consolidation.nominations if not n.subject.startswith("C-")],
                                  "outcomes": dict(outcomes), "anchoring": dict(anchoring), "retired": consolidation.retired, "dismissed": consolidation.dismissed,
                                  "expired": consolidation.expired, "groups": groups, "groups_at_bar": sum(g["at_bar"] for g in groups)}
    return entry


def _lesson_series(passes: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for p in passes:
        for lesson in sorted({r["lesson"] for r in p["rows"]}):
            rows = [r for r in p["rows"] if r["lesson"] == lesson]
            series = out.setdefault(lesson, {"tier": _lessons.tier(lesson), "series": [], "first_mention_pass": None})
            mentioned = bool(p["mentions"].get(lesson))
            if mentioned and series["first_mention_pass"] is None and p["kind"] == "stream":
                series["first_mention_pass"] = p["pass"]
            series["series"].append({"pass": p["pass"], "batch": p["batch"], "kind": p["kind"], "tasks": len(rows),
                                     "quality": {q: _mean([r[q] for r in rows]) for q in ("economy", "turns", "transfer")},
                                     "passed": sum(r["symptom"] == "pass" for r in rows), "naive": sum(r["symptom"] == "naive" for r in rows),
                                     "other": sum(r["symptom"] not in ("pass", "naive") for r in rows), "mentioned": mentioned,
                                     "grid": "".join(_symbol(r["symptom"]) for r in rows)})
    for lesson, series in out.items():
        first = series["first_mention_pass"]
        stream = [s for s in series["series"] if s["kind"] == "stream"]
        before = [s for s in stream if first is None or s["pass"] < first]
        after = [s for s in stream if first is not None and s["pass"] >= first]
        series["naive_before"] = (sum(s["naive"] for s in before), sum(s["tasks"] for s in before))
        series["naive_after"] = (sum(s["naive"] for s in after), sum(s["tasks"] for s in after))
        series["first_sight"] = (sum(s["passed"] for s in stream), sum(s["tasks"] for s in stream))
        series["quality"] = {q: _mean([s["quality"][q] for s in stream]) for q in ("economy", "turns", "transfer")}
        series["revisit"] = [(s["batch"], s["passed"], s["tasks"]) for s in series["series"] if s["kind"] == "revisit"]
    return out


# --- rendering ------------------------------------------------------------------------------------

def _rate(num: int, den: int) -> str:
    return f"{num / den:.2f} ({num}/{den})" if den else "—"


def _q(quality: dict[str, float | None]) -> str:
    """``economy / turns / transfer`` means, ``—`` where nothing was evaluable."""
    return " / ".join("—" if quality.get(q) is None else f"{quality[q]:.2f}" for q in ("economy", "turns", "transfer"))


def arm_markdown(log: dict[str, Any]) -> str:
    st = log["stream"]
    lines = [f"# {log['experiment']}/{log['arm']} — evolution", "",
             f"{log['mode']} on `{log['model']}`; {st['batches']} batches × {st['batch']} tasks from {'+'.join(st['families'])}, seed {st['seed']}"
             + (f"; revisit {st['revisit']}" if st["revisit"] else "") + ".", ""] + ([f"> {log['warning']}", ""] if log.get("warning") else []) + [
             "## Passes", "", "| pass | batch | first sight | economy / turns / transfer | symptoms | in context | mentions | filed | consolidation after |", "|---|---|---|---|---|---|---|---|---|"]
    for p in log["passes"]:
        sym = " ".join(f"{k}={v}" for k, v in sorted(p["symptoms"].items()))
        k = p["consolidation"]
        kk = "" if k is None else (f"{k['id']}: {len(k['groups'])} groups, {k['groups_at_bar']} at the bar; admitted {' '.join(k['admitted']) or 'nothing'}"
                                   + (f"; {', '.join(f'{v} {o}' for o, v in sorted(k['outcomes'].items()))}" if k["outcomes"] else "; nothing nominated")
                                   + (f"; retired {' '.join(k['retired'])}" if k["retired"] else "") + (f"; dismissed {len(k['dismissed'])}" if k["dismissed"] else ""))
        lines.append(f"| {p['pass']}{' (revisit)' if p['kind'] == 'revisit' else ''} | {p['batch']} | {'—' if p['pass_rate'] is None else f'{p['pass_rate']:.2f}'} | {_q(p['quality'])} | {sym} | "
                     f"{' '.join(p['in_context']) or 'none'} | {', '.join(f'{l}: {' '.join(ids)}' for l, ids in p['mentions'].items()) or '—'} | "
                     f"{len(p['observations'])} obs, {p['proposals']} prop | {kk} |")
    lines += ["", "## Lessons", "", "Each cell is the lesson's rows in that pass: ✓ passed, N the naive first-contact outcome (a same-shape failure), "
              "W another wrong answer, E a harness or tool error. `mentioned` marks passes with a record in context whose text uses the lesson's words.", "",
              "| lesson | tier | " + " | ".join(f"p{p['pass']}" + ("r" if p["kind"] == "revisit" else "") for p in log["passes"]) +
              " | first sight | economy / turns / transfer | naive before / after first mention | first mention | revisit |",
              "|---|---|" + "---|" * len(log["passes"]) + "---|---|---|---|---|"]
    by_pass = {p["pass"]: p for p in log["passes"]}
    for lesson, s in sorted(log["lessons"].items(), key=lambda kv: (_lessons.TIERS.index(kv[1]["tier"]) if kv[1]["tier"] in _lessons.TIERS else 9, kv[0])):
        cells = {x["pass"]: x["grid"] + ("*" if x["mentioned"] else "") for x in s["series"]}
        lines.append(f"| {lesson} | {s['tier'] or '—'} | " + " | ".join(cells.get(p, "") for p in by_pass) + f" | {_rate(*s['first_sight'])} | {_q(s['quality'])} | "
                     f"{_rate(*s['naive_before'])} / {_rate(*s['naive_after'])} | {s['first_mention_pass'] or '—'} | "
                     + (", ".join(f"batch {b}: {p}/{n}" for b, p, n in s["revisit"]) or "—") + " |")
    lines += ["", "## What the passes noticed", "", "Each observation as the close filed it, with the shape the blind coder gave it at the next "
              "consolidation (`open` until one has run); a group reaches the bar when its observations come from as many distinct sessions as the bar asks.", ""]
    for p in log["passes"]:
        for o in p["observations"]:
            lines.append(f"- pass {p['pass']} {o['name']} [{', '.join(o['shape'] or []) or o['state']}]: {o['noticed']}")
        k = p["consolidation"]
        if k is not None:
            for g in k["groups"]:
                lines.append(f"- {k['id']} group [{', '.join(g['shape'] or [])}] ← {' '.join(g['observations'])} from {' '.join(g['sessions'])}"
                             + (" — at the bar" if g["at_bar"] else " — below the bar"))
            for n in k["nominations"]:
                lines.append(f"- {k['id']} nominated {n['subject']} at {n['rung']} → {n['outcome']}")
    if not any(p["observations"] for p in log["passes"]):
        lines.append("Nothing was filed.")
    lines += ["", "## Records", ""]
    if log["records"]:
        lines += ["| record | admitted after pass | mentions | decision |", "|---|---|---|---|"]
        lines += [f"| {r['id']} | {r['admitted_after_pass'] or '—'} | {', '.join(r['mentions']) or '—'} | {r['decision']} |" for r in log["records"]]
    else:
        lines.append("No decision was admitted.")
    return "\n".join(lines) + "\n"


def experiment_markdown(exp, logs: dict[str, dict[str, Any]]) -> str:
    lines = [f"# {exp.name} — evolution" + (f": {exp.description}" if exp.description else ""), ""]
    if not logs:
        return "\n".join(lines + ["No stream arm has run."]) + "\n"
    first = next(iter(logs.values()))
    st = first["stream"]
    lines += [f"{st['batches']} batches × {st['batch']} tasks from {'+'.join(st['families'])}, seed {st['seed']}; every arm meets the same batches in the same order. "
              "A pass's score is first sight — nothing in the store was learned on that batch — so the curve is performance on unseen tasks as the store grows.", "",
              "## First sight, per batch", "", "Pass rate, then economy / turns / transfer per arm.", "",
              "| batch | " + " | ".join(logs) + " | " + " | ".join(f"{a} quality" for a in logs) + " | in context (attached) | consolidation after |", "|---|" + "---|" * (2 * len(logs) + 2)]
    stream_passes = {arm: {p["batch"]: p for p in log["passes"] if p["kind"] == "stream"} for arm, log in logs.items()}
    for b in range(1, st["batches"] + 1):
        cells = []
        for arm in logs:
            p = stream_passes[arm].get(b)
            cells.append("—" if p is None or p["pass_rate"] is None else f"{p['pass_rate']:.2f}")
        for arm in logs:
            p = stream_passes[arm].get(b)
            cells.append("—" if p is None else _q(p["quality"]))
        attached = next((stream_passes[a].get(b) for a, l in logs.items() if l["mode"] == "attached"), None)
        ctx = " ".join(attached["in_context"]) if attached else "—"
        k = attached["consolidation"] if attached else None
        lines.append(f"| {b} | " + " | ".join(cells) + f" | {ctx or 'none'} | " + ("" if not k else f"admitted {' '.join(k['admitted']) or 'nothing'}") + " |")
    totals = []
    for arm, log in logs.items():
        ps = [p for p in log["passes"] if p["kind"] == "stream"]
        rows = [r for p in ps for r in p["rows"]]
        num = sum(r["symptom"] == "pass" for r in rows)
        totals.append(f"{arm} {_rate(num, len(rows))}, quality {_q({q: _mean([r[q] for r in rows]) for q in ('economy', 'turns', 'transfer')})}")
    lines += ["", "Over the stream: " + "; ".join(totals) + ".", ""]
    lines += ["## First sight, per lesson", "", "Pass rate per arm, then economy / turns / transfer per arm.", "",
              "| lesson | tier | " + " | ".join(logs) + " | " + " | ".join(f"{a} quality" for a in logs) + " | naive-shape before / after first mention (attached) | first mention |",
              "|---|---|" + "---|" * (2 * len(logs) + 2)]
    lessons = sorted({l for log in logs.values() for l in log["lessons"]}, key=lambda l: (_lessons.TIERS.index(_lessons.tier(l)) if _lessons.tier(l) else 9, l))
    for lesson in lessons:
        cells = [_rate(*log["lessons"][lesson]["first_sight"]) if lesson in log["lessons"] else "—" for log in logs.values()]
        cells += [_q(log["lessons"][lesson]["quality"]) if lesson in log["lessons"] else "—" for log in logs.values()]
        att = next((log["lessons"].get(lesson) for log in logs.values() if log["mode"] == "attached"), None)
        lines.append(f"| {lesson} | {_lessons.tier(lesson) or '—'} | " + " | ".join(cells) + " | " +
                     (f"{_rate(*att['naive_before'])} / {_rate(*att['naive_after'])} | {att['first_mention_pass'] or '—'}" if att else "— | —") + " |")
    revisits = [(arm, s["batch"], s["passed"], s["tasks"], lesson) for arm, log in logs.items() for lesson, ls in log["lessons"].items() for s in ls["series"] if s["kind"] == "revisit"]
    if revisits:
        lines += ["", "## Revisit", ""]
        for arm, log in logs.items():
            for p in log["passes"]:
                if p["kind"] != "revisit":
                    continue
                first_sight = stream_passes[arm].get(p["batch"])
                lines.append(f"- {arm}: batch {p['batch']} scored {'—' if not first_sight or first_sight['pass_rate'] is None else f'{first_sight['pass_rate']:.2f}'} at first sight (pass {first_sight['pass'] if first_sight else '?'}) "
                             f"and {'—' if p['pass_rate'] is None else f'{p['pass_rate']:.2f}'} when met again at pass {p['pass']} with {' '.join(p['in_context']) or 'nothing'} in context.")
    lines += ["", "## Records admitted", ""]
    any_record = False
    for arm, log in logs.items():
        for r in log["records"]:
            any_record = True
            lines.append(f"- {arm} {r['id']} (after pass {r['admitted_after_pass'] or '?'}; mentions {', '.join(r['mentions']) or 'no lesson'}): {r['decision']}")
    if not any_record:
        lines.append("None.")
    lines += ["", "## Reading", "",
              "A symptom is derived, not judged: `naive` means the row's result equals what the task's scripted first-contact policy returns "
              "(or its error is of the same class), so a naive-shape failure after a record for the lesson was in context is the same shape recurring "
              "with the memory attached. Quality grades a passed solution: `economy` is the knowing policy's calls over the calls spent (zero on a failed row), "
              "`turns` the same over model turns, `transfer` whether the last shell command replayed in the task's twin world gives the twin's answer — "
              "a pass that knows a convention spends less and its method carries, where one that discovers it spends the discovery and may not. "
              "`mentions` is a keyword heuristic over a record's text and is logged as one. Every count is from one run and is a floor."]
    return "\n".join(lines) + "\n"


def write(exp, arm: str, root: Path | None = None) -> dict[str, Any] | None:
    """Write ``evolution.json`` and ``evolution.md`` beside the arm's store; return the log."""
    from hgi import experiment as _experiment

    log = arm_log(exp, arm, root)
    if log is None:
        return None
    where = _experiment.arm_dir(exp, arm, root)
    (where / "evolution.json").write_text(json.dumps(log, indent=2, sort_keys=True, default=str) + "\n")
    (where / "evolution.md").write_text(arm_markdown(log))
    return log


def write_experiment(exp, root: Path | None = None) -> str:
    """Every stream arm's log, written beside its store, and the experiment's paired report at ``runs/<experiment>/evolution.md``."""
    from hgi import experiment as _experiment

    logs = {arm: log for arm in exp.arms if (log := write(exp, arm, root)) is not None}
    text = experiment_markdown(exp, logs)
    out = (root or _experiment.runs_root()) / exp.name
    out.mkdir(parents=True, exist_ok=True)
    (out / "evolution.md").write_text(text)
    return text
