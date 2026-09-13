"""``hgi consult`` — the decision store read from outside the loop, through its projections.

The loop reads the store at boot: a model call classifies the work into
registered terms, the hook-major index matches them, a guard evaluator
decides each fire, and the fired records enter the pass's context. An agent
that is not the pass — a person's coding assistant with a problem, a
sibling project, a skill — has the same store and none of the loop's
machinery, and this command is its read. It is read-only: no session, no
disposition, no commit, and nothing under the store changes.

The read is two-staged, and the split is the settlement test (spec § 8.2):

1. **the surface** — one cell per decision, from the ``summaries`` and
   ``hooks`` projections: the hook prose the record is recognised by, the
   registered terms its consultation latch keys on, the exclusions, the
   stakes, the scopes, the watch. Nothing here can be complied with; a
   reader matches it against the work at hand and opens what matched. A
   superseded record is a tombstone pointing at its successor.
2. **the projection** — the payload of the records the reader named or
   the latch reached: the decision sentence, the counterfactual, the
   premises with their status, the anchors, the lineage. The full record
   stays the authority; the projection is what an agent can carry into a
   context without opening the store.

Two latches shortcut the reader's own match, both mechanical and both the
boot's: ``--terms`` routes registered terms through the hook-major index
exactly as stage one does, and ``--problem`` runs the lexical nominator —
stemmed token overlap against hook prose — whose hits are *nominated*, never
fired: the reader judges the exclusions, since no guard evaluator runs
here. A cell in either stage says which route reached it.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from typing import Any

from hgi import index as _index
from hgi.registry import is_escape
from hgi.store import Store
from hgi.types import Decision

LEXICAL_FLOOR = 2
"""Stemmed tokens a problem statement must share with a record's hook prose to nominate it — the boot's own floor."""

NOMINATED = "nominated by the lexical route; no guard ran — read the exclusions before applying"
NOTHING = "latched: nothing — no registered term named and no hook prose shared two tokens with the problem; the surface follows for your own match"
TOMBSTONE = "superseded; the successor carries the lesson"


# --- stage one: the surface ------------------------------------------------------------

def terms_by_record(store: Store) -> dict[str, list[str]]:
    """Record → the registered terms its live consultation latches key on, read off the hook-major projection."""
    out: dict[str, set[str]] = defaultdict(set)
    for term, cells in _index.read(store, "hooks").items():
        for cell in cells:
            out[cell["record"]].add(term)
    return {r: sorted(t) for r, t in out.items()}


def successors(store: Store) -> dict[str, list[str]]:
    """Record → the records that retired it, read off the lineage projection: a supersedure, a split's heirs, or a fold."""
    out: dict[str, list[str]] = defaultdict(list)
    for e in _index.read(store, "lineage")["edges"]:
        if e["kind"] in ("supersedes", "split", "fold"):
            out[e["from"]].append(e["to"])
    return {r: sorted(set(s)) for r, s in out.items()}


def surface(store: Store) -> list[dict[str, Any]]:
    """Stage one: every decision's activation cell. Passes the settlement test by construction — it is built from cells that do."""
    terms = terms_by_record(store)
    heirs = successors(store)
    cells = []
    for row in _index.read(store, "summaries"):
        cell = {"record": row["record"], "status": row["status"]}
        if row["status"] == "accepted":
            cell.update(latch=row["latch"], terms=terms.get(row["record"], []), not_this=row["not_this"],
                        stakes=row["stakes"], scopes=row["scopes"], watch=row["watch"])
        else:
            cell["successors"] = heirs.get(row["record"], [])
        cells.append(cell)
    return cells


# --- the latch -------------------------------------------------------------------------

def infer_terms(store: Store, problem: str) -> list[str]:
    """The registered terms a problem statement names outright: every token of the term's name appears in the problem."""
    present = _index.tokens(problem)
    return [t for t in store.registry.terms("work-shape") if not is_escape(t) and _index.tokens(t.replace("-", " ")) <= present]


