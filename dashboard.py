# /// script
# requires-python = ">=3.14"
# dependencies = ["marimo", "hgi"]
# ///
"""The marimo dashboard: the projection surface, the escalation queue and the runnable acceptance bar.

Every cell renders live from a store — the projection law of § 7 as a UI. The store is the
demonstration's ``./store`` or any experiment arm's under ``runs/<experiment>/<arm>/store``, chosen
at the top; an arm still running shows its passes as they land. When the chosen store is an arm,
every arm of its experiment is overlaid on one chart with the experiment's report beneath. The
notebook reads the store; it writes only through ``hgi`` commands (the queue's two buttons shell out
to ``hgi queue``).

The body is six tabs — Loop, Lessons, Passes, Store, Queue, Floor — under a row of header stats.
Lessons and Passes read the evolution log (:mod:`hgi.evolution`) of a stream arm and say so when the
chosen store is not one.

    uv run marimo run dashboard.py        # the app
    uv run marimo edit dashboard.py       # the notebook
"""

import marimo

__generated_with = "0.24.2"
app = marimo.App(width="full", app_title="HGI")  # "wide" is not a marimo width: the config parse fails and the app falls back to narrow


@app.cell
def _():
    import json
    import os
    import subprocess
    from pathlib import Path

    import marimo as mo

    from hgi import evolution as hevolution
    from hgi import experiment as hexperiment
    from hgi import index as hindex
    from hgi.cli import load_env
    from hgi.store import Store
    from hgi.tracing import weave_project_url, weave_url
    from suite import lessons as slessons

    def wlink(uri, text="trace"):
        """One Weave call URI as markdown into the trace store; an untraced run reads `—`."""
        return f"[{text}]({weave_url(uri)})" if weave_url(uri) else "—"

    def wcell(uri):
        """The same as a table cell — `mo.ui.table` renders an Html value and prints a markdown string raw."""
        return mo.md(wlink(uri))

    load_env()
    stores = {"store — the demonstration": Path("store")} | {
        f"{p.parents[1].name}/{p.parent.name}": p for p in sorted(hexperiment.runs_root().glob("*/*/store"))
    }
    _default = next((k for k, v in stores.items() if str(v) == os.environ.get("HGI_STORE", "store")), next(iter(stores)))
    picker = mo.ui.dropdown(options=stores, value=_default, label="store")
    refresh = mo.ui.refresh(options=["5s", "30s"], default_interval=None)
    return (
        Path,
        Store,
        hevolution,
        hexperiment,
        hindex,
        json,
        mo,
        os,
        picker,
        refresh,
        slessons,
        subprocess,
        wcell,
        weave_project_url,
        wlink,
    )


@app.cell
def _(Store, picker, refresh):
    refresh
    root = picker.value
    store = Store(root)
    sessions = sorted(store.all("session"), key=lambda s: (s.pass_, not s.attached))
    trace_root = next((s.trace_root for s in sessions if s.trace_root), None)  # the store's Weave project, or None untraced
    return root, sessions, store, trace_root


@app.cell
def _(fires, lint_out, mo, off, on, picker, refresh, root, sessions, store, trace_root, weave_project_url):
    _last = lambda pts: next((f"{v:.2f}" for _, v in reversed(pts) if v is not None), "—")
    _weave = mo.md(f"[Weave traces]({weave_project_url(trace_root)}) · [Weave evaluations]({weave_project_url(trace_root, 'evaluations')})"
                   if trace_root else "_untraced run (no HGI_WEAVE_PROJECT)_")
    mo.vstack([
        mo.md(f"# HGI — `{root}`"),
        mo.hstack([picker, refresh, _weave], justify="start"),
        mo.hstack([
            mo.stat(sum(s.attached for s in sessions), label="passes run", caption="attached", bordered=True),
            mo.stat(_last(on), label="task_pass_rate", caption="attached, latest", bordered=True),
            mo.stat(_last(off), label="task_pass_rate", caption="detached, latest", bordered=True),
            mo.stat(len(store.decisions("accepted")), label="live decisions", caption="accepted, not retired", bordered=True),
            mo.stat(len(store.observations()), label="open observations", caption="awaiting a consolidation", bordered=True),
            mo.stat(len(fires), label="undischarged fires", caption="a latch fired, nothing answered", bordered=True),
            mo.stat("green" if lint_out.returncode == 0 else "red", label="lint", caption="the acceptance bar", bordered=True),
        ], justify="start", gap=0.6, widths="equal"),
    ])
    return


