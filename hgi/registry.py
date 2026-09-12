"""The registry: closed vocabularies, port declarations, bars, the constitution
cap, the lens register and the id counters.

The registry is a *register* — a current-state surface corrected in place,
with git carrying its history. Every closed vocabulary ships the escape
``other(<what>)``; a value outside a vocabulary without the escape is refused
at parse time by the validators in :mod:`hgi.types`, which read the registry
through :func:`current`.

Files under ``<store>/registry/``:

- ``vocabulary.json``   ``{vocab: {"means": …, "terms": {term: {"means": …, "since": …}}}}``
- ``ports.json``        ``{kind: {status: {latch_type: "required"|"optional"|"forbidden"}}}``
- ``bars.json``         promotion bars and the review window (spec § 10.4)
- ``constitution.json`` ``{"max_articles": n, "max_bytes": n}``
- ``lenses.json``       the lens register, a list of lens records
- ``ids.json``          ``{prefix: last_issued}`` — the monotone counters
"""

from __future__ import annotations

import json
import os
import re
from contextvars import ContextVar
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ESCAPE = re.compile(r"^other\((.+)\)$")
"""Every closed vocabulary admits ``other(<what>)``; the group is the ``what``."""

_PARAMETRIC = re.compile(r"^([a-z-]+)\(<[^>]+>\)$")
"""A term of the form ``name(<param>)`` matches any value ``name(…)``."""


def is_escape(value: str) -> bool:
    return bool(ESCAPE.match(value))


def term_matches(term: str, value: str) -> bool:
    """Whether ``value`` instantiates the registered ``term``.

    A plain term matches only itself. A parametric term such as
    ``decline(<why>)`` matches ``decline(anything non-empty)``.
    """
    if term == value:
        return True
    m = _PARAMETRIC.match(term)
    if m:
        return bool(re.match(rf"^{re.escape(m.group(1))}\(.+\)$", value))
    return False


def term_head(value: str) -> str:
    """``decline(too weak)`` → ``decline``; a plain term is its own head."""
    return value.split("(", 1)[0]


@dataclass
class Vocabulary:
    name: str
    means: str
    terms: dict[str, dict[str, Any]]

    def check(self, value: str) -> str:
        """Return ``value`` if it is a registered term or an escape; raise otherwise."""
        if is_escape(value):
            return value
        if any(term_matches(t, value) for t in self.terms):
            return value
        raise ValueError(
            f"{value!r} is not in the closed vocabulary {self.name!r} "
            f"({', '.join(self.terms)}) and is not an other(<what>) escape"
        )


@dataclass
class Registry:
    root: Path
    vocabularies: dict[str, Vocabulary]
    ports: dict[str, dict[str, dict[str, str]]]
    bars: dict[str, Any]
    constitution_cap: dict[str, int]
    ids: dict[str, int] = field(default_factory=dict)

    # --- paths ---------------------------------------------------------
    @property
    def dir(self) -> Path:
        return self.root / "registry"

    def path(self, name: str) -> Path:
        return self.dir / f"{name}.json"

    # --- vocabulary ----------------------------------------------------
    def vocab(self, name: str) -> Vocabulary:
        try:
            return self.vocabularies[name]
        except KeyError:
            raise KeyError(f"no closed vocabulary named {name!r} in {self.path('vocabulary')}") from None

    def check(self, vocab: str, value: str) -> str:
        return self.vocab(vocab).check(value)

    def terms(self, vocab: str) -> list[str]:
        return list(self.vocab(vocab).terms)

    def add_term(self, vocab: str, term: str, means: str, since: str) -> None:
        """Grow a vocabulary — the route-before-mint ladder's last rung for a term."""
        self.vocab(vocab).terms[term] = {"means": means, "since": since}
        self.save("vocabulary")

    # --- ports ---------------------------------------------------------
    def port(self, kind: str, status: str, latch_type: str) -> str:
        """The obligation mark for a latch type on a kind at a status; ``optional`` when undeclared."""
        return self.ports.get(kind, {}).get(status, {}).get(latch_type, "optional")

    # --- ids -----------------------------------------------------------
    def mint(self, prefix: str) -> str:
        """Reserve the next id for ``prefix`` and persist the counter. Ids are reserve-once and gap-tolerant."""
        n = self.ids.get(prefix, 0) + 1
        self.ids[prefix] = n
        self.save("ids")
        return f"{prefix}-{n:04d}"

    # --- persistence ---------------------------------------------------
    def save(self, name: str) -> None:
        payload: Any
        if name == "vocabulary":
            payload = {
                v.name: {"means": v.means, "terms": v.terms} for v in self.vocabularies.values()
            }
        elif name == "ports":
            payload = self.ports
        elif name == "bars":
            payload = self.bars
        elif name == "constitution":
            payload = self.constitution_cap
        elif name == "ids":
            payload = self.ids
        else:
            raise KeyError(name)
        write_json(self.path(name), payload)

    def lenses(self, host: str | None = None) -> list[Any]:
        """The lens register as typed :class:`hgi.types.Lens` records, optionally filtered by host."""
        from hgi.types import Lens  # lazy: types validates against this registry

        raw = read_json(self.path("lenses"))
        lenses = [Lens.model_validate(item, context={"registry": self}) for item in raw]
        return [l for l in lenses if host is None or l.host == host]


# --- loading ---------------------------------------------------------------

def read_json(path: Path) -> Any:
    with path.open() as f:
        return json.load(f)


def write_json(path: Path, payload: Any) -> None:
    """Write canonical JSON: sorted keys, two-space indent, trailing newline — so regeneration is byte-stable."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(payload, f, indent=2, sort_keys=True, ensure_ascii=False)
        f.write("\n")


def load(root: Path | str) -> Registry:
    root = Path(root)
    reg_dir = root / "registry"
    raw_vocab = read_json(reg_dir / "vocabulary.json")
    vocabularies = {
        name: Vocabulary(name=name, means=v.get("means", ""), terms=v["terms"])
        for name, v in raw_vocab.items()
    }
    ids_path = reg_dir / "ids.json"
    return Registry(
        root=root,
        vocabularies=vocabularies,
        ports=read_json(reg_dir / "ports.json"),
        bars=read_json(reg_dir / "bars.json"),
        constitution_cap=read_json(reg_dir / "constitution.json"),
        ids=read_json(ids_path) if ids_path.exists() else {},
    )


# --- the registry in scope ---------------------------------------------------

_current: ContextVar[Registry | None] = ContextVar("hgi_registry", default=None)


def default_root() -> Path:
    """The store root: ``$HGI_STORE`` or ``./store``."""
    return Path(os.environ.get("HGI_STORE", "store"))


def current() -> Registry:
    """The registry the validators consult when a parse supplies no explicit context."""
    reg = _current.get()
    if reg is None:
        reg = load(default_root())
        _current.set(reg)
    return reg


def use(registry: Registry | None):
    """Make ``registry`` the one in scope for this context (a token to reset with :func:`reset`)."""
    return _current.set(registry)


def reset(token) -> None:
    _current.reset(token)
