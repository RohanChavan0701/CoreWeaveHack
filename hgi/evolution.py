"""The evolution log: what a stream arm learned, batch by batch, read back from its store.

A stream arm (:mod:`suite.stream`) meets a new batch every pass, so its
curve is first-sight performance on unseen tasks as the store grows. This
module derives, from the arm's store and its recorded deal, the log that
makes that curve legible — nothing here is written during the run:

- per pass: the batch, its tasks and their lessons, each row's **symptom**
  (:func:`suite.lessons.symptom` — ``pass``, ``naive`` when the row
  reproduces the task's naive first-contact outcome, ``wrong``, or
  ``error:<class>``), the records the pass had in context, which records
  **fired** on each lesson's rows and how those rows then turned out (the
  applied-vs-outcome join, read off ``rows[].applied`` and the row's
  symptom — the signal the series pivots on), which lessons the in-context
  records mention (a keyword heuristic over the record's text, kept and
  logged as a heuristic, not the driving signal), the observations it filed,
  and what the consolidation after it admitted, declined, retired or
  dismissed;
- per pass and per lesson, the **quality** of the solutions beside their
  correctness: ``economy`` (the knowing policy's calls over the calls
  spent, zero on a failed row — derived here from the row's call counts and
  the task's knowing floor, so it reads on runs the oracle scored before
  the series existed), ``turns`` (the same over model turns) and
  ``transfer`` (the last shell command replayed in the task's twin), the
  latter two read off the oracle's scores where the run recorded them;
- per lesson: the first-sight series over the stream, the naive-shape
  failures before and after the first pass a record **fired** on the
  lesson's rows (``first_applied_pass`` — a record appearing in some row's
  ``applied`` for that lesson, not a keyword mention) — the same-shape
  recurrence the memory is supposed to stop — and the revisit outcome where
  a batch was met again;
- per experiment: the attached arm against the detached arm on the same
  batches, paired per batch and per lesson.

Every count is a floor from one run: a lesson met once a batch is one
sample a batch, and a record that fired on a lesson's rows is not thereby
the record that helped — the applied-vs-outcome join is what says whether
the rows it fired on then passed.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

import suite as _suite
from hgi import registry as _registry
from hgi.index import observation_for, row_passed
from suite import lessons as _lessons
from suite.stream import key_of


def evaluated_sessions(store, mode: str) -> list:
    """The arm's evaluated sessions of ``mode``, in pass order — attached sessions for an attached arm, detached for a detached one."""
    attached = mode == "attached"
    return sorted((s for s in store.all("session") if s.attached == attached and s.evaluation is not None), key=lambda s: s.pass_)


def in_context_records(session, accepted) -> list[str]:
    """The records a pass actually had in context: guard-passed, not the constitution, and still an accepted decision the
    store holds. Empty where retrieval reached nothing — the silent failure a flat pass rate hides (reasoning-core, economy)."""
    return [c.record for c in session.considered if c.guard_passed and c.via != "constitution" and c.record in accepted]


# --- mid-run health ---------------------------------------------------------------------------

def _row_error_classes(row: dict[str, Any]) -> list[str]:
    """The tool/harness error classes a row carries — its final error and every tool error in its trace, by the tool
    layer's own markers (:func:`suite.lessons.error_class`). A row that recovered from a broken call and answered wrong
    still shows the call here through ``tool_errors``, which its final symptom does not."""
    classes = [_lessons.error_class(e) for e in (row.get("tool_errors") or [])]
    if row.get("error"):
        classes.append(_lessons.error_class(row["error"]))
    return classes


def _consolidation_disposition(consolidation) -> dict[str, Any]:
    """A consolidation's drafts by disposition: how many were nominated, how many admitted, and the bucket each
    nomination's outcome fell in — ``admitted``, ``refused_floor`` (the contract floor refused the draft),
    ``declined``, ``escalated``, ``deferred`` or ``pending``. ``nominated`` > 0 with ``admitted`` == 0 is the
    everything-drafted-nothing-admitted failure (text2sql, economy); ``nominated`` == 0 is nothing to learn."""
    def bucket(outcome: str | None) -> str:
        o = outcome or "pending"
        for prefix, name in (("admitted", "admitted"), ("refused by the floor", "refused_floor"),
                             ("declined", "declined"), ("escalated", "escalated"), ("defer", "deferred")):
            if o.startswith(prefix):
                return name
        return "pending"

    drafts = [n for n in consolidation.nominations if not n.subject.startswith("C-")]
    return {"id": consolidation.id, "nominated": len(drafts), "admitted": len(consolidation.admitted),
            "outcomes": dict(Counter(bucket(n.outcome) for n in drafts))}