@app.cell
def _(mo):
    PALETTE = ["#2a7", "#c55", "#36c", "#d92", "#93c", "#0aa", "#864", "#555"]

    def curve_svg(series: dict[str, list[tuple[int, float | None]]]) -> "mo.Html":
        """One chart, one line per named series, over the union of their passes."""
        w, h, pad = 640, 240, 36
        passes = sorted({p for pts in series.values() for p, _ in pts}) or [1]
        x = lambda p: pad + (p - min(passes)) * (w - 2 * pad) / max(1, max(passes) - min(passes))
        y = lambda v: h - pad - (v or 0) * (h - 2 * pad)

        def path(points, color):
            pts = [(p, v) for p, v in points if v is not None]
            if not pts:
                return ""
            d = " ".join(f"{'M' if i == 0 else 'L'}{x(p):.1f},{y(v):.1f}" for i, (p, v) in enumerate(pts))
            return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="2"/>' + "".join(
                f'<circle cx="{x(p):.1f}" cy="{y(v):.1f}" r="4" fill="{color}"/>' for p, v in pts)

        axes = (f'<line x1="{pad}" y1="{h-pad}" x2="{w-pad}" y2="{h-pad}" stroke="#888"/>'
                f'<line x1="{pad}" y1="{pad}" x2="{pad}" y2="{h-pad}" stroke="#888"/>'
                + "".join(f'<text x="{x(p):.1f}" y="{h-pad+16}" font-size="11" text-anchor="middle">{p}</text>' for p in passes)
                + "".join(f'<text x="{pad-6}" y="{y(v)+4:.1f}" font-size="11" text-anchor="end">{v:.1f}</text>' for v in (0, 0.5, 1.0)))
        colors = {name: PALETTE[i % len(PALETTE)] for i, name in enumerate(series)}
        legend = "".join(f'<rect x="440" y="{10 + 20 * i}" width="12" height="12" fill="{colors[n]}"/>'
                         f'<text x="458" y="{21 + 20 * i}" font-size="12">{n}</text>' for i, n in enumerate(series))
        return mo.Html(f'<svg width="{w}" height="{h}" style="background:#fff;border:1px solid #ddd">{axes}'
                       + "".join(path(pts, colors[n]) for n, pts in series.items()) + legend + "</svg>")
    return PALETTE, curve_svg


@app.cell
def _(Path, hevolution, hexperiment, root):
    # the arm's evolution log, live: `hgi.evolution` derives it from the store on every refresh
    _dir = Path(root).parent
    _file = Path("experiments") / f"{_dir.parent.name}.toml"
    exp = log = evo_error = None
    logs = {}
    if _dir.parent.parent == hexperiment.runs_root() and (_file.exists() or (_dir / "arm.json").exists()):
        _errors = []
        # `hgi` refuses with SystemExit, which is a BaseException: `except Exception` lets it through and marimo blanks every cell under it
        try:  # an experiment file declares the arms; a directory of arms no file declares (a retrofit) is read from its arm.json records
            exp = hexperiment.load(_file) if _file.exists() else hexperiment.from_dir(_dir.parent)[0]
        except (Exception, SystemExit) as _e:  # a half-written or stale arm names itself instead of killing the tab
            _errors.append(f"the experiment did not load: `{type(_e).__name__}: {_e}`")
        for _arm in dict.fromkeys([*exp.arms, _dir.name]) if exp is not None else ():
            try:  # arm by arm: a sibling arm that will not read must not blank the chosen one
                if (_l := hevolution.arm_log(exp, _arm)) is not None:
                    logs[_arm] = _l
            except (Exception, SystemExit) as _e:
                _errors.append(f"the evolution log did not read: `{type(_e).__name__}: {_e}`" if _arm == _dir.name
                               else f"arm `{_arm}` was skipped: `{type(_e).__name__}: {_e}`")
        log = logs.get(_dir.name)
        evo_error = "; ".join(_errors) or None
    return evo_error, exp, log, logs


