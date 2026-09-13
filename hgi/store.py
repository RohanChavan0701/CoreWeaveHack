"""Read and write for every store; id minting; the committer; the pre-admission tier.

The write law (spec § 7): one canonical source per record; every index a
regenerated projection; ids reserve-once, immutable, gap-tolerant;
retirements tombstone with successor pointers; refinement is a successor
record or a status flip, never a rewrite of evidence.

Layouts, from :data:`LAYOUTS`: ``file`` stores are one JSON file per record
named by id; ``jsonl`` stores are one append-only file per kind. Observations
and fires are files because each receives exactly one in-place flip (the
observation's disposition on promotion, the fire's disposition on
discharge); everything else that is a ledger is JSON Lines.
"""

from __future__ import annotations

import json
import re
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, TypeVar

from pydantic import BaseModel

from hgi import registry as _registry
from hgi.registry import read_json, write_json
from hgi.types import (
    ID_PATTERN,
    PREFIXES,
    RECORD_MODELS,
    Admission,
    ConstitutionArticle,
    Decision,
    Deferral,
    Draft,
    Envelope,
    LedgerEntry,
    Observation,
    QueueEntry,
    RoleCall,
)

M = TypeVar("M", bound=BaseModel)

LAYOUTS: dict[str, tuple[str, str]] = {
    "constitution": ("constitution", "file"),
    "decision": ("decisions", "file"),
    "observation": ("observations", "file"),
    "fire": ("fires", "file"),
    "session": ("sessions", "file"),
    "consolidation": ("consolidations", "file"),
    "hypothesis": ("ledger", "jsonl"),
    "disposition": ("dispositions", "jsonl"),
    "steer": ("steers", "jsonl"),
}
"""kind → (directory, layout)."""

ETERNAL_KINDS = ("constitution", "decision")
"""Kinds whose ids only the committer mints."""
ETERNAL_PREFIXES = {PREFIXES[k] for k in ETERNAL_KINDS}


def now() -> datetime:
    return datetime.now(timezone.utc).astimezone()


def record_id(record: BaseModel) -> str:
    return getattr(record, "id", None) or getattr(record, "name")


def dump(record: BaseModel) -> dict[str, Any]:
    return record.model_dump(mode="json", by_alias=True)


def wiring_latch(records: list[str], store: "Store", act: str = "check") -> dict[str, Any]:
    """A neighbour-keyed latch on ``records``: the edge is any of them changing status, the consumer is propagation.

    The guard remembers each neighbour's status as of the write, so the edge is
    a departure from what was seen — the latch stays immutable and the fire
    ledger carries every later observation.
    """
    seen = {}
    for rid in records:
        neighbour = store.find(rid)
        if neighbour is not None:
            seen[rid] = neighbour.status  # type: ignore[attr-defined]
    return {"type": "wiring", "slot": "lifecycle", "key_space": "neighbor", "edge": {"kind": "edge"},
            "guard": {"records": list(records), "statuses": seen}, "consumer": "propagation",
            "owed_act": {"class": act, "role": "corroborating"}, "lifecycle": {"status": "live"}}


