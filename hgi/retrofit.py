"""Retrofit: an old attached arm's store re-consolidated by today's backward pass, one pass at a time.

An arm consolidated with code that has since been fixed leaves a question:
what would its store have held at each iteration had the backward pass been
today's? ``hgi experiment retrofit <old arm> --out <new arm>`` answers it
without touching the original and without re-running the actor:

1. a fresh store is seeded with today's genesis (:mod:`hgi.genesis`) — so it
   carries today's vocabulary, lenses and bars — priced for the old arm's
   pass model, with the old arm's consolidation cadence copied from its
   ``registry/bars.json`` so consolidations fall where they fell;
2. the old store's attached sessions are walked in pass order. For pass *k*
   the recorded session ``S-k`` is **spliced** into the new store with its
   evaluation rows unchanged — the forward pass is the record, never
   replayed — the watch fires the new store's own latches owe on those
   scores are emitted (:func:`hgi.evaluate.emit_fires`, the oracle's
   mechanical half), and today's ``close`` runs on the session, so its
   dispositions, observations, steers and proposals are the fixed code's; at
   each cadence point today's ``consolidate`` runs with the backward-pass
   roles — consolidator, examiner, adjudicator, coder, reauthor — on the
   teacher model (``--teacher``; default :data:`DEFAULT_TEACHER`, which the
   role contracts are priced for). The close's own calls (the close lenses,
   the disposition, the proposal) run on the old arm's pass model, as the
   pass's reflection did;
3. every step commits inside the new arm's repository exactly as a live arm's
   does — one ``Splice`` commit standing for the boot and evaluate the
   record already holds, then ``Close``, then ``Consolidate`` — and
   ``snapshots/after-pass-<k>.json`` beside the store lists what the store
   held after each pass: decisions with status, open observations, fires,
   steers, proposals, what the close filed, what the consolidation did, and
   what the splice stripped;
4. ``arm.json`` carries a ``retrofit`` block — the source arm, the commit its
   store was read at, the code commit the retrofit ran from, the teacher,
   the date — and ``hgi experiment report``, ``evolution`` and the dashboard
   read the directory as an arm through :func:`hgi.experiment.from_dir`.

**What the splice strips.** The recorded session's references into the old
store — the records it consulted and considered through the index, the boot
lens answers naming them, the fires it saw — name records the new store
never admitted, so they are dropped and listed on the pass's snapshot; the
session enters with the constitution alone in context. The rows keep their
``applied`` ids untouched: those name the old store's records, and the new
store's decision counter starts past the old store's highest decision id, so
no new record can wear an id a row already names and be credited for what
the old record did. A retrofitted store's own decisions therefore begin at
``D-<old maximum + 1>``, and an id below that in any of its rows is the old
store's.

**The limit.** The stream is prequential: once a retrofitted consolidation
admits a record, the real following pass would have booted with it in
context and acted on it, and the recorded rows cannot reflect that. An arm
whose passes had nothing in context at first sight (the economy run) gives a
clean counterfactual of the backward pass alone — the same rows, today's
judgement of them; an arm where a real record was consulted later (the
stream run's ``D-0001`` from pass 7) does not: those rows were produced
under a record the new store does not hold, and are spliced in with that
context stripped. A retrofit reads the backward pass; it never measures the
forward one. ``hgi experiment compare`` (:func:`compare`) writes the
per-iteration reading of the retrofitted store beside the original's, pass
by pass, and names where they diverge.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

import suite as _suite
from hgi import boot as _boot
from hgi import evaluate as _evaluate
from hgi import experiment as _experiment
from hgi import index as _index
from hgi import model as _model
from hgi import registry as _registry
from hgi import tracing
from hgi.experiment import STUB, ModelSpec
from hgi.roles import ROLES
from hgi.store import Store, git
from hgi.types import Considered, Consolidation, Session
from suite.tasks import Suite, build

DEFAULT_TEACHER = "openai/gpt-oss-120b"
"""The model the backward-pass roles run on unless ``--teacher`` says otherwise: the one the role contracts are priced for."""

TEACHER_ROLES = tuple(r for r in ROLES if r != "pass")
"""Every role but the pass runs on the teacher: consolidator, examiner, adjudicator, coder, reauthor."""

EXPERIMENT = "retrofit"
"""The experiment name a retrofitted arm files under: ``runs/retrofit/<source experiment>-<source arm>/``."""

RESULTS = Path("experiments") / "results" / "retrofit"
"""Where :func:`compare` writes the readings unless told otherwise."""


# --- the source ------------------------------------------------------------------------------

def source_record(source: Path) -> dict[str, Any]:
    path = source / "arm.json"
    if not path.exists():
        raise SystemExit(f"{source} is not an arm directory: no arm.json")
    return json.loads(path.read_text())


def teacher_spec(teacher: str | None, source_experiment: str) -> ModelSpec:
    """The teacher: an alias of the source experiment's file when one declares it, else a model id on W&B Inference; ``stub`` is the stub."""
    teacher = teacher or DEFAULT_TEACHER
    if teacher == "stub":
        return STUB
    path = Path(__file__).resolve().parents[1] / "experiments" / f"{source_experiment}.toml"
    if path.exists():
        exp = _experiment.load(path)
        if teacher in exp.models:
            return exp.models[teacher]
    return ModelSpec(id=teacher)