@app.cell
def _(curve_svg, log, mo, sessions):
    def _series(attached: bool):
        return [(s.pass_, s.evaluation.scores["task_pass_rate"].value) for s in sessions
                if s.attached == attached and s.evaluation and "task_pass_rate" in s.evaluation.scores]

    on, off = _series(True), _series(False)
    curve = mo.vstack([
        mo.md("## " + ("first sight per pass (batch k met once; r = revisit)" if log else
                       "Score curve — `task_pass_rate` by pass, same suite hash")),
        curve_svg({"memory attached": on, "detached (ablation)": off}),
    ])
    return curve, off, on


@app.cell
def _(curve_svg, exp, hexperiment, json, mo, trace_root, weave_project_url):
    overlay = mo.md("")
    if exp is not None:
        try:  # `hexperiment.report` resolves every arm, and a refusal there is a SystemExit
            _arms = {a: json.loads(p.read_text()) for a in exp.arms if (p := hexperiment.arm_dir(exp, a) / "arm.json").exists()}
            _series = {f"{a} · {r['roster']['pass']}" + (" (detached)" if r["spec"]["mode"] == "detached" else ""):
                       [(int(p), v) for p, v in r["curve"].items()] for a, r in _arms.items()}
            overlay = mo.vstack([mo.md(f"## Experiment `{exp.name}` — every arm on one chart" + (f": {exp.description}" if exp.description else "")),
                                 curve_svg(_series), mo.md(hexperiment.report(exp).split("\n", 2)[2])]
                                + ([mo.md(f"[compare the arms' evaluations in Weave]({weave_project_url(trace_root, 'evaluations')})")] if trace_root else []))
        except (Exception, SystemExit) as _e:
            overlay = mo.md(f"⚠️ the experiment overlay did not read: `{type(_e).__name__}: {_e}`")
    return (overlay,)


@app.cell
def _(curve_svg, evo_error, exp, hevolution, log, logs, mo):
    # the paired attached-vs-detached report, and the arm's solution quality beside its correctness
    evolution_view = _warning = mo.md(f"⚠️ {evo_error}") if evo_error else mo.md("")
    if log is not None:
        _q = {q: [(p["pass"], p["quality"][q]) for p in log["passes"]] for q in ("economy", "turns", "transfer")}
        _q = {q: pts for q, pts in _q.items() if any(v is not None for _, v in pts)}
        evolution_view = mo.vstack([
            _warning,  # a sibling arm that would not read still says so over the chosen arm's report
            mo.md(hevolution.experiment_markdown(exp, logs)),
            mo.md("## Solution quality per pass — `economy` / `turns` / `transfer`, mean over the pass's rows"),
            curve_svg(_q) if _q else mo.md("_no quality series is evaluable on this arm_"),
        ])
    return (evolution_view,)


