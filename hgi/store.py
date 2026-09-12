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
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, TypeVar

from pydantic import BaseModel

from hgi import registry as _registry
from hgi.registry import read_json, write_json
from hgi.types import (
    PREFIXES,
    RECORD_MODELS,
    Admission,
    ConstitutionArticle,
    Decision,
    Draft,
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


def now() -> datetime:
    return datetime.now(timezone.utc).astimezone()


def record_id(record: BaseModel) -> str:
    return getattr(record, "id", None) or getattr(record, "name")


def dump(record: BaseModel) -> dict[str, Any]:
    return record.model_dump(mode="json", by_alias=True)


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
        """Admit an adjudicated draft: mint the eternal id, stamp admission, write, flip the observations it promotes.

        The floor runs before this is called (``hgi.lint.check_draft``); the
        commit that lands the record is the caller's. Only ``admit`` and
        ``admit-amended`` reach here — the verdict is read off the ledger
        entry, never supplied by the proposer.
        """
        from hgi.registry import term_head

        if term_head(entry.verdict) not in ("admit", "admit-amended"):
            raise PermissionError(f"the committer admits only on admit or admit-amended, not {entry.verdict!r}")
        if entry.adjudicator is None:
            raise PermissionError("an entry with no adjudicator call carries no verdict the committer may act on")
        body = draft.body.model_dump(by_alias=True)
        if amendment:
            body.update(amendment)
        id = self.registry.mint(PREFIXES["decision"])
        stamp = now()
        decision = self.parse_as(Decision, {
            "id": id, "kind": "decision", "status": "accepted", "created_at": draft.drafted_at.isoformat(),
            "lineage": {"supersedes": [], "superseded_by": None, "split_from": None, "folded_from": []},
            "admission": {"proposed_by": draft.proposed_by, "ledger_entry": entry.id, "verdict": entry.verdict,
                          "adjudicator": adjudicator.model_dump(), "committed_at": stamp.isoformat()},
            **body,
        })
        self.write(decision)
        for ev in draft.evidence:
            obs = self._observation_by_uid_or_name(ev)
            if obs is not None and obs.disposition.state == "open":
                obs.disposition.state = "promoted"
                obs.disposition.pointer = id
                obs.disposition.at = stamp
                self.write(obs)
        self.drop_draft(draft.uid)
        return decision

    def flip_status(self, record: Decision, status: str, successor: str | None = None) -> Decision:
        """The only in-place change a frozen record receives. A supersedure names its successor."""
        data = dump(record)
        data["status"] = status
        if successor:
            data["lineage"]["superseded_by"] = successor
        flipped = self.parse_as(Decision, data)
        self.write(flipped)
        return flipped

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
