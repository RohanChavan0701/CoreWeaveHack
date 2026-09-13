"""The trace store binding: ``rejoin`` re-opens the configured project from inside a thread ``init``
never ran in (item 34) — a no-op when tracing is off, a fresh ``weave.init`` when it is on."""

from __future__ import annotations

from hgi import tracing


def test_rejoin_is_a_noop_when_no_project_is_configured(monkeypatch):
    monkeypatch.delenv("HGI_WEAVE_PROJECT", raising=False)
    calls = []
    monkeypatch.setattr(tracing.weave, "init", lambda name: calls.append(name))
    tracing.rejoin()
    assert calls == []


def test_rejoin_reopens_the_configured_project(monkeypatch):
    monkeypatch.setenv("HGI_WEAVE_PROJECT", "hgi-experiments")
    monkeypatch.setenv("WANDB_ENTITY", "someone")
    calls = []
    monkeypatch.setattr(tracing.weave, "init", lambda name: calls.append(name))
    tracing.rejoin()
    assert calls == ["someone/hgi-experiments"]