def install(pass_model: str, teacher: ModelSpec) -> dict[str, str]:
    """The pass on the old arm's pass model, every other role on the teacher; return the roster."""
    _model.reset()
    _model.use(STUB.backend() if pass_model == "stub" else ModelSpec(id=pass_model).backend())
    backend = teacher.backend()
    for role in TEACHER_ROLES:
        _model.use(backend, role=role)
    return _model.roster()


def _max_id(store: Store, kind: str) -> int:
    return max((int(r.id.split("-")[1]) for r in store.all(kind)), default=0)  # type: ignore[attr-defined]


def seed_store(root: Path, pass_model: str, old_bars: dict[str, Any], spec: _experiment.ArmSpec, counters: dict[str, int]) -> _registry.Registry:
    """Today's genesis priced for the pass model, the old arm's cadence and bar overrides over its bars, and the id
    counters advanced past the old store's: the spliced sessions keep their ids, and no decision minted here can wear an
    id the rows already name."""
    from hgi.genesis import seed

    reg = seed(root, model_id=pass_model)
    bars = _experiment._merge(_experiment._merge(dict(reg.bars), {"consolidation_every_passes": old_bars["consolidation_every_passes"]}), spec.bars)
    _registry.write_json(root / "registry" / "bars.json", bars)
    ids = _registry.read_json(root / "registry" / "ids.json")
    _registry.write_json(root / "registry" / "ids.json", ids | {p: max(n, ids.get(p, 0)) for p, n in counters.items()})
    return _registry.load(root)


# --- the splice -------------------------------------------------------------------------------

def splice(store: Store, old: Session) -> dict[str, Any]:
    """Enter the recorded session into the store with its rows unchanged and its references into the old store stripped;
    emit the fires this store's latches owe on its scores. Returns what was stripped and what fired, for the snapshot."""
    if store.exists("session", old.id):
        raise SystemExit(f"{old.id} already exists in the retrofitted store")
    owed = [f["id"] for f in _index.undischarged_fires(store) if f["disposer"] == _boot.WORKING_PASS]
    session = Session(id=old.id, pass_=old.pass_, started_at=old.started_at, model_id=old.model_id, trace_root=old.trace_root,
                      work_shape=old.work_shape, fires_seen=list(owed), evaluation=old.evaluation, attached=True,
                      considered=[Considered(record=a.id, via="constitution", guard_passed=True, owed_act="apply") for a in store.articles()])
    store.write(session)
    fires = _evaluate.emit_fires(store, session)
    store.write(session)
    return {"consulted": [c.record for c in old.consulted], "considered": [c.record for c in old.considered if c.via != "constitution"],
            "fires_seen": list(old.fires_seen), "lens_answers": [a.lens for a in old.lens_answers],
            "original_close": {"observations_filed": list(old.observations_filed), "steers_filed": list(old.steers_filed),
                               "ledger_entries": list(old.ledger_entries), "proposals": len(old.proposals), "carry_forward": old.carry_forward},
            "fires_owed": owed, "fires_emitted": [f.id for f in fires]}


# --- snapshots --------------------------------------------------------------------------------

def by_shape(observations: list[Any]) -> dict[str, dict[str, Any]]:
    """The observation pile keyed by the shape the blind coder gave it (``uncoded`` until a consolidation has run): how many
    are open, promoted, dismissed or expired under each shape, and the open ones' names — the accumulation a
    consolidation groups over, read pass by pass."""
    out: dict[str, dict[str, Any]] = {}
    for o in observations:
        key = " ".join(o.shape) or "uncoded"
        cell = out.setdefault(key, {"open": 0, "promoted": 0, "dismissed": 0, "expired": 0, "sessions": set(), "names": []})
        cell[o.disposition.state] = cell.get(o.disposition.state, 0) + 1
        if o.disposition.state == "open":
            cell["sessions"].add(o.session)
            cell["names"].append(o.name)
    return {k: v | {"sessions": sorted(v["sessions"])} for k, v in sorted(out.items())}