def health(store, mode: str) -> dict[int, dict[str, Any]]:
    """The arm's per-pass health as it runs, derived from the store on disk — no model call, nothing that slows the arm.

    For each evaluated session of ``mode``, keyed by pass:

    - ``reach``: the records ``considered`` and, of those, the ``in_context`` count and ids a pass actually consulted
      (:func:`in_context_records`). Empty ``in_context`` on a pass that carries a store is retrieval reaching nothing —
      the reasoning-core/economy silent failure, and, on a seeded arm, the pass-1 tripwire that the latch scope is wrong.
    - ``errors``: the ``rows`` scored, the ``tool_error_rows`` that hit a tool or harness error, and the count ``by_class``
      over every such error (final and in-trace). A spike in a harness class (``endpoint``, ``shell-exit``,
      ``malformed-tool-call``) is a broken arm; a world-fault class (``http-410``) is the task's own content.
    - ``coverage``: the ``failed`` rows, how many the pass ``observed`` (filed an observation from), and how many of those
      are ``shaped`` — whether the close is filing from the failures at all.
    - ``consolidation``: the round's draft disposition (:func:`_consolidation_disposition`), or ``None`` on a pass that
      closed no round.

    A detached arm has no store, so its ``reach``, ``coverage`` and ``consolidation`` are empty by construction and only
    ``errors`` carries signal — the ablation's own bad-call rate."""
    accepted = {d.id for d in store.all("decision")}
    obs_by_session: dict[str, list] = {}
    for o in store.observations(state=None):
        obs_by_session.setdefault(o.session, []).append(o)
    consolidations = {k.after_pass: k for k in store.all("consolidation")}
    out: dict[int, dict[str, Any]] = {}
    for s in evaluated_sessions(store, mode):
        rows = s.evaluation.rows
        session_obs = obs_by_session.get(s.id, [])
        failed = [(row, observation_for(session_obs, row)) for row in rows if not row_passed(row)]
        ic = in_context_records(s, accepted)
        k = consolidations.get(s.pass_)
        out[s.pass_] = {
            "pass": s.pass_,
            "reach": {"considered": len(s.considered), "in_context": len(ic), "records": ic},
            "errors": {"rows": len(rows), "tool_error_rows": sum(1 for row in rows if _row_error_classes(row)),
                       "by_class": dict(Counter(c for row in rows for c in _row_error_classes(row)))},
            "coverage": {"failed": len(failed), "observed": sum(o is not None for _, o in failed),
                         "shaped": sum(o is not None and bool(o.shape) for _, o in failed)},
            "consolidation": _consolidation_disposition(k) if k is not None else None,
        }
    return out

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
    batches, warning = _experiment.recorded_batches(spec, record)
    if r := record.get("retrofit"):
        # the rows are the source arm's and the store today's backward pass over them (hgi.retrofit): the log reads the store, not a run
        warning = (f"retrofitted from {r['source_experiment']}/{r['source_arm']} (store at {str(r.get('source_commit') or '?')[:7]}) on {r['date'][:10]}: "
                   f"the rows are the source arm's, unchanged; the backward pass is today's code on {r['teacher']}; nothing was in context at any "
                   f"pass — not a live run" + (f"; {warning}" if warning else ""))
    batch_of = {int(k): v for k, v in record["stream"]["passes"].items()}
    reg = _registry.load(where / "store")
    token = _registry.use(reg)
    try:
        store = Store(where / "store", registry=reg)
        sessions = evaluated_sessions(store, spec.mode)
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
                        "fired": _record_fired(passes, d.id),
                        "status": d.lifecycle.status if hasattr(d.lifecycle, "status") else None}
                       for d in sorted(accepted.values(), key=lambda d: d.id)]}
    return log