class Store:
    def __init__(self, root: Path | str | None = None, registry: _registry.Registry | None = None):
        self.root = Path(root) if root else _registry.default_root()
        self.registry = registry or _registry.load(self.root)

    # --- paths --------------------------------------------------------------
    def dir(self, kind: str) -> Path:
        return self.root / LAYOUTS[kind][0]

    def path(self, kind: str, id: str) -> Path:
        directory, layout = LAYOUTS[kind]
        return self.root / directory / (f"{id}.json" if layout == "file" else f"{directory}.jsonl")

    @property
    def proposals_dir(self) -> Path:
        return self.root / "proposals"

    @property
    def queue_dir(self) -> Path:
        return self.root / "queue"

    @property
    def index_dir(self) -> Path:
        return self.root / "index"

    # --- parsing ------------------------------------------------------------
    def parse(self, kind: str, data: dict[str, Any]) -> BaseModel:
        return RECORD_MODELS[kind].model_validate(data, context={"registry": self.registry})

    def parse_as(self, model: type[M], data: dict[str, Any]) -> M:
        return model.model_validate(data, context={"registry": self.registry})

    # --- reads --------------------------------------------------------------
    def read(self, kind: str, id: str) -> BaseModel:
        return self.parse(kind, read_json(self.path(kind, id)))

    def all(self, kind: str) -> list[BaseModel]:
        """Every record of a kind, in id order. A jsonl kind yields its lines in append order."""
        directory, layout = LAYOUTS[kind]
        if layout == "jsonl":
            return list(self._ledger(kind))
        return [self.parse(kind, read_json(p)) for p in sorted(self.dir(kind).glob("*.json"))]

    def _ledger(self, kind: str) -> Iterator[BaseModel]:
        path = self.path(kind, "")
        if not path.exists():
            return
        with path.open() as f:
            for line in f:
                if line.strip():
                    yield self.parse(kind, json.loads(line))

    def exists(self, kind: str, id: str) -> bool:
        return self.path(kind, id).exists()

    def decisions(self, *statuses: str) -> list[Decision]:
        return [d for d in self.all("decision") if not statuses or d.status in statuses]

    def articles(self) -> list[ConstitutionArticle]:
        return [a for a in self.all("constitution") if a.status == "live"]

    def observations(self, state: str | None = "open") -> list[Observation]:
        return [o for o in self.all("observation") if state is None or o.disposition.state == state]

    def conditioning(self) -> list[tuple[str, Any]]:
        """Every live record carrying authored conditioning text, as ``(kind, record)``.

        A lens's angle, an article and a decision's sentence are read by the
        model as conditioning, so each records the model it was priced for
        (spec § 6, § 9.6) and a model swap re-prices all of them. This is the
        set :mod:`hgi.price` re-prices and ``model-pricing`` checks.
        """
        return ([("lens", l) for l in self.registry.lenses()]
                + [("constitution", a) for a in self.articles()]
                + [("decision", d) for d in self.decisions("accepted")])

    def find(self, id: str) -> BaseModel | None:
        """Any record by id, across every file-layout kind."""
        for kind, (_, layout) in LAYOUTS.items():
            if layout == "file" and self.exists(kind, id):
                return self.read(kind, id)
        return None

    # --- writes -------------------------------------------------------------
    def write(self, record: BaseModel) -> Path:
        """Write a file-layout record in canonical JSON. Refuses to create an eternal record outside the committer."""
        kind = record.kind  # type: ignore[attr-defined]
        directory, layout = LAYOUTS[kind]
        if layout != "file":
            raise ValueError(f"{kind} is a ledger; use append()")
        path = self.path(kind, record_id(record))
        write_json(path, dump(record))
        return path

    def append(self, record: BaseModel) -> Path:
        """Append one line to a ledger. A ledger line is frozen at admission."""
        kind = record.kind  # type: ignore[attr-defined]
        path = self.path(kind, "")
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a") as f:
            f.write(json.dumps(dump(record), sort_keys=True, ensure_ascii=False) + "\n")
        return path

    def mint(self, kind: str) -> str:
        """Reserve the next id for a kind. Eternal kinds are minted only through :meth:`admit`."""
        if kind in ETERNAL_KINDS:
            raise PermissionError(f"{kind} ids are minted by the committer at admission")
        return self.registry.mint(PREFIXES[kind])

    # --- the pre-admission tier ---------------------------------------------
    def new_uid(self) -> str:
        return str(uuid.uuid7()) if hasattr(uuid, "uuid7") else str(uuid.uuid4())

    def next_name(self, prefix: str) -> str:
        """A recyclable human-facing name — the highest name in use plus one, never a reserved counter."""
        used = [int(p.stem.split("-")[1]) for p in self.dir("observation").glob(f"{prefix}-*.json")] if prefix == "O" else []
        used += [int(p.stem.split("-")[1]) for p in self.proposals_dir.glob(f"{prefix}-*.json")]
        return f"{prefix}-{(max(used) + 1 if used else 1):04d}"

    def write_draft(self, draft: Draft) -> Path:
        path = self.proposals_dir / f"{draft.uid}.json"
        write_json(path, dump(draft))
        return path

    def drafts(self) -> list[Draft]:
        return [self.parse_as(Draft, read_json(p)) for p in sorted(self.proposals_dir.glob("*.json"))]

    def draft(self, uid: str) -> Draft | None:
        path = self.proposals_dir / f"{uid}.json"
        return self.parse_as(Draft, read_json(path)) if path.exists() else None

    def host(self, id: str) -> BaseModel | None:
        """Whatever carries the latch a fire names: a decision or article by id, or a deferred draft by uid."""
        return self.find(id) or self.draft(id)

    def defer(self, draft: Draft, entry: LedgerEntry, until: Latch, after_pass: int) -> Draft:
        """The committer's act on ``defer(<until>)``: the condition becomes a latch on the draft, which stays in the pre-admission tier."""
        deferred = draft.model_copy(update={"deferral": Deferral(ledger_entry=entry.id, until=until, deferred_at=now(), after_pass=after_pass)})
        self.write_draft(deferred)
        return deferred

    def drop_draft(self, uid: str) -> None:
        """A declined draft is dropped without a tombstone: a vertex with no in-edges breaks no path."""
        (self.proposals_dir / f"{uid}.json").unlink(missing_ok=True)

    def queue(self) -> list[QueueEntry]:
        return [self.parse_as(QueueEntry, read_json(p)) for p in sorted(self.queue_dir.glob("*.json"))]

    def enqueue(self, entry: QueueEntry) -> Path:
        path = self.queue_dir / f"{entry.draft.uid}.json"
        write_json(path, dump(entry))
        return path

    def dequeue(self, uid: str) -> None:
        (self.queue_dir / f"{uid}.json").unlink(missing_ok=True)

    # --- the committer ------------------------------------------------------
    def admit(self, draft: Draft, entry: LedgerEntry, adjudicator: RoleCall, amendment: dict[str, Any] | None = None) -> Decision:
        """Admit an adjudicated draft: mint the eternal id, stamp admission, write, retire what it supersedes, flip the observations it promotes.

        The floor runs before this is called (``hgi.lint.check_draft``); the
        commit that lands the record is the caller's. Only ``admit`` and
        ``admit-amended`` reach here — the verdict is read off the ledger
        entry, never supplied by the proposer.

        The lineage operators of § 10.6 are executed here and nowhere else: a
        draft that ``supersedes``, is a leaf ``split_from`` a fused record, or
        is ``folded_from`` several records lands with its own edges written
        and every retiree flipped to ``superseded`` with the reciprocal
        pointer — one commit, one DAG move.
        """
        from hgi.registry import term_head

        if term_head(entry.verdict) not in ("admit", "admit-amended"):
            raise PermissionError(f"the committer admits only on admit or admit-amended, not {entry.verdict!r}")
        if entry.adjudicator is None:
            raise PermissionError("an entry with no adjudicator call carries no verdict the committer may act on")
        for rid in draft.retires:
            if not self.exists("decision", rid):
                raise ValueError(f"{draft.name} retires {rid}, which is not a decision in this store")
        body = draft.body.model_dump(by_alias=True)
        if amendment:
            body.update(amendment)
        neighbours = [a for a in body["warrant"]["anchors"] if a not in draft.retires and isinstance(self.find(a), Envelope)]
        if neighbours:  # a warrant that cites a record is wired to it: its status change is this record's edge
            body["latches"].append(wiring_latch(neighbours, self, act="check"))
        id = self.registry.mint(PREFIXES["decision"])
        stamp = now()
        decision = self.parse_as(Decision, {
            "id": id, "kind": "decision", "status": "accepted", "created_at": draft.drafted_at.isoformat(),
            "lineage": {"supersedes": list(draft.supersedes), "superseded_by": [], "split_from": draft.split_from, "folded_from": list(draft.folded_from)},
            "admission": {"proposed_by": draft.proposed_by, "ledger_entry": entry.id, "verdict": entry.verdict,
                          "adjudicator": adjudicator.model_dump(), "committed_at": stamp.isoformat()},
            **body,
        })
        self.write(decision)
        for pred in draft.retires:
            self.flip_status(self.read("decision", pred), "superseded", successor=id)  # type: ignore[arg-type]
        for ev in draft.evidence:
            obs = self._observation_by_uid_or_name(ev)
            if obs is not None and obs.disposition.state == "open":
                obs.disposition.state = "promoted"
                obs.disposition.pointer = id
                obs.disposition.at = stamp
                self.write(obs)
        self.drop_draft(draft.uid)
        return decision

    def license(self, by: str) -> str:
        """What may settle a frozen record, and the refusal when ``by`` is not it.

        A settlement — a status flip, a premise flip, a latch settled — cites
        what licensed it: an admitted successor record, a ledger entry that
        carries an adjudicator's verdict, or a fire whose latch is
        **dispositive**. A fire on a corroborating latch bears and never
        settles: its verdict lands on the ledger as a nomination and the
        settlement cites the entry, not the fire. A consolidation, a session
        or a bare name is no licence — nothing settles by count or by
        schedule alone.
        """
        kind = by.split("-", 1)[0] if ID_PATTERN.match(by) else None
        if kind == "F":
            fire = self.read("fire", by) if self.exists("fire", by) else None
            if fire is None:
                raise PermissionError(f"{by} is not a fire in this store")
            host = self.host(fire.latch.record)  # type: ignore[union-attr]
            latches = host.all_latches() if host is not None else []  # type: ignore[union-attr]
            latch = latches[fire.latch.index] if fire.latch.index < len(latches) else None  # type: ignore[union-attr]
            if latch is None:
                raise PermissionError(f"{by} names a latch that no longer exists")
            if latch.owed_act.role != "dispositive":
                raise PermissionError(f"{by} fired a {latch.owed_act.role} latch, which nominates and never settles; cite the adjudicated ledger entry instead")
            return f"dispositive fire {by}"
        if kind == "H":
            entry = next((e for e in self.all("hypothesis") if e.id == by), None)  # type: ignore[attr-defined]
            if entry is None:
                raise PermissionError(f"{by} is not on the ledger")
            if entry.verdict == "pending" or entry.adjudicator is None:  # type: ignore[attr-defined]
                raise PermissionError(f"{by} carries no adjudicated verdict; a pending entry settles nothing")
            return f"adjudicated entry {by}"
        if kind in ETERNAL_PREFIXES and self.find(by) is not None:
            return f"successor {by}"
        raise PermissionError(f"{by!r} licenses no settlement: cite an adjudicated ledger entry, a dispositive fire, or the admitted successor")

    def flip_status(self, record: Decision, status: str, successor: str | None = None, by: str | None = None) -> Decision:
        """The only in-place change a frozen record receives, licensed by :meth:`license`.

        A retiring flip (``superseded`` | ``moot``) settles every live latch of
        the record's own fan in the same write — a settled latch is kept as
        evidence, never removed, and names its licence. A supersedure names
        its successor: the pointer is appended (a split's parent collects one
        per heir) and a wiring latch keyed on the successor is added, so
        propagation can check the tombstone when the successor itself changes
        status. Wiring latches are the one type a flip leaves live: they are
        the edges propagation walks after the flip, not the fan the flip
        retires.
        """
        licence = successor or by
        if not licence:
            raise PermissionError("a status flip cites what licensed it")
        self.license(licence)
        data = dump(record)
        data["status"] = status
        stamp = now().isoformat()
        if status in ("superseded", "moot"):
            for latch in [*data["latches"], data["lifecycle"]["retirement"]]:
                if latch["lifecycle"]["status"] == "live" and latch["type"] != "wiring":
                    latch["lifecycle"] = {"status": "settled", "settled_at": stamp, "settled_by": licence}
        if successor:
            if successor not in data["lineage"]["superseded_by"]:
                data["lineage"]["superseded_by"].append(successor)
            data["latches"].append(wiring_latch([successor], self, act="check"))
        flipped = self.parse_as(Decision, data)
        self.write(flipped)
        return flipped

    def flip_premises(self, record: Decision, status: str, premise: str | None = None, *, by: str) -> Decision:
        """The one in-place flip a warrant takes: a premise's status, licensed by :meth:`license`. One premise by id, or every premise when none is named."""
        self.license(by)
        data = dump(record)
        hit = False
        for p in data["warrant"]["premises"]:
            if premise is None or p["id"] == premise:
                p["status"] = status
                hit = True
        if not hit:
            raise ValueError(f"{record.id} has no premise {premise!r}")
        flipped = self.parse_as(Decision, data)
        self.write(flipped)
        return flipped

    def anchor_article(self, article: ConstitutionArticle, anchor: str) -> ConstitutionArticle:
        """The one in-place change a genesis warrant takes: an anchor the adjudicator ratified, appended. ``evidence`` stays ``genesis``."""
        anchored = article.model_copy(update={"warrant": article.warrant.model_copy(update={"anchors": [*article.warrant.anchors, anchor]})})
        self.write(anchored)
        return anchored

    def evict_article(self, article: ConstitutionArticle) -> ConstitutionArticle:
        """Displace an article under the cap: a status flip to ``evicted`` — superseded, never deleted."""
        evicted = article.model_copy(update={"status": "evicted"})
        self.write(evicted)
        return evicted

    def _observation_by_uid_or_name(self, key: str) -> Observation | None:
        for o in self.all("observation"):
            if o.uid == key or o.name == key:
                return o
        return None

    def observation(self, key: str) -> Observation | None:
        return self._observation_by_uid_or_name(key)