def snapshot(store: Store) -> dict[str, Any]:
    """What a store holds: every decision with its status, the observations by state (the open ones in full) and by shape,
    every fire, steer and open proposal, the queue, the consolidations and the ledger by species."""
    observations = store.all("observation")
    return {
        "decisions": [{"id": d.id, "status": d.status, "hook": d.consultation_terms, "decision": d.decision, "proposed_by": d.admission.proposed_by,
                       "rung": d.admission.rung, "displaced_from": d.admission.displaced_from, "supersedes": list(d.lineage.supersedes),
                       "superseded_by": list(d.lineage.superseded_by), "anchors": list(d.warrant.anchors),
                       "premises": {p.id: p.status for p in d.warrant.premises}} for d in store.all("decision")],  # type: ignore[attr-defined]
        "observations": {"open": [{"name": o.name, "session": o.session, "shape": list(o.shape), "noticed": o.noticed}
                                  for o in observations if o.disposition.state == "open"],  # type: ignore[attr-defined]
                         "by_state": dict(Counter(o.disposition.state for o in observations)),  # type: ignore[attr-defined]
                         "by_shape": by_shape(observations)},
        "fires": [{"id": f.id, "record": f.latch.record, "index": f.latch.index, "pass": f.edge_event.pass_, "scorer": f.edge_event.scorer,
                   "observed": f.edge_event.observed, "disposer": f.disposer, "act": f.disposition.act, "discharged": f.disposition.discharged,
                   "by": f.disposition.by, "outcome": f.disposition.outcome} for f in store.all("fire")],  # type: ignore[attr-defined]
        "steers": [{"id": t.id, "kind": t.source.kind, "session": t.session, "record": t.indicts.record if t.indicts else None,
                    "slot": t.indicts.slot if t.indicts else None, "cell": t.matrix_cell, "correction": t.correction} for t in store.all("steer")],  # type: ignore[attr-defined]
        "proposals": [{"uid": d.uid, "name": d.name, "proposed_by": d.proposed_by, "rung": d.rung, "deferred": d.deferral is not None, "decision": d.body.decision}
                      for d in store.drafts()],
        "queue": [{"uid": q.draft.uid, "name": q.draft.name, "why": q.why} for q in store.queue()],
        "consolidations": [k.id for k in store.all("consolidation")],  # type: ignore[attr-defined]
        "ledger": dict(Counter(e.species for e in store.all("hypothesis"))),  # type: ignore[attr-defined]
    }


def consolidation_summary(k: Consolidation) -> dict[str, Any]:
    bar_groups = [{"shape": g.get("shape"), "sessions": g.get("sessions", []), "observations": g.get("observations", [])}
                  for g in k.brief.get("groups", []) if isinstance(g, dict)]
    return {"id": k.id, "after_pass": k.after_pass, "sessions_read": list(k.sessions_read), "admitted": list(k.admitted), "flipped": list(k.flipped),
            "deferred": list(k.deferred), "dismissed": list(k.dismissed), "expired": list(k.expired), "retired": list(k.retired), "anchored": list(k.anchored),
            "minted": list(k.minted), "fires_discharged": list(k.fires_discharged), "triage": list(k.brief.get("triage", [])), "groups": bar_groups,
            "nominations": [{"subject": n.subject, "rung": n.rung, "displaced_from": n.displaced_from, "adopts": n.adopts, "outcome": n.outcome} for n in k.nominations]}


def _score(session: Session) -> float | None:
    if session.evaluation is None or "task_pass_rate" not in session.evaluation.scores:
        return None
    return session.evaluation.scores["task_pass_rate"].value


def after_pass(store: Store, session_id: str, splice_notes: dict[str, Any] | None, consolidation: Consolidation | None) -> dict[str, Any]:
    """The state of one store after one pass: the session's score and context, what its close filed, what the
    consolidation after it did (when one ran), and the whole store."""
    s: Session = store.read("session", session_id)  # type: ignore[assignment]
    rows = s.evaluation.rows if s.evaluation else []
    return {"pass": s.pass_, "session": s.id, "score": _score(s), "rows": len(rows), "failed": [r["task"] for r in rows if not _index.row_passed(r)],
            "in_context": [c.record for c in s.consulted],
            "off_map": not s.consulted and any(r.get("error") for r in rows),
            "splice": splice_notes,
            "close": {"dispositions": [{"record": u.record, "disposition": u.disposition, "note": u.note} for u in store.all("disposition") if u.session == s.id],  # type: ignore[attr-defined]
                      "observations_filed": list(s.observations_filed), "steers_filed": list(s.steers_filed), "ledger_entries": list(s.ledger_entries),
                      "proposals": len(s.proposals), "carry_forward": s.carry_forward},
            "consolidation": consolidation_summary(consolidation) if consolidation is not None else None,
            "store": snapshot(store)}


