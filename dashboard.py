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

    uv run marimo run dashboard.py        # the app
    uv run marimo edit dashboard.py       # the notebook
"""

import marimo

__generated_with = "0.24.2"
app = marimo.App(width="wide", app_title="HGI")


@app.cell
def _():
    import json
    import os
    import subprocess
    from pathlib import Path

    import marimo as mo

    from hgi import experiment as hexperiment
    from hgi import index as hindex
    from hgi.cli import load_env
    from hgi.store import Store

    load_env()
    stores = {"store — the demonstration": Path("store")} | {
        f"{p.parents[1].name}/{p.parent.name}": p for p in sorted(hexperiment.runs_root().glob("*/*/store"))
    }
    _default = next((k for k, v in stores.items() if str(v) == os.environ.get("HGI_STORE", "store")), next(iter(stores)))
    picker = mo.ui.dropdown(options=stores, value=_default, label="store")
    refresh = mo.ui.refresh(options=["5s", "30s"], default_interval=None)
    return Path, Store, hexperiment, hindex, json, mo, os, picker, refresh, subprocess


@app.cell
def _(Store, mo, picker, refresh):
    refresh
    root = picker.value
    store = Store(root)
    sessions = sorted(store.all("session"), key=lambda s: (s.pass_, not s.attached))
    mo.vstack([mo.md(f"# HGI — `{root}`"), mo.hstack([picker, refresh], justify="start")])
    return root, sessions, store


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
def _(curve_svg, mo, sessions):
    def _series(attached: bool):
        return [(s.pass_, s.evaluation.scores["task_pass_rate"].value) for s in sessions
                if s.attached == attached and s.evaluation and "task_pass_rate" in s.evaluation.scores]

    on, off = _series(True), _series(False)
    curve = curve_svg({"memory attached": on, "detached (ablation)": off})
    mo.vstack([mo.md("## Score curve — `task_pass_rate` by pass, same suite hash"), curve])
    return curve, off, on


@app.cell
def _(Path, curve_svg, hexperiment, json, mo, root):
    _arm_dir = Path(root).parent
    _file = Path("experiments") / f"{_arm_dir.parent.name}.toml"
    _view = mo.md("")
    if _arm_dir.parent.parent == hexperiment.runs_root() and _file.exists():
        _exp = hexperiment.load(_file)
        _arms = {a: json.loads(p.read_text()) for a in _exp.arms if (p := hexperiment.arm_dir(_exp, a) / "arm.json").exists()}
        _series = {f"{a} · {r['roster']['pass']}" + (" (detached)" if r["spec"]["mode"] == "detached" else ""):
                   [(int(p), v) for p, v in r["curve"].items()] for a, r in _arms.items()}
        _view = mo.vstack([mo.md(f"## Experiment `{_exp.name}` — every arm on one chart" + (f": {_exp.description}" if _exp.description else "")),
                           curve_svg(_series), mo.md(hexperiment.report(_exp).split("\n", 2)[2])])
    _view
    return


@app.cell
def _(hindex, mo, store):
    hooks = hindex.read(store, "hooks")
    competence = hindex.read(store, "competence")
    fires = hindex.read(store, "fires")
    zero = hindex.read(store, "structural_zero")
    mo.vstack([
        mo.md("## Projections"),
        mo.md("### Hook-major index — a cell carries what a reader cannot obey without opening the record"),
        mo.ui.table([{"term": t, **c} for t, cells in hooks.items() for c in cells]) if hooks else mo.md("_no live consultation hook_"),
        mo.md("### Competence — applied ÷ considered; a nominator, never a verdict"),
        mo.ui.table(competence) if competence else mo.md("_no accepted decision_"),
        mo.md(f"### Undischarged fires: {len(fires)} · structural zero: {zero or 'none'}"),
        mo.ui.table(fires) if fires else mo.md("_none_"),
    ])
    return competence, fires, hooks, zero


@app.cell
def _(hindex, mo, store):
    graph = hindex.read(store, "lineage")
    _lines = ["graph LR"] + [f'  {e["from"].replace("-", "_")}(["{e["from"]}"]) -->|{e["kind"]}| {e["to"].replace("-", "_")}(["{e["to"]}"])' for e in graph["edges"]]
    mo.vstack([mo.md("## Lineage DAG"), mo.mermaid("\n".join(_lines)) if graph["edges"] else mo.md("_no lineage yet_")])
    return (graph,)


@app.cell
def _(hindex, mo, store):
    m = hindex.read(store, "matrix")
    _cell = lambda k: len(m.get(k, []))
    mo.vstack([
        mo.md("## Detection matrix — every count is a floor"),
        mo.ui.table([
            {"": "system catches", "oracle or human catches": _cell("system-catches/oracle-catches") + _cell("system-catches/human-catches"), "neither catches": _cell("system-catches/none-catches")},
            {"": "system misses", "oracle or human catches": _cell("system-misses/oracle-catches") + _cell("system-misses/human-catches"), "neither catches": f"≥ {_cell('system-misses/none-catches')} (detection-limited)"},
        ]),
    ])
    return (m,)


@app.cell
def _(mo, store):
    queue = store.queue()
    admit = {q.draft.uid: mo.ui.button(label=f"admit {q.draft.name}", value=q.draft.uid) for q in queue}
    decline = {q.draft.uid: mo.ui.button(label=f"decline {q.draft.name}", value=q.draft.uid) for q in queue}
    mo.vstack([mo.md(f"## Escalation queue — {len(queue)} awaiting a human verdict")] + [
        mo.vstack([mo.md(f"**{q.draft.name}** · {q.why} · ledger {q.ledger_entry}\n\n> {q.draft.body.decision}\n\n"
                         f"attack: {json_dumps(q.oracle_evidence.get('attack', {}))}"), mo.hstack([admit[q.draft.uid], decline[q.draft.uid]])])
        for q in queue
    ] or [mo.md("_empty_")])
    return admit, decline, queue


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
    mo.md("\n".join(f"`{o.strip()}`" for o in _out if o) or "")
    return


@app.cell
def _(mo, root, subprocess):
    _lint = subprocess.run(["uv", "run", "hgi", "--store", str(root), "lint"], capture_output=True, text=True)
    mo.vstack([mo.md("## The floor"), mo.md(f"```\n{_lint.stdout.strip()}\n```")])
    return


if __name__ == "__main__":
    app.run()
