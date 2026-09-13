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

The body is seven tabs — Loop, Lessons, Passes, Compute, Store, Queue, Floor — under a row of header
stats. Lessons and Passes read the evolution log (:mod:`hgi.evolution`) of a stream arm and say so
when the chosen store is not one. Compute reads the trace store: every model call an arm made
carries its tokens and latency in Weave, with the arm, pass and role as attributes, so the tab
pulls them on request and charts where the tokens and the seconds went. Every chart is an altair
chart rendered by marimo: hover a mark for the row behind it.

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

    import altair as alt
    import marimo as mo
    import polars as pl

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
        alt,
        hevolution,
        hexperiment,
        hindex,
        json,
        mo,
        os,
        picker,
        pl,
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
def _(alt, mo, pl):
    # The chart vocabulary. Categorical hues are assigned in a fixed order to a fixed domain — an arm keeps its
    # colour whether or not its siblings are on the chart — and the light and dark steps are the same eight
    # hues re-stepped for the surface, so the slot is the identity in both themes. Magnitude is one hue
    # light → dark. Every mark carries a tooltip with the row behind it.
    _DARK = mo.app_meta().theme == "dark"
    SLOTS = (["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#008300", "#9085e9", "#e66767"] if _DARK
             else ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"])
    SURFACE = "#1a1a19" if _DARK else "#fcfcfb"
    INK = "#c3c2b7" if _DARK else "#52514e"
    RAMP = ["#0d366b", "#cde2fb"] if _DARK else ["#cde2fb", "#0d366b"]  # sequential blue, light → dark on the light surface
    ROLES = ["pass", "consolidator", "examiner", "adjudicator", "coder", "reauthor"]

    def slots(domain: list[str], order: list[str] | None = None) -> alt.Scale:
        """The categorical scale for a fixed domain: a name takes the hue of its place in ``order`` (the domain itself by
        default), past eight it folds to grey — so an arm keeps its colour when a sibling is absent from one chart."""
        domain, order = list(domain), list(order or domain)
        hue = lambda n: SLOTS[order.index(n)] if n in order and order.index(n) < len(SLOTS) else "#888"
        return alt.Scale(domain=domain, range=[hue(n) for n in domain])

    def _themed(chart: alt.TopLevelMixin) -> alt.TopLevelMixin:
        return (chart.configure_view(strokeWidth=0)
                .configure_axis(gridColor="#888", gridOpacity=0.25, domainColor="#888", tickColor="#888", labelColor=INK, titleColor=INK)
                .configure_legend(labelColor=INK, titleColor=INK, symbolStrokeWidth=2)
                .configure_title(color=INK, anchor="start", fontWeight="normal", fontSize=13))

    _PASS_X = alt.X("pass:Q", axis=alt.Axis(tickMinStep=1, format="d", title="pass", grid=False))

    def present(df: pl.DataFrame, order: list[str], field: str = "arm") -> list[str]:
        """The names of ``order`` that occur in the frame, in that order — a legend names what is drawn, nothing else."""
        seen = set(df[field].to_list()) if df.height else set()
        return [n for n in order if n in seen]

    def score_curve(df: pl.DataFrame, arms: list[str], focus: str | None = None, marks: pl.DataFrame | None = None, title: str = "") -> alt.LayerChart:
        """One line an arm over the passes, the chosen arm at full ink and its siblings faded; attached solid, detached dashed;
        a stream pass a circle, a revisit a triangle; a dotted rule where the chosen arm admitted a record."""
        base = alt.Chart(df).encode(
            x=_PASS_X,
            y=alt.Y("score:Q", scale=alt.Scale(domain=[0, 1]), axis=alt.Axis(title="task_pass_rate", tickCount=5, format=".1f")),
            color=alt.Color("arm:N", scale=slots(present(df, arms), arms), legend=alt.Legend(title=None, orient="top", direction="horizontal")),
            opacity=alt.condition(f"datum.arm == '{focus}'", alt.value(1), alt.value(0.4)) if focus and len(arms) > 1 else alt.value(1),
            tooltip=[alt.Tooltip("arm:N"), alt.Tooltip("pass:Q", format="d"), alt.Tooltip("score:Q", format=".2f"), alt.Tooltip("kind:N"),
                     alt.Tooltip("batch:N"), alt.Tooltip("in_context:N", title="records in context"), alt.Tooltip("after:N", title="consolidation after")],
        )
        lines = base.mark_line(strokeWidth=2, strokeJoin="round", strokeCap="round").encode(
            strokeDash=alt.StrokeDash("mode:N", scale=alt.Scale(domain=["attached", "detached"], range=[[1, 0], [6, 4]]), legend=None))
        points = base.mark_point(size=70, filled=True, stroke=SURFACE, strokeWidth=2).encode(
            shape=alt.Shape("kind:N", scale=alt.Scale(domain=["stream", "revisit", "pass"], range=["circle", "triangle-up", "circle"]), legend=None))
        layers = [lines, points]
        if marks is not None and marks.height:
            # marimo projects its point selection on x and y of every layer, so the rule spans a y field (lo → hi) and the
            # label sits on one, rather than on a bare value — a layer without a y field loses the param and the frontend
            # then listens for a signal Vega never made
            rule = alt.Chart(marks).encode(x=_PASS_X, y=alt.Y("lo:Q"), tooltip=[alt.Tooltip("pass:Q", format="d"), alt.Tooltip("records:N", title="admitted after the pass")])
            layers += [rule.mark_rule(strokeDash=[2, 3], color="#888").encode(y2="hi:Q"),
                       rule.mark_text(align="left", baseline="top", dx=4, dy=2, fontSize=10, color=INK).encode(y=alt.Y("hi:Q"), text="records:N")]
        return _themed(alt.layer(*layers).properties(width="container", height=260, title=title))

    def facet_lines(df: pl.DataFrame, arms: list[str], measures: list[str], columns: int = 3, title: str = "") -> alt.FacetChart:
        """Small multiples, one panel a measure on its own axis — never two scales on one plot — one line an arm."""
        base = alt.Chart(df).encode(
            x=_PASS_X,
            y=alt.Y("value:Q", axis=alt.Axis(title=None, tickCount=4)),
            color=alt.Color("arm:N", scale=slots(present(df, arms), arms), legend=alt.Legend(title=None, orient="top", direction="horizontal")),
            tooltip=[alt.Tooltip("arm:N"), alt.Tooltip("measure:N"), alt.Tooltip("pass:Q", format="d"), alt.Tooltip("value:Q", format=".2f")],
        )
        chart = alt.layer(base.mark_line(strokeWidth=2, strokeJoin="round"), base.mark_point(size=50, filled=True, stroke=SURFACE, strokeWidth=2))
        return _themed(chart.properties(width=240, height=150).facet(
            facet=alt.Facet("measure:N", sort=measures, header=alt.Header(title=None, labelColor=INK, labelFontWeight="bold")), columns=columns, title=title)
            .resolve_scale(y="independent"))

    def lesson_heatmap(df: pl.DataFrame, lessons: list[str], title: str = "") -> alt.LayerChart:
        """Lesson × pass, the cell the first-sight rate on one blue ramp; a mentioned cell is ringed."""
        base = alt.Chart(df).encode(
            x=alt.X("column:N", sort=None, axis=alt.Axis(title="pass (r = revisit)", labelAngle=0, grid=False)),
            y=alt.Y("lesson:N", sort=lessons, axis=alt.Axis(title=None, grid=False)),
            tooltip=[alt.Tooltip("lesson:N"), alt.Tooltip("tier:N"), alt.Tooltip("column:N", title="pass"), alt.Tooltip("rate:Q", format=".2f", title="passed ÷ rows"),
                     alt.Tooltip("grid:N", title="rows (✓ pass · N naive · W wrong · E error)"), alt.Tooltip("mentioned:N", title="a record in context mentions it")],
        )
        cells = base.mark_rect(stroke=SURFACE, strokeWidth=2).encode(
            color=alt.Color("rate:Q", scale=alt.Scale(domain=[0, 1], range=RAMP), legend=alt.Legend(title="first sight", format=".1f", orient="right")))
        rings = base.transform_filter("datum.mentioned").mark_rect(fill=None, stroke=SLOTS[1], strokeWidth=2)
        text = base.mark_text(fontSize=11, fontWeight="bold").encode(
            text="grid:N", color=alt.condition("datum.rate > 0.55", alt.value("#fcfcfb" if not _DARK else "#0b0b0b"), alt.value("#0b0b0b" if not _DARK else "#ffffff")))
        return _themed(alt.layer(cells, rings, text).properties(width="container", height=24 * max(3, len(lessons)) + 30, title=title))

    def lesson_bars(df: pl.DataFrame, arms: list[str], lessons: list[str], title: str = "") -> alt.Chart:
        """First sight over the stream per lesson, one bar an arm, lessons ordered by tier — where the memory helped and where it did not."""
        return _themed(alt.Chart(df).mark_bar(cornerRadiusEnd=3).encode(
            x=alt.X("lesson:N", sort=lessons, axis=alt.Axis(title=None, labelAngle=0)),
            xOffset=alt.XOffset("arm:N", sort=present(df, arms)),
            y=alt.Y("rate:Q", scale=alt.Scale(domain=[0, 1]), axis=alt.Axis(title="first sight", tickCount=5, format=".1f")),
            color=alt.Color("arm:N", scale=slots(present(df, arms), arms), legend=alt.Legend(title=None, orient="top", direction="horizontal")),
            tooltip=[alt.Tooltip("arm:N"), alt.Tooltip("lesson:N"), alt.Tooltip("tier:N"), alt.Tooltip("rate:Q", format=".2f"), alt.Tooltip("count:N", title="passed / rows")],
        ).properties(width="container", height=220, title=title))

    def stacked_bars(df: pl.DataFrame, series: list[str], series_field: str, y_title: str, arms: list[str], title: str = "") -> alt.FacetChart:
        """Per pass, a bar stacked by series with a 2px surface gap between segments; one panel an arm."""
        return _themed(alt.Chart(df).mark_bar(stroke=SURFACE, strokeWidth=2, cornerRadiusEnd=2).encode(
            x=alt.X("pass:O", axis=alt.Axis(title="pass", labelAngle=0, grid=False)),
            y=alt.Y("value:Q", axis=alt.Axis(title=y_title, tickCount=4)),
            color=alt.Color(f"{series_field}:N", scale=slots(series), sort=series, legend=alt.Legend(title=None, orient="top", direction="horizontal")),
            order=alt.Order("order:Q"),
            tooltip=[alt.Tooltip("arm:N"), alt.Tooltip("pass:O"), alt.Tooltip(f"{series_field}:N"), alt.Tooltip("value:Q", format=",.0f", title=y_title),
                     alt.Tooltip("detail:N")],
        ).properties(width=max(220, 900 // max(1, len(present(df, arms)))), height=200).facet(
            column=alt.Column("arm:N", sort=present(df, arms), header=alt.Header(title=None, labelColor=INK, labelFontWeight="bold")), title=title))

    def competence_bars(df: pl.DataFrame, title: str = "") -> alt.Chart:
        """One row a record: its dispositions over the review window stacked left to right, applied first."""
        order = ["applied", "not_applicable", "guard_failed", "off_map"]
        return _themed(alt.Chart(df).mark_bar(stroke=SURFACE, strokeWidth=2, cornerRadiusEnd=3).encode(
            y=alt.Y("record:N", sort="-x", axis=alt.Axis(title=None, grid=False)),
            x=alt.X("count:Q", axis=alt.Axis(title="dispositions in the review window", tickMinStep=1, format="d")),
            color=alt.Color("disposition:N", scale=slots(order), sort=order, legend=alt.Legend(title=None, orient="top", direction="horizontal")),
            order=alt.Order("order:Q"),
            href="adjudicator:N",
            tooltip=[alt.Tooltip("record:N"), alt.Tooltip("disposition:N"), alt.Tooltip("count:Q"), alt.Tooltip("competence:N", title="applied ÷ considered")],
        ).properties(width="container", height=22 * max(2, df["record"].n_unique()) + 30, title=title))

    return ROLES, competence_bars, facet_lines, lesson_bars, lesson_heatmap, score_curve, slots, stacked_bars


@app.cell
def _(Path, Store, hevolution, hexperiment, root):
    # the arm's evolution log, live: `hgi.evolution` derives it from the store on every refresh
    _dir = Path(root).parent
    _file = Path("experiments") / f"{_dir.parent.name}.toml"
    exp = log = evo_error = None
    logs = {}
    arm_sessions = {}  # every arm's sessions, for the series the evolution log does not carry (wall-clock, activity)
    arm_after = {}  # every arm's consolidation id → the pass it followed: the backward pass's calls carry the consolidation as their session
    if _dir.parent.parent == hexperiment.runs_root() and _file.exists():
        _errors = []
        # `hgi` refuses with SystemExit, which is a BaseException: `except Exception` lets it through and marimo blanks every cell under it
        try:
            exp = hexperiment.load(_file)
        except (Exception, SystemExit) as _e:  # a half-written or stale arm names itself instead of killing the tab
            _errors.append(f"the experiment did not load: `{type(_e).__name__}: {_e}`")
        for _arm in dict.fromkeys([*exp.arms, _dir.name]) if exp is not None else ():
            try:  # arm by arm: a sibling arm that will not read must not blank the chosen one
                if (_l := hevolution.arm_log(exp, _arm)) is not None:
                    logs[_arm] = _l
                if (_s := hexperiment.arm_dir(exp, _arm) / "store").is_dir():
                    arm_sessions[_arm] = sorted((s for s in Store(_s).all("session") if s.evaluation is not None), key=lambda s: s.pass_)
                    arm_after[_arm] = {k.id: k.after_pass for k in Store(_s).all("consolidation")}
            except (Exception, SystemExit) as _e:
                _errors.append(f"the evolution log did not read: `{type(_e).__name__}: {_e}`" if _arm == _dir.name
                               else f"arm `{_arm}` was skipped: `{type(_e).__name__}: {_e}`")
        log = logs.get(_dir.name)
        evo_error = "; ".join(_errors) or None
    arm_names = list(exp.arms) if exp is not None else []
    focus_arm = _dir.name if exp is not None else None
    return arm_after, arm_names, arm_sessions, evo_error, exp, focus_arm, log, logs


@app.cell
def _(arm_names, exp, focus_arm, hexperiment, json, log, logs, mo, pl, score_curve, sessions):
    def _series(attached: bool):
        return [(s.pass_, s.evaluation.scores["task_pass_rate"].value) for s in sessions
                if s.attached == attached and s.evaluation and "task_pass_rate" in s.evaluation.scores]

    on, off = _series(True), _series(False)
    _COLS = {"arm": pl.Utf8, "mode": pl.Utf8, "pass": pl.Int64, "score": pl.Float64, "kind": pl.Utf8, "batch": pl.Utf8, "in_context": pl.Utf8, "after": pl.Utf8}
    _rows, _arms, _marks = [], [], []
    if exp is not None:
        # every arm of the experiment from its arm.json curve — written after each pass, so a running arm grows — with the
        # evolution log's batch, kind, context and consolidation on the point where the arm is a stream arm
        for _arm in arm_names:
            _p = hexperiment.arm_dir(exp, _arm) / "arm.json"
            if not _p.exists():
                continue
            _r = json.loads(_p.read_text())
            _by = {p["pass"]: p for p in logs.get(_arm, {}).get("passes", [])}
            _arms.append(_arm)
            for _n, _v in _r["curve"].items():
                _e = _by.get(int(_n))
                _k = _e["consolidation"] if _e else None
                _rows.append({"arm": _arm, "mode": _r["spec"]["mode"], "pass": int(_n), "score": _v,
                              "kind": _e["kind"] if _e else "pass", "batch": str(_e["batch"]) if _e else "—",
                              "in_context": " ".join(_e["in_context"]) or "none" if _e else "—",
                              "after": ("—" if _k is None else f"{_k['id']}: admitted {' '.join(_k['admitted']) or 'nothing'}") if _e else "—"})
        if log is not None:
            _at = {}
            for _d in log["records"]:
                if _d["admitted_after_pass"] is not None:
                    _at.setdefault(_d["admitted_after_pass"], []).append(_d["id"])
            _marks = [{"pass": p, "records": " ".join(ids), "lo": 0.0, "hi": 1.0} for p, ids in sorted(_at.items())]
    else:
        _arms = ["memory attached", "detached (ablation)"]
        _rows = [{"arm": a, "mode": m, "pass": p, "score": v, "kind": "pass", "batch": "—", "in_context": "—", "after": "—"}
                 for a, m, pts in (("memory attached", "attached", on), ("detached (ablation)", "detached", off)) for p, v in pts]
    curve_df = pl.DataFrame([r for r in _rows if r["score"] is not None], schema=_COLS)
    _title = (f"Experiment {exp.name} — task_pass_rate by pass, every arm; first sight per pass on a stream arm" if exp is not None
              else "Score curve — task_pass_rate by pass, same suite hash")
    # a plain chart, not `mo.ui.altair_chart`: marimo puts its point-selection param on every layer and projects it on x and
    # y, and the rule and label layers lose theirs in the compiled view, so the frontend listens for signals that do not
    # exist; the pass drill-down is the dropdown on the Passes tab
    _chart = score_curve(curve_df, _arms, focus=focus_arm, marks=pl.DataFrame(_marks, schema={"pass": pl.Int64, "records": pl.Utf8, "lo": pl.Float64, "hi": pl.Float64}), title=_title)
    curve = mo.vstack([
        mo.md("## " + ("First sight per pass — hover a point for the batch, the records in context and the consolidation after it" if log else "Score curve")),
        _chart if curve_df.height else mo.md("_no evaluated pass yet_"),
    ])
    return curve, curve_df, off, on


@app.cell
def _(exp, hexperiment, mo, trace_root, weave_project_url):
    overlay = mo.md("")
    if exp is not None:
        try:  # `hexperiment.report` resolves every arm, and a refusal there is a SystemExit
            overlay = mo.vstack([mo.md(f"## Experiment `{exp.name}`" + (f" — {exp.description}" if exp.description else "")),
                                 mo.md(hexperiment.report(exp).split("\n", 2)[2])]
                                + ([mo.md(f"[compare the arms' evaluations in Weave]({weave_project_url(trace_root, 'evaluations')})")] if trace_root else []))
        except (Exception, SystemExit) as _e:
            overlay = mo.md(f"⚠️ the experiment overlay did not read: `{type(_e).__name__}: {_e}`")
    return (overlay,)


@app.cell
def _(arm_names, arm_sessions, evo_error, exp, facet_lines, hevolution, log, logs, mo, pl):
    # the paired attached-vs-detached report, the arms' solution quality beside their correctness, and what each pass cost
    evolution_view = _warning = mo.md(f"⚠️ {evo_error}") if evo_error else mo.md("")
    _QUAL = ["economy", "turns", "transfer"]
    _ACT = ["wall-clock (s)", "records considered", "observations filed", "tool calls"]
    _q = pl.DataFrame([{"arm": a, "measure": q, "pass": p["pass"], "value": p["quality"][q]}
                       for a, l in logs.items() for p in l["passes"] for q in _QUAL if p["quality"][q] is not None],
                      schema={"arm": pl.Utf8, "measure": pl.Utf8, "pass": pl.Int64, "value": pl.Float64})
    _a = pl.DataFrame([{"arm": a, "measure": m, "pass": s.pass_, "value": v} for a, ss in arm_sessions.items() for s in ss for m, v in (
        ("wall-clock (s)", (s.closed_at - s.started_at).total_seconds() if s.closed_at else None),
        ("records considered", len(s.considered)), ("observations filed", len(s.observations_filed)),
        ("tool calls", sum(r.get("tool_calls") or 0 for r in s.evaluation.rows))) if v is not None],
        schema={"arm": pl.Utf8, "measure": pl.Utf8, "pass": pl.Int64, "value": pl.Float64})
    if exp is not None:
        evolution_view = mo.vstack([
            _warning,  # a sibling arm that would not read still says so over the chosen arm's report
            mo.md(hevolution.experiment_markdown(exp, logs)) if logs else mo.md(""),
            mo.md("## Solution quality per pass — `economy` / `turns` / `transfer`, mean over the pass's rows, one panel a measure"),
            facet_lines(_q, arm_names, _QUAL) if _q.height else mo.md("_no quality series is evaluable on this experiment_"),
            mo.md("## What a pass cost — wall-clock and memory activity per pass, one panel a measure; a detached arm consults nothing, so its rows sit at zero"),
            facet_lines(_a, arm_names, _ACT, columns=4) if _a.height else mo.md("_no closed pass yet_"),
        ])
    return (evolution_view,)


@app.cell
def _(exp, hevolution, lesson_bars, lesson_heatmap, log, logs, mo, pl, slessons):
    GLYPH = {"✓": "#2a7", "N": "#d92", "W": "#c55", "E": "#888"}

    def _cell(s):
        """One lesson's rows in one pass; a mentioned pass is ringed and says so on hover."""
        glyphs = "".join(f'<span style="color:{GLYPH.get(c, "#888")};font-weight:600">{c}</span>' for c in s["grid"])
        ring = ('style="border:2px solid #36c" title="a record in context mentions this lesson"' if s["mentioned"] else 'style="border:1px solid #eee"')
        return f'<td align="center" {ring}>{glyphs}{"<sup style=color:#36c>•</sup>" if s["mentioned"] else ""}</td>'

    _tier = lambda l: slessons.TIERS.index(slessons.tier(l)) if slessons.tier(l) in slessons.TIERS else 9
    lessons_view = mo.md("")
    if log is not None:
        _cols = [f"p{_x['pass']}" + ("r" if _x["kind"] == "revisit" else "") for _x in log["passes"]]
        _head = ("<tr><th align=left>lesson</th><th>tier</th>" + "".join(f"<th>{c}</th>" for c in _cols)
                 + "<th>first sight</th><th>naive before / after</th><th>first mention</th><th>economy / turns / transfer</th></tr>")
        _rows = []
        _ordered = sorted(log["lessons"], key=lambda l: (_tier(l), l))
        for _lesson in _ordered:
            _s = log["lessons"][_lesson]
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
        _heat = pl.DataFrame([{"lesson": l, "tier": log["lessons"][l]["tier"] or "—", "column": f"p{s['pass']}" + ("r" if s["kind"] == "revisit" else ""),
                               "rate": s["passed"] / s["tasks"], "grid": s["grid"], "mentioned": s["mentioned"]}
                              for l in _ordered for s in log["lessons"][l]["series"] if s["tasks"]],
                             schema={"lesson": pl.Utf8, "tier": pl.Utf8, "column": pl.Utf8, "rate": pl.Float64, "grid": pl.Utf8, "mentioned": pl.Boolean})
        _all = sorted({l for lg in logs.values() for l in lg["lessons"]}, key=lambda l: (_tier(l), l))
        _bars = pl.DataFrame([{"arm": a, "lesson": l, "tier": lg["lessons"][l]["tier"] or "—",
                               "rate": lg["lessons"][l]["first_sight"][0] / lg["lessons"][l]["first_sight"][1],
                               "count": hevolution._rate(*lg["lessons"][l]["first_sight"])}
                              for a, lg in logs.items() for l in _all if l in lg["lessons"] and lg["lessons"][l]["first_sight"][1]],
                             schema={"arm": pl.Utf8, "lesson": pl.Utf8, "tier": pl.Utf8, "rate": pl.Float64, "count": pl.Utf8})
        lessons_view = mo.vstack([
            mo.md(f"## Lessons — `{log['experiment']}/{log['arm']}`, one row a lesson, one column a pass"),
            lesson_heatmap(_heat, _ordered, title="first sight per lesson per pass — noisy by construction: a lesson is met once a batch, so a cell is one or two rows; an orange ring is a mention in context"),
            mo.accordion({"the symptom grid — every row's glyph, with the floors beside it": mo.vstack([_grid, _legend])}),
            mo.md("## First sight over the stream per lesson, every arm — lessons in tier order, loud to invisible"),
            lesson_bars(_bars, list(exp.arms), _all, title="passed ÷ rows over every stream pass; the naive-shape floors are in the grid above"),
            mo.md("## Reading\n\n" + hevolution.experiment_markdown(exp, logs).split("## Reading", 1)[-1].strip()),
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
def _(mo, trace_root):
    pull = mo.ui.run_button(label="pull usage from Weave", disabled=trace_root is None)
    return (pull,)


@app.cell
def _(ROLES, arm_after, arm_names, exp, focus_arm, mo, pl, pull, sessions, slots, stacked_bars, store, trace_root):
    # The compute tab: the trace store is the only place a call's tokens and latency live, and every call an arm made
    # carries `attributes.hgi.{experiment, arm, pass, role}` — so one filtered query gives where the tokens and the
    # seconds went, by pass, by role and by the model that served the call. Pulled on request: a network read.
    compute_view = mo.vstack([mo.md("## Compute — tokens and latency per pass, by role and by the model that served the call"),
                              mo.md("_untraced run: nothing in the trace store to read_" if trace_root is None else
                                    "Every model call is in Weave with its tokens, its latency and the arm, pass and role it served. Pull them to chart what the memory costs."), pull])
    usage_df = None
    if pull.value and trace_root:
        try:
            import weave

            _project = trace_root.removeprefix("weave:///").split("/call/")[0]
            _client = weave.init(_project)
            _q = ({"$eq": [{"$getField": "attributes.hgi.experiment"}, {"$literal": exp.name}]} if exp is not None else
                  {"$or": [{"$eq": [{"$getField": "attributes.hgi.session"}, {"$literal": s.id}]} for s in sessions]})
            _q = {"$expr": {"$and": [_q, {"$contains": {"input": {"$getField": "op_name"}, "substr": {"$literal": "chat.completions.create"}}}]}}
            _rows = []
            _after = arm_after if exp is not None else {None: {k.id: k.after_pass for k in store.all("consolidation")}}
            for _c in _client.get_calls(query=_q, columns=["op_name", "attributes", "summary", "started_at", "ended_at"], limit=50000):
                _h = (_c.attributes or {}).get("hgi") or {}
                _arm = _h.get("arm") or ("attached" if any(s.id == _h.get("session") and s.attached for s in sessions) else "detached")
                if exp is not None and _arm not in arm_names:
                    continue
                # a forward-pass call names its pass; a backward-pass call names its consolidation, charged to the pass it followed
                _pass = _h.get("pass") if _h.get("pass") is not None else _after.get(_arm if exp is not None else None, {}).get(_h.get("session"))
                if _pass is None:
                    continue
                for _model, _u in ((_c.summary or {}).get("usage") or {}).items():
                    _rows.append({"arm": _arm, "pass": int(_pass), "role": _h.get("role") or "?", "model": _model,
                                  "prompt": float(_u.get("prompt_tokens") or 0), "completion": float(_u.get("completion_tokens") or 0),
                                  "latency_s": float(((_c.summary or {}).get("weave") or {}).get("latency_ms") or 0) / 1000, "calls": 1.0})
            usage_df = pl.DataFrame(_rows, schema={"arm": pl.Utf8, "pass": pl.Int64, "role": pl.Utf8, "model": pl.Utf8, "prompt": pl.Float64,
                                                    "completion": pl.Float64, "latency_s": pl.Float64, "calls": pl.Float64})
        except Exception as _e:
            compute_view = mo.vstack([compute_view, mo.md(f"⚠️ the trace store did not answer: `{type(_e).__name__}: {_e}`")])
    if usage_df is not None and usage_df.height:
        _arms = arm_names or ["attached", "detached"]
        _roles = [r for r in ROLES if r in set(usage_df["role"])] + sorted(set(usage_df["role"]) - set(ROLES))
        _g = (usage_df.group_by("arm", "pass", "role").agg(pl.col("prompt").sum(), pl.col("completion").sum(), pl.col("latency_s").sum(), pl.col("calls").sum())
              .with_columns((pl.col("prompt") + pl.col("completion")).alias("tokens"), pl.col("role").map_elements(_roles.index, return_dtype=pl.Int64).alias("order")))
        _tok = _g.with_columns(pl.col("tokens").alias("value"),
                               pl.format("{} calls · prompt {} · completion {}", pl.col("calls").cast(pl.Int64), pl.col("prompt").cast(pl.Int64), pl.col("completion").cast(pl.Int64)).alias("detail"))
        _lat = _g.with_columns(pl.col("latency_s").alias("value"), pl.format("{} calls · {} s per call", pl.col("calls").cast(pl.Int64), (pl.col("latency_s") / pl.col("calls")).round(1)).alias("detail"))
        _per_arm = usage_df.group_by("arm").agg(pl.col("prompt").sum(), pl.col("completion").sum(), pl.col("latency_s").sum(), pl.col("calls").sum()).sort("arm")
        _per_model = (usage_df.group_by("arm", "model", "role").agg(pl.col("calls").sum().cast(pl.Int64), pl.col("prompt").sum().cast(pl.Int64), pl.col("completion").sum().cast(pl.Int64),
                                                                     (pl.col("latency_s").sum() / pl.col("calls").sum()).round(2).alias("mean latency (s)"))
                      .sort("arm", "model", "role"))
        _passed = {a: sum(r.get("scores", {}).get("task_pass_rate", {}).get("value") == 1.0 for s in ss for r in s.evaluation.rows)
                   for a, ss in (((focus_arm, sessions),) if exp is None else ())}
        compute_view = mo.vstack([
            compute_view,
            mo.hstack([mo.stat(f"{int(r['prompt'] + r['completion']):,}", label=f"{r['arm']} · tokens", bordered=True,
                               caption=f"{int(r['calls'])} calls · {r['latency_s'] / 60:.1f} min of model latency") for r in _per_arm.iter_rows(named=True)],
                      justify="start", gap=0.6, widths="equal"),
            stacked_bars(_tok, _roles, "role", "tokens", _arms, title="tokens per pass, stacked by role — prompt and completion together, the backward pass charged to the pass it followed; hover for the split"),
            stacked_bars(_lat, _roles, "role", "seconds", _arms, title="model latency per pass, stacked by role — the seconds the endpoint took, summed over the pass's calls"),
            mo.md("### By the model that served the call — one row an arm × model × role; the endpoint dimension"),
            mo.ui.table(_per_model.to_dicts()),
        ])
    return compute_view, usage_df


@app.cell
def _(competence_bars, hindex, mo, pl, store, wcell, weave_url):
    hooks = hindex.read(store, "hooks")
    _adjudicator = {d.id: d.admission.adjudicator.call if d.admission.adjudicator else None for d in store.decisions("accepted")}
    competence = [{**r, "adjudicator": wcell(_adjudicator.get(r["record"]))} for r in hindex.read(store, "competence")]
    _bars = pl.DataFrame([{"record": r["record"], "disposition": d, "count": r.get(d, 0), "order": i,
                           "adjudicator": weave_url(_adjudicator.get(r["record"])) or "",
                           "competence": f"{r['applied']} / {r['considered']}" if r.get("considered") else "—"}
                          for r in hindex.read(store, "competence") for i, d in enumerate(("applied", "not_applicable", "guard_failed", "off_map")) if r.get(d)],
                         schema={"record": pl.Utf8, "disposition": pl.Utf8, "count": pl.Int64, "order": pl.Int64, "adjudicator": pl.Utf8, "competence": pl.Utf8})
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
        competence_bars(_bars, title="dispositions per accepted record over the review window — click a bar for the adjudicator's call in Weave") if _bars.height else mo.md(""),
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
def _(compute_view, curve, escalations, evolution_view, floor, ledger, lessons_view, lineage, log, matrix, mo, overlay, passes_view, projections, verdicts):
    _not_stream = mo.md("not a stream arm; the Loop tab has the curve")
    mo.ui.tabs({
        "Loop": mo.vstack([curve, overlay, evolution_view]),
        "Lessons": lessons_view if log is not None else _not_stream,
        "Passes": passes_view if log is not None else _not_stream,
        "Compute": compute_view,
        "Store": mo.vstack([projections, ledger, lineage, matrix]),
        "Queue": mo.vstack([escalations, verdicts]),
        "Floor": floor,
    })
    return


if __name__ == "__main__":
    app.run()