def latch(store: Store, *, terms: list[str] | None = None, problem: str = "") -> list[dict[str, Any]]:
    """Stage-one selection for a reader: which accepted records the given terms and problem reach, and by which route.

    Registered terms route through the hook-major index, exactly the boot's
    route; a term the registry lacks is refused by name, since an escape
    reaches nothing. A problem statement infers the terms it names and then
    runs the lexical nominator over hook prose; a lexical hit is marked
    nominated and carries the tokens it shared. An exclusion whose text the
    problem contains is reported as ``excluded_by`` — the stub guard's
    reading, offered as a flag for the reader, never as a verdict.
    """
    registered = store.registry.terms("work-shape")
    asked = list(terms or [])
    unknown = [t for t in asked if t not in registered]
    if unknown:
        raise SystemExit(f"not registered work-shape terms: {', '.join(unknown)}; the registry holds {', '.join(registered)}")
    inferred = infer_terms(store, problem) if problem else []
    hooks = _index.read(store, "hooks")
    reached: dict[str, dict[str, Any]] = {}
    for term in dict.fromkeys([*asked, *inferred]):
        for cell in hooks.get(term, []):
            hit = reached.setdefault(cell["record"], {"record": cell["record"], "via": "index", "terms_matched": [], "not_this": cell["not_this"]})
            hit["terms_matched"].append(term)
    if problem:
        presented = _index.tokens(problem)
        for row in _index.read(store, "summaries"):
            if row["record"] in reached or row["status"] != "accepted":
                continue
            overlap = presented & _index.tokens(row["latch"])
            if len(overlap) >= LEXICAL_FLOOR:
                reached[row["record"]] = {"record": row["record"], "via": "lexical", "terms_matched": sorted(overlap), "not_this": row["not_this"],
                                          "note": NOMINATED}
        lowered = problem.lower()
        for hit in reached.values():
            excluded = [n for n in hit["not_this"] if n.lower() in lowered]
            if excluded:
                hit["excluded_by"] = excluded
    for hit in reached.values():
        hit["terms_matched"] = sorted(set(hit["terms_matched"]))
    return sorted(reached.values(), key=lambda h: (h["via"] != "index", -len(h["terms_matched"]), h["record"]))


# --- stage two: the projection ---------------------------------------------------------

def project(store: Store, ids: list[str]) -> list[dict[str, Any]]:
    """Stage two: the payload of each named decision — what a reader carries into a context. An id the store lacks is refused."""
    missing = [i for i in ids if not store.exists("decision", i)]
    if missing:
        raise SystemExit(f"no decision named {', '.join(missing)}")
    heirs = successors(store)
    out = []
    for i in ids:
        d: Decision = store.read("decision", i)  # type: ignore[assignment]
        cell = {
            "record": d.id, "status": d.status, "decision": d.decision, "counterfactual": d.counterfactual,
            "latch": d.summary.latch, "terms": sorted(set(d.consultation_terms)),
            "not_this": sorted(set(d.summary.not_this) | set(d.consultation_not_this)),
            "stakes": d.summary.stakes, "scopes": d.scopes, "context": d.context,
            "options": [{"name": o.name, "judged": o.judged, "why": o.why} for o in d.options],
            "premises": [{"id": p.id, "statement": p.statement, "falsifier": p.falsifier, "status": p.status} for p in d.warrant.premises],
            "floor": d.enforcement.floor, "residue": d.enforcement.residue,
            "anchors": d.warrant.anchors, "watch": _index.watch_of(d),
            "lineage": {"supersedes": d.lineage.supersedes, "superseded_by": d.lineage.superseded_by,
                        "split_from": d.lineage.split_from, "folded_from": d.lineage.folded_from},
            "priced_for": d.priced_for.model_id,
        }
        if d.status != "accepted":
            cell["note"] = TOMBSTONE
            cell["successors"] = heirs.get(d.id, d.lineage.superseded_by)
        out.append(cell)
    return out


def articles(store: Store) -> list[dict[str, Any]]:
    """The constitution: the stratum every pass loads unconditionally, offered to a reader who asks for it."""
    return [{"record": a.id, "article": a.article, "counterfactual": a.counterfactual} for a in store.articles()]


# --- rendering -------------------------------------------------------------------------

def _list(xs: list[str]) -> str:
    return "; ".join(xs) if xs else "(none)"


def render_surface(cells: list[dict[str, Any]], vocabulary: list[str]) -> str:
    lines = ["== decision surface — activation only; nothing here settles a question ==",
             f"registered terms: {', '.join(vocabulary)}", ""]
    for c in cells:
        if c["status"] != "accepted":
            lines.append(f"{c['record']}  [{c['status']}" + (f" -> {', '.join(c['successors'])}" if c["successors"] else "") + "]")
            lines.append("")
            continue
        lines += [f"{c['record']}  [{c['status']}]  terms: {', '.join(c['terms']) or '(no registered hook reaches it)'}",
                  f"  latch:    {c['latch']}",
                  f"  not_this: {_list(c['not_this'])}",
                  f"  stakes:   {c['stakes']}",
                  f"  scopes:   {_list(c['scopes'])}   watch: {c['watch']}", ""]
    lines.append("open what matched: hgi consult D-nnnn …   — or latch: --terms <term,…> | --problem \"<the work at hand>\"")
    return "\n".join(lines)


def render_latch(hits: list[dict[str, Any]]) -> str:
    if not hits:
        return NOTHING
    lines = [f"latched {len(hits)}:"]
    for h in hits:
        line = f"  {h['record']} via {h['via']} ({', '.join(h['terms_matched'])})"
        if h.get("excluded_by"):
            line += f" — the problem names an exclusion: {_list(h['excluded_by'])}"
        if h.get("note"):
            line += f" — {h['note']}"
        lines.append(line)
    return "\n".join(lines)