def _record_fired(passes: list[dict[str, Any]], record: str) -> dict[str, Any]:
    """Where a record actually fired: the rows it was applied on, how many passed, and the lessons and passes touched."""
    hits = [(p["pass"], r) for p in passes for r in p["rows"] if record in r["applied"]]
    return {"rows": len(hits), "passed": sum(r["symptom"] == "pass" for _, r in hits),
            "lessons": sorted({r["lesson"] for _, r in hits}), "passes": sorted({n for n, _ in hits}),
            "first_pass": min((n for n, _ in hits), default=None)}


def _admitted_after(consolidations: dict[int, Any], record: str) -> int | None:
    return next((n for n, k in sorted(consolidations.items()) if record in k.admitted), None)


def _applied_join(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Per lesson, the records that fired on its rows this pass and how those fired-on rows turned out.

    The real signal the series pivots on: a record ``fired`` on a row when its id is in ``rows[].applied`` (empty
    on rows and arms that recorded none — such a lesson simply does not appear here). Only rows a record fired on
    are counted, so ``passed + naive + other == tasks`` reads as the applied-vs-outcome join for that lesson."""
    out: dict[str, dict[str, Any]] = {}
    for lesson in sorted({r["lesson"] for r in rows}):
        fired_rows = [r for r in rows if r["lesson"] == lesson and r["applied"]]
        if not fired_rows:
            continue
        out[lesson] = {"records": sorted({rid for r in fired_rows for rid in r["applied"]}),
                       "passed": sum(r["symptom"] == "pass" for r in fired_rows),
                       "naive": sum(r["symptom"] == "naive" for r in fired_rows),
                       "other": sum(r["symptom"] not in ("pass", "naive") for r in fired_rows),
                       "tasks": len(fired_rows)}
    return out


def _pass_entry(store, session, batch: int, suite, revisit: bool, consolidation, accepted: dict[str, Any], bar: int) -> dict[str, Any]:
    token = _suite.use(suite)
    try:
        rows = []
        for row in session.evaluation.rows:
            task = suite.by_id.get(row["task"])
            if task is None:
                continue
            # only records this arm's store still holds: a retrofit's rows are the source arm's and carry the source's
            # applied ids, which this store does not know — those did not fire on this arm and must not read as if they did
            rows.append({"task": task.id, "lesson": key_of(task), "symptom": _lessons.symptom(task, row),
                         "applied": [rid for rid in row.get("applied", []) if rid in accepted],
                         "error": row.get("error"), "result": row.get("result"), "call": row.get("call"),
                         "economy": economy_of(task, row), "turns": _score(row, "turn_economy"), "transfer": _score(row, "method_transfer"),
                         "calls": {"shell": row.get("shell_calls"), "http": row.get("http_calls"), "turns": row.get("turns")}, "commands": row.get("commands")})
    finally:
        _suite.reset(token)
    in_context = in_context_records(session, accepted)
    mentions = {l: [r for r in in_context if _lessons.mentions(l, _record_text(store, r))] for l in _lessons.LESSONS}
    applied = _applied_join(rows)
    scored = [r for r in rows if r["symptom"] != "unevaluable"]
    entry = {"pass": session.pass_, "session": session.id, "batch": batch, "kind": "revisit" if revisit else "stream", "hash": suite.hash,
             "pass_rate": (sum(r["symptom"] == "pass" for r in scored) / len(scored)) if scored else None,
             "quality": {q: _mean([r[q] for r in rows]) for q in ("economy", "turns", "transfer")},
             "symptoms": dict(Counter(r["symptom"] for r in rows)), "rows": rows,
             "in_context": in_context, "mentions": {l: ids for l, ids in mentions.items() if ids}, "applied": applied,
             "work_shape": session.work_shape.terms, "proposals": len(session.proposals),
             "observations": [{"name": o.name, "happened": o.happened, "turned_on": o.turned_on, "shape": o.shape, "state": o.disposition.state}
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
            series = out.setdefault(lesson, {"tier": _lessons.tier(lesson), "series": [], "first_applied_pass": None, "first_mention_pass": None})
            mentioned = bool(p["mentions"].get(lesson))
            aj = p["applied"].get(lesson)
            applied = aj is not None
            if applied and series["first_applied_pass"] is None and p["kind"] == "stream":
                series["first_applied_pass"] = p["pass"]
            if mentioned and series["first_mention_pass"] is None and p["kind"] == "stream":
                series["first_mention_pass"] = p["pass"]
            series["series"].append({"pass": p["pass"], "batch": p["batch"], "kind": p["kind"], "tasks": len(rows),
                                     "quality": {q: _mean([r[q] for r in rows]) for q in ("economy", "turns", "transfer")},
                                     "passed": sum(r["symptom"] == "pass" for r in rows), "naive": sum(r["symptom"] == "naive" for r in rows),
                                     "other": sum(r["symptom"] not in ("pass", "naive") for r in rows), "mentioned": mentioned,
                                     "applied": applied, "applied_records": aj["records"] if aj else [],
                                     "applied_passed": aj["passed"] if aj else 0, "applied_naive": aj["naive"] if aj else 0,
                                     "applied_other": aj["other"] if aj else 0, "applied_tasks": aj["tasks"] if aj else 0,
                                     "grid": "".join(_symbol(r["symptom"]) for r in rows)})
    for lesson, series in out.items():
        # the driving signal is firing, not keyword mention: before/after split on the first pass a record fired on the lesson's rows
        first = series["first_applied_pass"]
        stream = [s for s in series["series"] if s["kind"] == "stream"]
        before = [s for s in stream if first is None or s["pass"] < first]
        after = [s for s in stream if first is not None and s["pass"] >= first]
        fired = [s for s in stream if s["applied"]]
        series["naive_before"] = (sum(s["naive"] for s in before), sum(s["tasks"] for s in before))
        series["naive_after"] = (sum(s["naive"] for s in after), sum(s["tasks"] for s in after))
        series["first_sight"] = (sum(s["passed"] for s in stream), sum(s["tasks"] for s in stream))
        # applied-vs-outcome over the stream: of the rows a record fired on, how many passed / went naive / went other
        series["applied_outcome"] = {"records": sorted({r for s in fired for r in s["applied_records"]}),
                                     "passed": sum(s["applied_passed"] for s in fired), "naive": sum(s["applied_naive"] for s in fired),
                                     "other": sum(s["applied_other"] for s in fired), "tasks": sum(s["applied_tasks"] for s in fired)}
        series["quality"] = {q: _mean([s["quality"][q] for s in stream]) for q in ("economy", "turns", "transfer")}
        series["revisit"] = [(s["batch"], s["passed"], s["tasks"]) for s in series["series"] if s["kind"] == "revisit"]
    return out


# --- rendering ------------------------------------------------------------------------------------

def _rate(num: int, den: int) -> str:
    return f"{num / den:.2f} ({num}/{den})" if den else "—"


def _q(quality: dict[str, float | None]) -> str:
    """``economy / turns / transfer`` means, ``—`` where nothing was evaluable."""
    return " / ".join("—" if quality.get(q) is None else f"{quality[q]:.2f}" for q in ("economy", "turns", "transfer"))


def _applied_cell(applied: dict[str, dict[str, Any]]) -> str:
    """``lesson: records → passed/tasks`` per lesson a record fired on this pass — the applied-vs-outcome join."""
    return ", ".join(f"{l}: {' '.join(a['records'])} → {a['passed']}/{a['tasks']}✓" for l, a in applied.items()) or "—"


def _outcome(o: dict[str, Any]) -> str:
    """The applied-vs-outcome tally ``passed/tasks (✓ N W)`` of the rows a record fired on, ``—`` where none fired."""
    return f"{o['passed']}/{o['tasks']} ({o['passed']}✓ {o['naive']}N {o['other']}W)" if o["tasks"] else "—"


def _fired(f: dict[str, Any]) -> str:
    """``passed/rows on lessons`` where a record fired over the stream, ``never`` where it fired on nothing."""
    return f"{f['passed']}/{f['rows']} on {', '.join(f['lessons'])}" if f["rows"] else "never"


def arm_markdown(log: dict[str, Any]) -> str:
    st = log["stream"]
    lines = [f"# {log['experiment']}/{log['arm']} — evolution", "",
             f"{log['mode']} on `{log['model']}`; {st['batches']} batches × {st['batch']} tasks from {'+'.join(st['families'])}, seed {st['seed']}"
             + (f"; revisit {st['revisit']}" if st["revisit"] else "") + ".", ""] + ([f"> {log['warning']}", ""] if log.get("warning") else []) + [
             "## Passes", "", "| pass | batch | first sight | economy / turns / transfer | symptoms | in context | applied → outcome | mentions | filed | consolidation after |", "|---|---|---|---|---|---|---|---|---|---|"]
    for p in log["passes"]:
        sym = " ".join(f"{k}={v}" for k, v in sorted(p["symptoms"].items()))
        k = p["consolidation"]
        kk = "" if k is None else (f"{k['id']}: {len(k['groups'])} groups, {k['groups_at_bar']} at the bar; admitted {' '.join(k['admitted']) or 'nothing'}"
                                   + (f"; {', '.join(f'{v} {o}' for o, v in sorted(k['outcomes'].items()))}" if k["outcomes"] else "; nothing nominated")
                                   + (f"; retired {' '.join(k['retired'])}" if k["retired"] else "") + (f"; dismissed {len(k['dismissed'])}" if k["dismissed"] else ""))
        lines.append(f"| {p['pass']}{' (revisit)' if p['kind'] == 'revisit' else ''} | {p['batch']} | {'—' if p['pass_rate'] is None else f'{p['pass_rate']:.2f}'} | {_q(p['quality'])} | {sym} | "
                     f"{' '.join(p['in_context']) or 'none'} | {_applied_cell(p['applied'])} | {', '.join(f'{l}: {' '.join(ids)}' for l, ids in p['mentions'].items()) or '—'} | "
                     f"{len(p['observations'])} obs, {p['proposals']} prop | {kk} |")
    lines += ["", "## Lessons", "", "Each cell is the lesson's rows in that pass: ✓ passed, N the naive first-contact outcome (a same-shape failure), "
              "W another wrong answer, E a harness or tool error. A trailing `*` marks a pass a record **fired** on the lesson's rows (its id in "
              "some row's `applied`); `first applied` is the first stream pass that happened, and the naive before / after split turns on it. "
              "`applied → outcome` is how the rows a record fired on turned out over the stream — a record that fired on every row but did not "
              "make it pass shows as a low ✓ count here, which keyword mention could not.", "",
              "| lesson | tier | " + " | ".join(f"p{p['pass']}" + ("r" if p["kind"] == "revisit" else "") for p in log["passes"]) +
              " | first sight | economy / turns / transfer | naive before / after first applied | first applied | applied → outcome | revisit |",
              "|---|---|" + "---|" * len(log["passes"]) + "---|---|---|---|---|---|"]
    by_pass = {p["pass"]: p for p in log["passes"]}
    for lesson, s in sorted(log["lessons"].items(), key=lambda kv: (_lessons.TIERS.index(kv[1]["tier"]) if kv[1]["tier"] in _lessons.TIERS else 9, kv[0])):
        cells = {x["pass"]: x["grid"] + ("*" if x["applied"] else "") for x in s["series"]}
        lines.append(f"| {lesson} | {s['tier'] or '—'} | " + " | ".join(cells.get(p, "") for p in by_pass) + f" | {_rate(*s['first_sight'])} | {_q(s['quality'])} | "
                     f"{_rate(*s['naive_before'])} / {_rate(*s['naive_after'])} | {s['first_applied_pass'] or '—'} | {_outcome(s['applied_outcome'])} | "
                     + (", ".join(f"batch {b}: {p}/{n}" for b, p, n in s["revisit"]) or "—") + " |")
    lines += ["", "## What the passes noticed", "", "Each observation as the close filed it, with the shape the blind coder gave it at the next "
              "consolidation (`open` until one has run); a group reaches the bar when its observations come from as many distinct sessions as the bar asks.", ""]
    for p in log["passes"]:
        for o in p["observations"]:
            lines.append(f"- pass {p['pass']} {o['name']} [{', '.join(o['shape'] or []) or o['state']}]: {o['happened']}")
        k = p["consolidation"]
        if k is not None:
            for g in k["groups"]:
                lines.append(f"- {k['id']} group [{', '.join(g['shape'] or [])}] ← {' '.join(g['observations'])} from {' '.join(g['sessions'])}"
                             + (" — at the bar" if g["at_bar"] else " — below the bar"))
            for n in k["nominations"]:
                lines.append(f"- {k['id']} nominated {n['subject']} at {n['rung']} → {n['outcome']}")
    if not any(p["observations"] for p in log["passes"]):
        lines.append("Nothing was filed.")
    lines += ["", "## Records", "", "`fired` is where the record was actually applied — rows it fired on, of those how many passed, "
              "and the lessons touched; `mentions` stays a keyword heuristic over the record's own text.", ""]
    if log["records"]:
        lines += ["| record | admitted after pass | fired (passed/rows on lessons) | mentions | decision |", "|---|---|---|---|---|"]
        lines += [f"| {r['id']} | {r['admitted_after_pass'] or '—'} | {_fired(r['fired'])} | {', '.join(r['mentions']) or '—'} | {r['decision']} |" for r in log["records"]]
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
    lines += ["## First sight, per lesson", "", "Pass rate per arm, then economy / turns / transfer per arm. The last columns are the attached arm: "
              "the naive-shape failures before and after the first pass a record fired on the lesson's rows, that pass, and how the rows a record fired "
              "on turned out — a record that fired on everything without helping shows a low ✓ here where keyword mention showed nothing.", "",
              "| lesson | tier | " + " | ".join(logs) + " | " + " | ".join(f"{a} quality" for a in logs) + " | naive-shape before / after first applied (attached) | first applied | applied → outcome |",
              "|---|---|" + "---|" * (2 * len(logs) + 3)]
    lessons = sorted({l for log in logs.values() for l in log["lessons"]}, key=lambda l: (_lessons.TIERS.index(_lessons.tier(l)) if _lessons.tier(l) else 9, l))
    for lesson in lessons:
        cells = [_rate(*log["lessons"][lesson]["first_sight"]) if lesson in log["lessons"] else "—" for log in logs.values()]
        cells += [_q(log["lessons"][lesson]["quality"]) if lesson in log["lessons"] else "—" for log in logs.values()]
        att = next((log["lessons"].get(lesson) for log in logs.values() if log["mode"] == "attached"), None)
        lines.append(f"| {lesson} | {_lessons.tier(lesson) or '—'} | " + " | ".join(cells) + " | " +
                     (f"{_rate(*att['naive_before'])} / {_rate(*att['naive_after'])} | {att['first_applied_pass'] or '—'} | {_outcome(att['applied_outcome'])}" if att else "— | — | —") + " |")
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
            lines.append(f"- {arm} {r['id']} (after pass {r['admitted_after_pass'] or '?'}; fired {_fired(r['fired'])}): {r['decision']}")
    if not any_record:
        lines.append("None.")
    lines += ["", "## Reading", "",
              "A symptom is derived, not judged: `naive` means the row's result equals what the task's scripted first-contact policy returns "
              "(or its error is of the same class), so a naive-shape failure after a record **fired** on the lesson's rows is the same shape recurring "
              "with the memory applied. The series turns on firing (a record's id in a row's `applied`), not on keyword mention: `first applied` is the "
              "first stream pass a record fired on the lesson, the naive before / after split turns on it, and `applied → outcome` shows how the rows a "
              "record fired on then went — a record that fired on every row and made none of them pass reads as a low ✓ count there, which the old keyword "
              "`mentions` column could not show. Quality grades a passed solution: `economy` is the knowing policy's calls over the calls spent (zero on a "
              "failed row), `turns` the same over model turns, `transfer` whether the last shell command replayed in the task's twin world gives the twin's "
              "answer — a pass that knows a convention spends less and its method carries, where one that discovers it spends the discovery and may not. "
              "`mentions` is kept as a keyword heuristic over a record's text and is logged as one, not the driving signal. Every count is from one run and is a floor."]
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