@app.cell
def _(curve_svg, exp, hevolution, log, logs, mo, slessons):
    GLYPH = {"✓": "#2a7", "N": "#d92", "W": "#c55", "E": "#888"}

    def _cell(s):
        """One lesson's rows in one pass; a mentioned pass is ringed and says so on hover."""
        glyphs = "".join(f'<span style="color:{GLYPH.get(c, "#888")};font-weight:600">{c}</span>' for c in s["grid"])
        ring = ('style="border:2px solid #36c" title="a record in context mentions this lesson"' if s["mentioned"] else 'style="border:1px solid #eee"')
        return f'<td align="center" {ring}>{glyphs}{"<sup style=color:#36c>•</sup>" if s["mentioned"] else ""}</td>'

    lessons_view = mo.md("")
    if log is not None:
        _cols = [f"p{_x['pass']}" + ("r" if _x["kind"] == "revisit" else "") for _x in log["passes"]]
        _head = ("<tr><th align=left>lesson</th><th>tier</th>" + "".join(f"<th>{c}</th>" for c in _cols)
                 + "<th>first sight</th><th>naive before / after</th><th>first mention</th><th>economy / turns / transfer</th></tr>")
        _rows = []
        for _lesson, _s in sorted(log["lessons"].items(), key=lambda kv: (slessons.TIERS.index(kv[1]["tier"]) if kv[1]["tier"] in slessons.TIERS else 9, kv[0])):
            _by = {x["pass"]: x for x in _s["series"]}
            _rows.append(f"<tr><td align=left><code>{_lesson}</code></td><td align=center>{_s['tier'] or '—'}</td>"
                         + "".join(_cell(_by[_x["pass"]]) if _x["pass"] in _by else "<td></td>" for _x in log["passes"])
                         + f"<td align=center>{hevolution._rate(*_s['first_sight'])}</td>"
                         f"<td align=center>{hevolution._rate(*_s['naive_before'])} / {hevolution._rate(*_s['naive_after'])}</td>"
                         f"<td align=center>{_s['first_mention_pass'] or '—'}</td><td align=center>{hevolution._q(_s['quality'])}</td></tr>")
        _grid = mo.Html(f'<table style="border-collapse:collapse;font-size:13px">{_head}{"".join(_rows)}</table>')
        _legend = mo.md("Each cell is the lesson's rows in that pass: "
                        + " · ".join(f'<span style="color:{c};font-weight:600">{g}</span> {n}' for g, c, n in
                                     [("✓", GLYPH["✓"], "passed"), ("N", GLYPH["N"], "the naive first-contact outcome — the same-shape failure"),
                                      ("W", GLYPH["W"], "another wrong answer"), ("E", GLYPH["E"], "a harness or tool error")])
                        + ". A ringed cell had a record in context whose text uses the lesson's words — a keyword heuristic, logged as one.")
        _fs = {_k: [(s["pass"], s["passed"] / s["tasks"]) for s in _v["series"] if s["kind"] == "stream" and s["tasks"]]
               for _k, _v in sorted(log["lessons"].items())}
        lessons_view = mo.vstack([
            mo.md(f"## Lessons — `{log['experiment']}/{log['arm']}`, one row a lesson, one column a pass"),
            _grid, _legend,
            mo.md("## Reading\n\n" + hevolution.experiment_markdown(exp, logs).split("## Reading", 1)[-1].strip()),
            mo.md("## First sight per lesson — noisy by construction: a lesson is met once a batch, so each point is one or two rows"),
            curve_svg(_fs),
        ])
    return (lessons_view,)


@app.cell
def _(log, mo):
    _label = lambda p: (f"pass {p['pass']}" + (" (revisit)" if p["kind"] == "revisit" else "") + f" · batch {p['batch']}"
                        + f" · first sight {'—' if p['pass_rate'] is None else f'{p["pass_rate"]:.2f}'}")
    _opts = {} if log is None else {_label(p): p["pass"] for p in log["passes"]}
    pass_pick = mo.ui.dropdown(options=_opts, value=next(iter(_opts), None), label="pass")
    return (pass_pick,)


@app.cell
def _(log, mo, pass_pick, sessions, store, wcell, wlink):
    passes_view = mo.md("")
    if log is not None and pass_pick.value is not None:
        _p = next(x for x in log["passes"] if x["pass"] == pass_pick.value)
        _s = next((s for s in sessions if s.id == _p["session"]), None)
        _run = (_s.evaluation.run if _s and _s.evaluation else None)
        _rows = [{"task": r["task"], "lesson": r["lesson"], "symptom": r["symptom"], "applied": " ".join(r["applied"]) or "—",
                  "http": r["calls"]["http"], "shell": r["calls"]["shell"], "turns": r["calls"]["turns"],
                  "economy": "—" if r["economy"] is None else f"{r['economy']:.2f}",
                  "error": ((r["error"] or {}).get("message") or "")[:80],
                  "trace": wcell(r["call"])} for r in _p["rows"]]
        _ctx = [f"**{i}** — {store.read('decision', i).decision}" for i in _p["in_context"] if store.exists("decision", i)]
        _k = _p["consolidation"]
        _kv = mo.md("_no consolidation after this pass_") if _k is None else mo.md("\n".join(
            [f"**{_k['id']}** — admitted {' '.join(_k['admitted']) or 'nothing'}; retired {' '.join(_k['retired']) or 'nothing'}; "
             f"dismissed {len(_k['dismissed'])}; expired {len(_k['expired'])}", ""]
            + [f"- group [{', '.join(g['shape'] or []) or '—'}] ← {' '.join(g['observations']) or 'none'} from {' '.join(g['sessions']) or 'none'}"
               + (" — **at the bar**" if g["at_bar"] else " — below the bar") for g in _k["groups"]]
            + [f"- nominated `{n['subject']}` at {n['rung']} → {n['outcome'] or 'pending'}" for n in _k["nominations"]]
            or ["", "_nothing grouped, nothing nominated_"]))
        passes_view = mo.vstack([
            mo.md(f"## Pass {_p['pass']} — batch {_p['batch']} (`{_p['hash']}`), session `{_p['session']}`, {_p['kind']}; "
                  f"work shape {', '.join(_p['work_shape']) or '—'}"
                  + (f" · {wlink(_run, 'evaluation in Weave')}" if _run else "")),
            pass_pick, mo.ui.table(_rows),
            mo.accordion({
                f"records in context ({len(_p['in_context'])})": mo.md("\n\n".join(_ctx) or "_nothing was in context_"),
                f"observations filed ({len(_p['observations'])})": mo.ui.table(_p["observations"]) if _p["observations"] else mo.md("_nothing was filed_"),
                "consolidation after the pass": _kv,
            }),
        ])
    return (passes_view,)