def _consolidation_after(store: Store, pass_: int) -> Consolidation | None:
    return next((k for k in store.all("consolidation") if k.after_pass == pass_), None)  # type: ignore[attr-defined]


# --- the retrofit ---------------------------------------------------------------------------------

def retrofit(source: Path | str, out: Path | str, *, teacher: str | None = None, upto: int | None = None,
             commit: bool = True, force: bool = False) -> dict[str, Any]:
    """Retrofit the attached arm at ``source`` into the new arm directory ``out``; return its ``arm.json`` record."""
    from hgi import cli
    from hgi import evolution

    source = Path(source).resolve()
    src_record = source_record(source)
    spec = _experiment.spec_of(src_record)
    if spec.mode != "attached":
        raise SystemExit(f"{source} is a {spec.mode} arm; only an attached arm has a backward pass to retrofit")
    src_reg = _registry.load(source / "store")
    src_token = _registry.use(src_reg)
    try:
        src_store = Store(source / "store", registry=src_reg)
        old_sessions = _experiment._sessions(src_store, "attached")
        counters = {"D": _max_id(src_store, "decision"), "S": _max_id(src_store, "session")}
    finally:
        _registry.reset(src_token)
    if not old_sessions:
        raise SystemExit(f"{source} holds no evaluated attached session")
    source_commit = _experiment._tree_commit(source)

    out = Path(out).resolve()
    if out.exists():
        if not force:
            raise SystemExit(f"{out} exists; pass --force to redo the retrofit (its store is discarded)")
        shutil.rmtree(out)
    out.mkdir(parents=True)
    store_root = out / "store"
    if commit:
        git("init", "-q", cwd=out)

    os.environ["WEAVE_PARALLELISM"] = str(spec.concurrency)
    pass_model = src_record["roster"]["pass"]
    teacher_model = teacher_spec(teacher, src_record["experiment"])
    roster = install(pass_model, teacher_model)
    batches, warning = _experiment.recorded_batches(spec, src_record)
    world = batches[0] if batches else build(spec.suite)
    suite_token = _suite.use(world)
    reg = seed_store(store_root, pass_model, src_reg.bars, spec, counters)
    cadence = reg.bars["consolidation_every_passes"]
    token = _registry.use(reg)
    store = Store(store_root, registry=reg)
    arm = out.name
    record: dict[str, Any] = {
        "experiment": out.parent.name, "arm": arm, "spec": spec.model_dump(), "passes": spec.passes, "roster": roster,
        "suite": src_record.get("suite"), "stream": src_record.get("stream"), "seed": None,
        "weave_project": tracing.project_name(), "started_at": _experiment._now(), "finished_at": None, "sessions": [], "curve": {},
        "commit": _experiment._tree_commit(),
        "retrofit": {"source": str(source), "source_experiment": src_record["experiment"], "source_arm": src_record["arm"],
                     "source_commit": source_commit, "source_code_commit": src_record.get("commit"), "source_passes": [s.pass_ for s in old_sessions],
                     "teacher": teacher_model.id, "pass_model": pass_model, "code_commit": _experiment._tree_commit(), "date": _experiment._now(),
                     "upto": upto, "cadence": cadence, "id_counters": counters, "batches": warning},
    }
    _experiment._write(out / "arm.json", record)
    previous_store = os.environ.get("HGI_STORE")
    os.environ["HGI_STORE"] = str(store_root)
    tracing.run(record["experiment"], arm)
    argv = ["--store", str(store_root)] + ([] if commit else ["--no-commit"])
    short = (source_commit or "no commit")[:7]

    def hgi(*args: str) -> None:
        if cli.main([args[0], *argv, *args[1:]]) != 0:
            raise SystemExit(f"hgi {args[0]} failed in retrofit {arm}")

    batch_of = {int(k): v for k, v in (record["stream"] or {}).get("passes", {}).items()} if batches else {}

    def suite_for(n: int) -> Suite:
        """The suite pass ``n`` met: its batch of the stream (a revisited one past the stream), or the arm's one suite."""
        return batches[batch_of[n] - 1] if batches else world

    def progress() -> None:
        record["sessions"] = sorted(s.id for s in _experiment._sessions(store, "attached"))
        record["curve"] = _experiment.curve(store, "attached")
        _experiment._write(out / "arm.json", record)

    snapshots = out / "snapshots"
    snapshots.mkdir(exist_ok=True)
    try:
        ids = sorted(a.id for a in store.articles())
        _experiment._commit_arm(out, store, commit, f"Genesis for {record['experiment']}/{arm}: priced for {pass_model}, consolidating every {cadence}"
                                + (f", constitution {ids[0]}..{ids[-1]}" if len(ids) > 1 else "") + f"; retrofit of {src_record['experiment']}/{src_record['arm']} at {short}")
        for old in old_sessions:
            n = old.pass_
            if upto is not None and n > upto:
                break
            _suite.use(suite_for(n))
            notes = splice(store, old)
            _index.regenerate(store)
            stripped = " ".join(dict.fromkeys([*notes["consulted"], *notes["considered"], *notes["fires_seen"]]))
            _experiment._commit_arm(out, store, commit, f"Splice {old.id} pass {n} from {short}: rows unchanged"
                                    + (f", stripped {stripped}" if stripped else "") + (f", fired {' '.join(notes['fires_emitted'])}" if notes["fires_emitted"] else ""))
            hgi("close", "--session", old.id)
            if n <= spec.passes and n % cadence == 0:
                hgi("consolidate")
            snap = after_pass(store, old.id, notes, _consolidation_after(store, n))
            (snapshots / f"after-pass-{n}.json").write_text(json.dumps(snap, indent=2, sort_keys=True, default=str) + "\n")
            progress()
            _experiment._commit_arm(out, store, commit, f"Snapshot after pass {n}: {len(snap['store']['decisions'])} decisions, "
                                    f"{len(snap['store']['observations']['open'])} open observations, {len(snap['store']['fires'])} fires, {len(snap['store']['steers'])} steers")
        _suite.use(world)
        hgi("lint", "--model", pass_model)
    finally:
        record["finished_at"] = _experiment._now()
        _experiment._write(out / "arm.json", record)
        if batches:
            exp, root = _experiment.from_dir(out)
            evolution.write(exp, arm, root)
        _experiment._commit_arm(out, store, commit, f"Retrofit {record['experiment']}/{arm} finished: {_experiment._curve_line(record['curve'])}")
        tracing.run()
        _registry.reset(token)
        _suite.reset(suite_token)
        _model.reset()
        if previous_store is None:
            os.environ.pop("HGI_STORE", None)
        else:
            os.environ["HGI_STORE"] = previous_store
    return record


