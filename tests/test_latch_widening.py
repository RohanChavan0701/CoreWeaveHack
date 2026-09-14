"""Carry-forward item 50 — a hook-edit that widens a record's consultation latch onto a term (essentially) every task in
the pool carries is refused: the record would fire on every task and mean nothing. Only a genuine widening onto a
pool-universal term is refused; a narrowing, or a broadening onto a term the whole pool does not carry, stands."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

import suite as _suite
from hgi import consolidate as _consolidate
from tests.conftest import adjudicated_entry, adjudicator, draft


def _pool(monkeypatch, *task_shapes):
    fake = SimpleNamespace(tasks=[SimpleNamespace(shapes=tuple(s)) for s in task_shapes])
    monkeypatch.setattr(_suite, "current", lambda: fake)


def _admit(store, terms):
    latches = [
        {"type": "consultation", "slot": "payload", "key_space": "work-shape", "edge": {"kind": "level", "at": "boot"},
         "guard": {"terms": list(terms), "not_this": []}, "consumer": "the working pass",
         "owed_act": {"class": "apply", "role": "dispositive"}, "lifecycle": {"status": "live"}},
    ]
    d = draft(store, "D-0001", latches=latches)
    entry = adjudicated_entry(store, d.uid)
    entry.verdict = "admit"
    return store.admit(d, entry, adjudicator())


def test_pool_universal_terms(monkeypatch):
    _pool(monkeypatch, ("shell-tool", "tool-budget", "output-schema"),
                       ("shell-tool", "tool-budget", "http-tool"),
                       ("shell-tool", "tool-budget", "file-tool"))
    assert _consolidate.pool_universal_terms() == {"shell-tool", "tool-budget"}


def test_a_single_task_pool_has_no_universal_term(monkeypatch):
    _pool(monkeypatch, ("shell-tool", "tool-budget"))
    assert _consolidate.pool_universal_terms() == set()


def test_a_hook_edit_widening_onto_a_pool_universal_term_is_refused(store, monkeypatch):
    _pool(monkeypatch, ("shell-tool", "tool-budget", "output-schema"),
                       ("shell-tool", "tool-budget", "http-tool"),
                       ("shell-tool", "tool-budget", "file-tool"))
    d = _admit(store, ["output-schema"])
    raw = {"rung": "hook-edit", "supersedes": [d.id], "edit": {"terms": ["output-schema", "shell-tool", "tool-budget"]}}
    with pytest.raises(ValueError, match="pool-universal"):
        _consolidate.edited_body(store, raw)


def test_a_sensible_broadening_onto_a_non_universal_term_is_admitted(store, monkeypatch):
    _pool(monkeypatch, ("shell-tool", "tool-budget", "output-schema"),
                       ("shell-tool", "tool-budget", "http-tool"),
                       ("shell-tool", "tool-budget", "file-tool"))
    d = _admit(store, ["output-schema"])
    raw = {"rung": "hook-edit", "supersedes": [d.id], "edit": {"terms": ["output-schema", "http-tool"]}}
    body = _consolidate.edited_body(store, raw)
    terms = [t for latch in body["latches"] if latch["type"] == "consultation" for t in latch["guard"]["terms"]]
    assert set(terms) == {"output-schema", "http-tool"}


def test_a_narrowing_hook_edit_is_admitted(store, monkeypatch):
    _pool(monkeypatch, ("shell-tool", "tool-budget", "output-schema"),
                       ("shell-tool", "tool-budget", "http-tool"))
    # the record already carries a universal term; narrowing it away is fine — only adding a universal term is refused
    d = _admit(store, ["shell-tool", "output-schema"])
    raw = {"rung": "hook-edit", "supersedes": [d.id], "edit": {"terms": ["output-schema"]}}
    body = _consolidate.edited_body(store, raw)
    terms = [t for latch in body["latches"] if latch["type"] == "consultation" for t in latch["guard"]["terms"]]
    assert terms == ["output-schema"]


def test_keeping_a_universal_term_already_present_is_not_a_widening(store, monkeypatch):
    _pool(monkeypatch, ("shell-tool", "tool-budget", "output-schema"),
                       ("shell-tool", "tool-budget", "http-tool"))
    d = _admit(store, ["shell-tool", "output-schema"])
    # shell-tool was already there (not newly widened onto); adding a non-universal term is fine
    raw = {"rung": "hook-edit", "supersedes": [d.id], "edit": {"terms": ["shell-tool", "output-schema", "http-tool"]}}
    body = _consolidate.edited_body(store, raw)
    terms = {t for latch in body["latches"] if latch["type"] == "consultation" for t in latch["guard"]["terms"]}
    assert terms == {"shell-tool", "output-schema", "http-tool"}