@app.cell
def _(hindex, mo, store, wcell):
    hooks = hindex.read(store, "hooks")
    _adjudicator = {d.id: d.admission.adjudicator.call if d.admission.adjudicator else None for d in store.decisions("accepted")}
    competence = [{**r, "adjudicator": wcell(_adjudicator.get(r["record"]))} for r in hindex.read(store, "competence")]
    fires = hindex.read(store, "fires")
    zero = hindex.read(store, "structural_zero")
    deferred = hindex.read(store, "deferred")
    wiring = hindex.read(store, "wiring")
    fusion = [r for r in hindex.read(store, "fusion") if r["bimodal"]]
    convergence = hindex.read(store, "convergence")
    projections = mo.vstack([
        mo.md("## Projections"),
        mo.md("### Hook-major index — a cell carries what a reader cannot obey without opening the record"),
        mo.ui.table([{"term": t, **c} for t, cells in hooks.items() for c in cells]) if hooks else mo.md("_no live consultation hook_"),
        mo.md("### Competence — applied ÷ considered; a nominator, never a verdict. `adjudicator` is the call that admitted the record"),
        mo.ui.table(competence) if competence else mo.md("_no accepted decision_"),
        mo.md(f"### Undischarged fires: {len(fires)} · structural zero: {zero or 'none'}"),
        mo.ui.table(fires) if fires else mo.md("_none_"),
        mo.md(f"### Deferred drafts: {len(deferred)} — each waits on the condition its verdict named"),
        mo.ui.table(deferred) if deferred else mo.md("_none_"),
        mo.md(f"### Wiring — {len(wiring)} live neighbour latches propagation walks"),
        mo.ui.table(wiring) if wiring else mo.md("_none_"),
        mo.md(f"### Split and fold nominators — fused records: {len(fusion)} · converging pairs: {len(convergence)}"),
        mo.ui.table([{"record": r["record"], "applied_on": r["applied_on"], "never_on": r["never_on"]} for r in fusion] +
                    [{"records": r["records"], "shared_terms": r["shared_terms"], "co_applied": r["co_applied"]} for r in convergence])
        if fusion or convergence else mo.md("_none_"),
    ])
    return fires, projections


@app.cell
def _(mo, store, wcell):
    _entries = store.all("hypothesis")
    ledger = mo.vstack([
        mo.md("## Ledger — every entry three distinct role calls"),
        mo.ui.table([{
            "entry": e.id, "species": e.species, "subject": e.subject, "verdict": e.verdict,
            "proposer": e.proposer.role, "proposer call": wcell(e.proposer.call),
            "contradiction": e.contradiction.source.role, "contradiction call": wcell(e.contradiction.source.call),
            "adjudicator": e.adjudicator.role if e.adjudicator else "—",
            "adjudicator call": wcell(e.adjudicator.call if e.adjudicator else None),
        } for e in _entries]) if _entries else mo.md("_the ledger is empty_"),
    ])
    return (ledger,)


@app.cell
def _(hindex, mo, store):
    graph = hindex.read(store, "lineage")
    _lines = ["graph LR"] + [f'  {e["from"].replace("-", "_")}(["{e["from"]}"]) -->|{e["kind"]}| {e["to"].replace("-", "_")}(["{e["to"]}"])' for e in graph["edges"]]
    lineage = mo.vstack([mo.md("## Lineage DAG"), mo.mermaid("\n".join(_lines)) if graph["edges"] else mo.md("_no lineage yet_")])
    return (lineage,)