# --- git: admission is a commit ----------------------------------------------

def git(*args: str, cwd: Path | None = None) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def commit(store: Store, message: str) -> str | None:
    """Stage the store and commit; return the short hash, or ``None`` when the tree was clean or is not a repository."""
    try:
        top = git("rev-parse", "--show-toplevel", cwd=store.root)
    except subprocess.CalledProcessError:
        return None
    git("add", "-A", str(store.root.resolve()), cwd=Path(top))
    if not git("status", "--porcelain", "--", str(store.root.resolve()), cwd=Path(top)):
        return None
    git("commit", "-q", "-m", message, cwd=Path(top))
    return git("rev-parse", "--short", "HEAD", cwd=Path(top))


ID_OR_RANGE = re.compile(r"\b([A-Z])-(\d{4})(?:\.\.([A-Z])-(\d{4}))?(?!\d)")
"""An id in a commit subject, or a range of them of the form ``C-0001..C-0007``."""


def ids_named(subject: str) -> set[str]:
    """Every record id a commit subject names. A range names each id it spans, which is how genesis names its articles."""
    out: set[str] = set()
    for prefix, first, last_prefix, last in ID_OR_RANGE.findall(subject):
        if last and last_prefix == prefix:
            out |= {f"{prefix}-{n:04d}" for n in range(int(first), int(last) + 1)}
        else:
            out.add(f"{prefix}-{first}")
    return out


def commits_naming(store: Store, id: str) -> list[dict[str, str]]:
    """Every commit over the store whose message names ``id``, newest first; empty outside a repository."""
    try:
        top = git("rev-parse", "--show-toplevel", cwd=store.root)
    except (subprocess.CalledProcessError, FileNotFoundError, NotADirectoryError):
        return []
    log = git("log", f"--grep={id.split('-')[0]}-", "--format=%h%x1f%as%x1f%s", "--",
              str(store.root.resolve()), cwd=Path(top))
    rows = (line.split("\x1f", 2) for line in log.splitlines())
    return [{"sha": sha, "date": date, "subject": subject}
            for sha, date, subject in rows if id in ids_named(subject)]


def admitting_commit(store: Store, id: str) -> dict[str, str] | None:
    """The commit that admitted ``id`` — the oldest one naming it — or ``None`` when nothing has committed it.

    ``admission.commit`` is not a stored field, because a commit cannot contain
    its own hash. The anchor is git history instead, which the commit messages
    make legible by naming every id they admit, flip or retire. History is
    append-only and no message names a record before the commit that wrote it,
    so the oldest naming is the admission.
    """
    naming = commits_naming(store, id)
    return naming[-1] if naming else None
