# /// script
# requires-python = ">=3.14"
# dependencies = ["marimo", "hgi"]
# ///
"""The marimo dashboard: the projection surface, the escalation queue and the runnable acceptance bar.

Every cell renders live from the store — the projection law of § 7 as a UI. The notebook reads the
store; it writes only through ``hgi`` commands (the queue's two buttons shell out to ``hgi queue``).

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

    from hgi import index as hindex
    from hgi.store import Store

    root = Path(os.environ.get("HGI_STORE", "store"))
    refresh = mo.ui.refresh(options=["5s", "30s"], default_interval=None)
    return Path, Store, hindex, json, mo, os, refresh, root, subprocess


@app.cell
def _(Store, mo, refresh, root):
    refresh
    store = Store(root)
    sessions = sorted(store.all("session"), key=lambda s: (s.pass_, not s.attached))
    mo.vstack([mo.md(f"# HGI — `{root}`"), refresh])
    return sessions, store


@app.cell
def _(mo, sessions):
    def _series(attached: bool):
        return [(s.pass_, s.evaluation.scores["task_pass_rate"].value) for s in sessions
                if s.attached == attached and s.evaluation and "task_pass_rate" in s.evaluation.scores]

    on, off = _series(True), _series(False)
    _w, _h, _pad = 640, 240, 36
    _passes = sorted({p for p, _ in on + off}) or [1]
    _x = lambda p: _pad + (p - min(_passes)) * (_w - 2 * _pad) / max(1, max(_passes) - min(_passes))
    _y = lambda v: _h - _pad - (v or 0) * (_h - 2 * _pad)

    def _path(points, color):
        pts = [(p, v) for p, v in points if v is not None]
        if not pts:
            return ""
        d = " ".join(f"{'M' if i == 0 else 'L'}{_x(p):.1f},{_y(v):.1f}" for i, (p, v) in enumerate(pts))
        dots = "".join(f'<circle cx="{_x(p):.1f}" cy="{_y(v):.1f}" r="4" fill="{color}"/>' for p, v in pts)
        return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="2"/>{dots}'

    _axes = (f'<line x1="{_pad}" y1="{_h-_pad}" x2="{_w-_pad}" y2="{_h-_pad}" stroke="#888"/>'
             f'<line x1="{_pad}" y1="{_pad}" x2="{_pad}" y2="{_h-_pad}" stroke="#888"/>'
             + "".join(f'<text x="{_x(p):.1f}" y="{_h-_pad+16}" font-size="11" text-anchor="middle">{p}</text>' for p in _passes)
             + "".join(f'<text x="{_pad-6}" y="{_y(v)+4:.1f}" font-size="11" text-anchor="end">{v:.1f}</text>' for v in (0, 0.5, 1.0)))
    _legend = ('<rect x="440" y="10" width="12" height="12" fill="#2a7"/><text x="458" y="21" font-size="12">memory attached</text>'
               '<rect x="440" y="30" width="12" height="12" fill="#c55"/><text x="458" y="41" font-size="12">detached (ablation)</text>')
    curve = mo.Html(f'<svg width="{_w}" height="{_h}" style="background:#fff;border:1px solid #ddd">{_axes}{_path(off, "#c55")}{_path(on, "#2a7")}{_legend}</svg>')
    mo.vstack([mo.md("## Score curve — `task_pass_rate` by pass, same suite hash"), curve])
    return curve, off, on


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