@app.cell
def _(hindex, mo, store):
    m = hindex.read(store, "matrix")
    a = hindex.read(store, "attacker")
    _cell = lambda k: len(m.get(k, []))
    matrix = mo.vstack([
        mo.md("## Detection matrix — every count is a floor"),
        mo.ui.table([
            {"": "system catches", "oracle or human catches": _cell("system-catches/oracle-catches") + _cell("system-catches/human-catches"), "neither catches": _cell("system-catches/none-catches")},
            {"": "system misses", "oracle or human catches": _cell("system-misses/oracle-catches") + _cell("system-misses/human-catches"), "neither catches": f"≥ {_cell('system-misses/none-catches')} rows nothing caught (a floor: failed rows of passes that consulted nothing and filed no observation from the row)"},
        ]),
        mo.md(f"## Attacker precision — {a['dispatched']} dispatched, {a['landed']} claims landed, {a['upheld']} upheld, {a['overruled']} overruled"
              + (f"; precision {a['precision']:.2f}" if a["precision"] is not None else "; precision unevaluable (no landing)")),
        mo.ui.table([{"angle": k, **v} for k, v in a["per_angle"].items()]) if a["per_angle"] else mo.md("_no attack on the ledger_"),
        mo.md("**Should-have-been-caught-by:** " + ("; ".join(f"{r['record']} survived {', '.join(r['survived'])}, caught by {', '.join(r['caught_by'])}" for r in a["misses"]) or "none")),
        mo.md("\n".join(f"_{n}_" for n in a["notes"])) if a["notes"] else mo.md(""),
    ])
    return (matrix,)


@app.cell
def _(json_dumps, mo, store):
    queue = store.queue()
    admit = {q.draft.uid: mo.ui.button(label=f"admit {q.draft.name}", value=q.draft.uid) for q in queue}
    decline = {q.draft.uid: mo.ui.button(label=f"decline {q.draft.name}", value=q.draft.uid) for q in queue}
    escalations = mo.vstack([mo.md(f"## Escalation queue — {len(queue)} awaiting a human verdict")] + [
        mo.vstack([mo.md(f"**{q.draft.name}** · {q.why} · ledger {q.ledger_entry}\n\n> {q.draft.body.decision}\n\n"
                         f"attack: {json_dumps(q.oracle_evidence.get('attack', {}))}"), mo.hstack([admit[q.draft.uid], decline[q.draft.uid]])])
        for q in queue
    ] or [mo.md("_empty_")])
    return admit, decline, escalations


@app.cell
def _(json):
    def json_dumps(x):
        return json.dumps(x, default=str)[:600]
    return (json_dumps,)


@app.cell
def _(admit, decline, mo, os, root, subprocess):
    _out = []
    for _uid, _b in admit.items():
        if _b.value:
            _out.append(subprocess.run(["uv", "run", "hgi", "--store", str(root), "queue", "--resolve", _uid, "--verdict", "admit"], capture_output=True, text=True, env=os.environ).stdout)
    for _uid, _b in decline.items():
        if _b.value:
            _out.append(subprocess.run(["uv", "run", "hgi", "--store", str(root), "queue", "--resolve", _uid, "--verdict", "decline(declined on the escalation surface)"], capture_output=True, text=True, env=os.environ).stdout)
    verdicts = mo.md("\n".join(f"`{o.strip()}`" for o in _out if o) or "")
    return (verdicts,)


@app.cell
def _(mo, root, subprocess):
    lint_out = subprocess.run(["uv", "run", "hgi", "--store", str(root), "lint"], capture_output=True, text=True)
    floor = mo.vstack([mo.md("## The floor"), mo.md(f"```\n{lint_out.stdout.strip()}\n```")])
    return floor, lint_out


@app.cell
def _(curve, escalations, evolution_view, floor, ledger, lessons_view, lineage, log, matrix, mo, overlay, passes_view, projections, verdicts):
    _not_stream = mo.md("not a stream arm; the Loop tab has the curve")
    mo.ui.tabs({
        "Loop": mo.vstack([curve, overlay, evolution_view]),
        "Lessons": lessons_view if log is not None else _not_stream,
        "Passes": passes_view if log is not None else _not_stream,
        "Store": mo.vstack([projections, ledger, lineage, matrix]),
        "Queue": mo.vstack([escalations, verdicts]),
        "Floor": floor,
    })
    return


if __name__ == "__main__":
    app.run()