# --- the original, pass by pass, from its history ----------------------------------------------------

def _commits(arm_dir: Path) -> list[tuple[str, str]]:
    """Every commit over the arm's repository, oldest first, as ``(sha, subject)``."""
    log = git("log", "--reverse", "--format=%H%x1f%s", cwd=arm_dir)
    return [tuple(line.split("\x1f", 1)) for line in log.splitlines() if line]  # type: ignore[misc]


def commit_after_pass(arm_dir: Path, pass_: int) -> tuple[str, str] | None:
    """The commit that left the arm's store as it stood after pass ``k``: the consolidation after it when one ran, else its close."""
    close = kons = None
    for sha, subject in _commits(arm_dir):
        if re.match(rf"Close S-\d+ pass {pass_}(?!\d)", subject):
            close = (sha, subject)
        if re.match(rf"Consolidate K-\d+ after pass {pass_}(?!\d)", subject):
            kons = (sha, subject)
    return kons or close


def store_at(arm_dir: Path, sha: str, into: Path) -> Store:
    """The arm's store as one commit left it, extracted under ``into`` and read with its own registry."""
    archive = subprocess.run(["git", "-C", str(arm_dir), "archive", "--format=tar", sha, "store"], check=True, capture_output=True).stdout
    subprocess.run(["tar", "-x", "-C", str(into)], input=archive, check=True)
    root = into / "store"
    return Store(root, registry=_registry.load(root))


def original_after_pass(source: Path, pass_: int, into: Path) -> dict[str, Any] | None:
    """The original store as it stood after pass ``k``, in the shape :func:`after_pass` writes for the retrofit."""
    hit = commit_after_pass(source, pass_)
    if hit is None:
        return None
    sha, subject = hit
    where = into / f"pass-{pass_}"
    where.mkdir(parents=True, exist_ok=True)
    store = store_at(source, sha, where)
    token = _registry.use(store.registry)
    try:
        session = next((s for s in _experiment._sessions(store, "attached") if s.pass_ == pass_), None)
        if session is None:
            return None
        snap = after_pass(store, session.id, None, _consolidation_after(store, pass_))
    finally:
        _registry.reset(token)
    return snap | {"commit": sha[:7], "subject": subject}


# --- the reading --------------------------------------------------------------------------------------

def _outcomes(k: dict[str, Any] | None) -> Counter:
    return Counter((n["outcome"] or "pending").split("(")[0].split(";")[0].strip() for n in (k or {}).get("nominations", [])
                   if not str(n["subject"]).startswith(("C-", "L-")))