def render_projection(cells: list[dict[str, Any]], co_applying: list[list[str]] = ()) -> str:
    lines = []
    for group in co_applying:
        lines.append(f"co-applying: {', '.join(group)} — no specificity order; apply each where it bears")
    for c in cells:
        lines += [f"== {c['record']}  [{c['status']}]  terms: {', '.join(c['terms']) or '(none)'}  scopes: {_list(c['scopes'])}",
                  f"  decision:       {c['decision']}",
                  f"  counterfactual: {c['counterfactual']}",
                  f"  latch:          {c['latch']}",
                  f"  not_this:       {_list(c['not_this'])}",
                  f"  stakes:         {c['stakes']}",
                  f"  residue:        {_list(c['residue'])}   floor: {_list(c['floor'])}",
                  f"  context:        {c['context']}"]
        for o in c["options"]:
            lines.append(f"  option {o['judged']:8} {o['name']} — {o['why']}")
        for p in c["premises"]:
            lines.append(f"  premise {p['id']} [{p['status']}] {p['statement']} — falsified by: {p['falsifier']}")
        lines.append(f"  anchors: {_list(c['anchors'])}   watch: {c['watch']}   priced for: {c['priced_for'] or 'unpriced'}")
        edges = {k: v for k, v in c["lineage"].items() if v}
        if edges:
            lines.append("  lineage: " + "; ".join(f"{k} {', '.join(v) if isinstance(v, list) else v}" for k, v in edges.items()))
        if c.get("note"):
            lines.append(f"  note: {c['note']}" + (f" — {', '.join(c['successors'])}" if c.get("successors") else ""))
        lines.append("")
    return "\n".join(lines).rstrip()


def render_articles(cells: list[dict[str, Any]]) -> str:
    lines = ["== constitution — loaded with every pass =="]
    for a in cells:
        lines += [f"  {a['record']}: {a['article']}", f"      overshoot: {a['counterfactual']}"]
    return "\n".join(lines)


# --- the command ------------------------------------------------------------------------

def consult(store: Store, *, ids: list[str] | None = None, terms: list[str] | None = None, problem: str = "",
            everything: bool = False, with_articles: bool = False) -> dict[str, Any]:
    """The read as one structure: the surface when nothing is named, else the latch and the projection of what it reached."""
    from hgi.boot import co_applying

    out: dict[str, Any] = {"store": str(store.root)}
    if with_articles:
        out["articles"] = articles(store)
    if everything:
        ids = [d.id for d in store.decisions("accepted")]
    hits = latch(store, terms=terms, problem=problem) if (terms or problem) else None
    if hits is not None:
        out["latched"] = hits
    wanted = list(dict.fromkeys([*(ids or []), *(h["record"] for h in hits or [])]))
    if not wanted:
        # Nothing named and nothing latched: the broadening fallback is the whole surface, for the reader's own match.
        out["surface"] = surface(store)
        return out
    out["records"] = project(store, wanted)
    accepted = [r["record"] for r in out["records"] if r["status"] == "accepted"]
    out["co_applying"] = co_applying(store, accepted) if len(accepted) > 1 else []
    return out


def render(out: dict[str, Any], vocabulary: list[str]) -> str:
    parts = []
    if "articles" in out:
        parts.append(render_articles(out["articles"]))
    if "latched" in out:
        parts.append(render_latch(out["latched"]))
    if "surface" in out:
        parts.append(render_surface(out["surface"], vocabulary))
    if out.get("records"):
        parts.append(render_projection(out["records"], out.get("co_applying", [])))
    return "\n\n".join(parts)


def register(add, store_of, finish) -> None:
    p = add("consult", "read the decision store from outside the loop: the surface, or the payload of what a latch reaches")
    p.add_argument("ids", nargs="*", help="decision ids to project in full")
    p.add_argument("--terms", help="registered work-shape terms, comma-separated, routed through the hook-major index")
    p.add_argument("--problem", default="", help="the work at hand, in prose; infers terms and nominates by hook prose")
    p.add_argument("--all", dest="everything", action="store_true", help="project every accepted record")
    p.add_argument("--articles", action="store_true", help="include the constitution")
    p.add_argument("--json", action="store_true", help="the structure, not the rendering")
    p.set_defaults(fn=lambda args: _cmd(args, store_of))


def _cmd(args, store_of) -> int:
    store = store_of(args)
    terms = [t.strip() for t in (args.terms or "").split(",") if t.strip()]
    out = consult(store, ids=args.ids, terms=terms, problem=args.problem, everything=args.everything, with_articles=args.articles)
    if args.json:
        json.dump(out, sys.stdout, indent=2, ensure_ascii=False)
        print()
    else:
        print(render(out, store.registry.terms("work-shape")))
    return 0