def divergences(o: dict[str, Any] | None, r: dict[str, Any]) -> list[str]:
    """Where the two stores part after one pass, and why, read mechanically off the two snapshots."""
    k = r["pass"]
    out = []
    if o is None:
        return [f"pass {k}: the original's history holds no commit after this pass; nothing to read beside"]
    if o["in_context"] and not r["in_context"]:
        disposed = ", ".join(f"{u['record']} {u['disposition']}" for u in o["close"]["dispositions"] if u["record"] in o["in_context"]) or "nothing disposed"
        out.append(f"pass {k}: the original booted with {' '.join(o['in_context'])} in context ({disposed}); the retrofit spliced the same rows with nothing "
                   "in context, so its rows were produced under a record its store does not hold"
                   + (" and its close read the failed rows as off-map" if r["off_map"] else ""))
    fo, fr = len(o["close"]["observations_filed"]), len(r["close"]["observations_filed"])
    if fo != fr:
        out.append(f"pass {k}: the close filed {fo} observation{'s' if fo != 1 else ''} originally and {fr} retrofitted — the close lenses are today's "
                   "(L-0004 per failed row, L-0009 on recovered misses, L-0010 off-map) on the same rows")
    po, pr = o["close"]["proposals"], r["close"]["proposals"]
    if po != pr:
        out.append(f"pass {k}: the pass proposed {po} draft{'s' if po != 1 else ''} originally and {pr} retrofitted")
    eo, er = {f["id"] for f in o["store"]["fires"] if f["pass"] == k}, {f["id"] for f in r["store"]["fires"] if f["pass"] == k}
    if bool(eo) != bool(er):
        out.append(f"pass {k}: fires on this pass's scores — original {' '.join(sorted(eo)) or 'none'}, retrofit {' '.join(sorted(er)) or 'none'}: "
                   "a watch fires only where a record with a live revisit latch stands, and the two stores hold different records")
    ko, kr = o["consolidation"], r["consolidation"]
    if ko or kr:
        if (ko or {}).get("admitted", []) != (kr or {}).get("admitted", []):
            out.append(f"after pass {k}: the original {ko['id'] if ko else 'consolidated nothing'} admitted {' '.join(ko['admitted']) if ko and ko['admitted'] else 'nothing'}; "
                       f"the retrofit {kr['id'] if kr else 'consolidated nothing'} admitted {' '.join(kr['admitted']) if kr and kr['admitted'] else 'nothing'}")
        oo, orr = _outcomes(ko), _outcomes(kr)
        if oo != orr:
            out.append(f"after pass {k}: nomination outcomes — original {dict(oo) or 'none'}; retrofit {dict(orr) or 'none'}")
        if kr and kr["dismissed"]:
            out.append(f"after pass {k}: the retrofit's noise filter dismissed {' '.join(kr['dismissed'])} as irreducible" + ("; the original had no filter" if ko and not ko["dismissed"] else ""))
        if (ko or {}).get("flipped") != (kr or {}).get("flipped"):
            out.append(f"after pass {k}: flipped — original {' '.join((ko or {}).get('flipped', [])) or 'nothing'}, retrofit {' '.join((kr or {}).get('flipped', [])) or 'nothing'}")
        if (ko or {}).get("retired") != (kr or {}).get("retired"):
            out.append(f"after pass {k}: lenses retired — original {' '.join((ko or {}).get('retired', [])) or 'none'}, retrofit {' '.join((kr or {}).get('retired', [])) or 'none'}")
    so, sr = len(o["store"]["steers"]), len(r["store"]["steers"])
    if so != sr:
        out.append(f"pass {k}: {so} steer{'s' if so != 1 else ''} on the original store, {sr} on the retrofit")
    return out


def reading(retro: Path) -> dict[str, Any]:
    """The per-iteration reading of one retrofitted arm beside its source, from the retrofit's snapshots and the source's history."""
    retro = Path(retro).resolve()
    record = source_record(retro)
    meta = record.get("retrofit")
    if not meta:
        raise SystemExit(f"{retro} is not a retrofitted arm: its arm.json carries no retrofit block")
    source = Path(meta["source"])
    passes = []
    with tempfile.TemporaryDirectory(prefix="hgi-retrofit-") as tmp:
        for path in sorted(retro.glob("snapshots/after-pass-*.json"), key=lambda p: int(p.stem.rsplit("-", 1)[1])):
            r = json.loads(path.read_text())
            o = original_after_pass(source, r["pass"], Path(tmp)) if (source / "arm.json").exists() else None
            passes.append({"pass": r["pass"], "original": o, "retrofit": r, "divergence": divergences(o, r)})
    last_o = next((p["original"] for p in reversed(passes) if p["original"]), None)
    last_r = passes[-1]["retrofit"] if passes else None
    return {"arm": record["arm"], "retrofit": meta, "curve": record["curve"], "passes": passes,
            "final": {"original": last_o["store"] if last_o else None, "retrofit": last_r["store"] if last_r else None}}


def _decision_line(d: dict[str, Any]) -> str:
    return f"{d['id']} [{d['status']}] on {' '.join(d['hook']) or 'no hook'}" + (f" (displaced from {d['displaced_from']})" if d.get("displaced_from") else "") + f": {d['decision']}"


def _admitted_after(passes: list[dict[str, Any]], side: str) -> dict[str, int]:
    return {rid: p["pass"] for p in passes if (k := (p[side] or {}).get("consolidation")) for rid in k["admitted"]}


def reading_markdown(r: dict[str, Any]) -> str:
    meta = r["retrofit"]
    lines = [f"# {r['arm']} — the retrofitted store beside the original, pass by pass", "",
             f"Source `{meta['source_experiment']}/{meta['source_arm']}` (store at `{str(meta.get('source_commit') or '?')[:7]}`), retrofitted on {meta['date'][:10]} "
             f"from the code at `{str(meta.get('code_commit') or '?')[:7]}`: the rows are the source arm's, unchanged; the close runs on `{meta['pass_model']}`, "
             f"the backward pass on `{meta['teacher']}`; consolidation every {meta['cadence']} passes. The retrofit's decisions begin at "
             f"D-{meta['id_counters']['D'] + 1:04d}; any lower decision id is the original's. Nothing was in context at any retrofitted pass: the "
             "stream is prequential, and a pass the original booted with a record in context produced its rows under that record.", "",
             "## After each pass", "",
             "`o` is the original store after the pass (its consolidation included where one ran), `r` the retrofitted one.", "",
             "| pass | score | in context (o) | filed o / r | open obs o / r | accepted o / r | fires o / r | steers o / r | consolidation (o) | consolidation (r) |",
             "|---|---|---|---|---|---|---|---|---|---|"]

    def kcell(k):
        if not k:
            return ""
        oc = _outcomes(k)
        return (f"{k['id']}: admitted {' '.join(k['admitted']) or 'nothing'}" + (f"; flipped {' '.join(k['flipped'])}" if k["flipped"] else "")
                + (f"; {', '.join(f'{v} {o}' for o, v in sorted(oc.items()))}" if oc else "; nothing nominated")
                + (f"; dismissed {len(k['dismissed'])}" if k["dismissed"] else "") + (f"; retired {' '.join(k['retired'])}" if k["retired"] else ""))

    def accepted(s):
        return sum(d["status"] == "accepted" for d in s["store"]["decisions"])

    def fires(s):
        return f"{sum(not f['discharged'] for f in s['store']['fires'])} open of {len(s['store']['fires'])}"

    for p in r["passes"]:
        o, rr = p["original"], p["retrofit"]
        score = "—" if rr["score"] is None else f"{rr['score']:.2f}"
        oc = lambda f, default="—": f(o) if o else default  # noqa: E731
        lines.append(f"| {p['pass']} | {score} | {oc(lambda s: ' '.join(s['in_context']) or 'none')} | "
                     f"{oc(lambda s: len(s['close']['observations_filed']))} / {len(rr['close']['observations_filed'])} | "
                     f"{oc(lambda s: len(s['store']['observations']['open']))} / {len(rr['store']['observations']['open'])} | "
                     f"{oc(accepted)} / {accepted(rr)} | {oc(fires)} / {fires(rr)} | {oc(lambda s: len(s['store']['steers']))} / {len(rr['store']['steers'])} | "
                     f"{oc(lambda s: kcell(s['consolidation']), '')} | {kcell(rr['consolidation'])} |")
    lines += ["", "## Decisions", ""]
    for side, label in (("original", "Original"), ("retrofit", "Retrofit")):
        final = r["final"][side]
        lines.append(f"**{label}.** " + ("Nothing admitted." if not final or not final["decisions"] else ""))
        after = _admitted_after(r["passes"], side)
        for d in (final or {}).get("decisions", []):
            lines.append(f"- {_decision_line(d)} — after pass {after.get(d['id'], '?')}")
        lines.append("")
    lines += ["## Observations by shape, pass by pass", "",
              "Open observations under each shape after each pass, original / retrofit; a shape is the blind coder's at the next "
              "consolidation, so a pile is `uncoded` until one has run. The bar asks for observations from as many distinct sessions "
              "as `independent_observations`; the last column is each side's final pile with what was promoted or dismissed.", ""]
    shapes = sorted({k for p in r["passes"] for side in ("original", "retrofit") if p[side] for k in p[side]["store"]["observations"].get("by_shape", {})})
    if shapes:
        lines.append("| shape | " + " | ".join(f"p{p['pass']}" for p in r["passes"]) + " | end o / r (open; promoted; dismissed) |")
        lines.append("|---|" + "---|" * (len(r["passes"]) + 1))
        for shape in shapes:
            cells = []
            for p in r["passes"]:
                o_ = ((p["original"] or {}).get("store", {}).get("observations", {}).get("by_shape", {}) or {}).get(shape)
                r_ = p["retrofit"]["store"]["observations"].get("by_shape", {}).get(shape)
                cells.append(f"{o_['open'] if o_ else ('—' if p['original'] is None else 0)} / {r_['open'] if r_ else 0}")
            ends = []
            for side in ("original", "retrofit"):
                c = ((r["final"][side] or {}).get("observations", {}).get("by_shape", {}) or {}).get(shape)
                ends.append(f"{c['open']}; {c['promoted']}; {c['dismissed']}" if c else "0; 0; 0")
            lines.append(f"| {shape} | " + " | ".join(cells) + f" | {ends[0]} / {ends[1]} |")
    else:
        lines.append("No observation was filed on either side.")
    lines += ["", "## Where they diverge, and why", ""]
    any_div = False
    for p in r["passes"]:
        for line in p["divergence"]:
            any_div = True
            lines.append(f"- {line}")
    if not any_div:
        lines.append("The two stores agree after every pass.")
    lines += ["", "## What the retrofit's passes stripped", ""]
    stripped = [(p["pass"], p["retrofit"]["splice"]) for p in r["passes"] if p["retrofit"].get("splice")]
    rows = [(k, s) for k, s in stripped if s["consulted"] or s["considered"] or s["fires_seen"]]
    if rows:
        lines.append("| pass | consulted | considered via the index | fires seen | original close filed |")
        lines.append("|---|---|---|---|---|")
        for k, s in rows:
            oc_ = s["original_close"]
            lines.append(f"| {k} | {' '.join(s['consulted']) or '—'} | {' '.join(s['considered']) or '—'} | {' '.join(s['fires_seen']) or '—'} | "
                         f"{len(oc_['observations_filed'])} obs, {oc_['proposals']} prop |")
    else:
        lines.append("No pass of the original consulted a record or saw a fire: every row was produced with nothing in context, and the "
                     "retrofit is a clean counterfactual of the backward pass alone.")
    lines += ["", "## Reading", "",
              "The forward pass is the record and was not replayed: every score above is the original actor's, and a retrofitted "
              "consolidation that admits a record cannot change the rows that follow it. Where the original consulted a record, the rows "
              "after that point were produced under it and the retrofit reads them as if nothing had been in context — the divergence "
              "is then partly the actor's and not the backward pass's. Every count is from one run of each backward pass and is a floor."]
    return "\n".join(lines) + "\n"


def compare(dirs: list[Path | str], out: Path | None = None) -> str:
    """Write the reading of each retrofitted arm (``<arm>.json`` and ``<arm>.md``) under ``out`` and an index ``report.md`` over them; return the index."""
    out = Path(out) if out else RESULTS
    out.mkdir(parents=True, exist_ok=True)
    readings = []
    for d in dirs:
        r = reading(Path(d))
        (out / f"{r['arm']}.json").write_text(json.dumps(r, indent=2, sort_keys=True, default=str) + "\n")
        (out / f"{r['arm']}.md").write_text(reading_markdown(r))
        readings.append(r)
    lines = ["# retrofit — old attached arms re-consolidated by today's backward pass, pass by pass", "",
             "Each arm's rows are its original run's, unchanged; the close and the consolidations are today's code. "
             "`o` is the original store, `r` the retrofit; decisions count those accepted at the end.", "",
             "| arm | passes | teacher | admitted (o) | admitted (r) | accepted at end o / r | open observations o / r | dismissed (r) | fires o / r | divergences |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for r in readings:
        fo, fr = r["final"]["original"], r["final"]["retrofit"]
        ao = " ".join(_admitted_after(r["passes"], "original")) or "nothing"
        ar = " ".join(_admitted_after(r["passes"], "retrofit")) or "nothing"
        dismissed = sum(len(k["dismissed"]) for p in r["passes"] if (k := p["retrofit"].get("consolidation")))
        lines.append(f"| [{r['arm']}]({r['arm']}.md) | {len(r['passes'])} | {r['retrofit']['teacher']} | {ao} | {ar} | "
                     f"{sum(d['status'] == 'accepted' for d in fo['decisions']) if fo else '—'} / {sum(d['status'] == 'accepted' for d in fr['decisions']) if fr else '—'} | "
                     f"{len(fo['observations']['open']) if fo else '—'} / {len(fr['observations']['open']) if fr else '—'} | {dismissed} | "
                     f"{len(fo['fires']) if fo else '—'} / {len(fr['fires']) if fr else '—'} | {sum(len(p['divergence']) for p in r['passes'])} |")
    text = "\n".join(lines) + "\n"
    (out / "report.md").write_text(text)
    return text
