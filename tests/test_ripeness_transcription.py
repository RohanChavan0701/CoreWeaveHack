"""Item 58 — variance-driven ripeness (lever A) and price-zero transcription (lever B).

Lever A is pure projection: it populates the two frozen Cut-C slots per cluster (``world_content_variance`` over the
members' settled ``happened`` tokens, ``presentation_universality`` over their shared work-shape terms), scores each
cluster's ripeness ``independence × (1 − wcv) × (1 − pu)``, and floats the ripe clusters (low variance, non-universal,
multi-session) to the head of the brief — the machine ranks and annotates, it never authors a sketch (I2). The
universality factor is the refusal that keeps a high-independence-but-universal cluster (the item-56 budget trap) from
reading ripe. Both levers are floored below the independence bar so a small pile fabricates no signal.

Lever B transcribes the price-zero happenstance floor — a ``happened`` that is mechanically evaluable (it quotes a
literal or states a comparison) — to a ``Fact`` with no adjudication, and surfaces every ambiguous ``happened`` to the
human instead. ``turned_on`` (the inference) is never transcribed."""

from __future__ import annotations

from hgi import consolidate as _consolidate
from hgi.types import Consolidation, Fact
from hgi.store import now
from tests.test_slice3 import CLEAN, FAULTED, NO_CAUSE, _observe, _session


# --- lever A: the two Cut-C measures ---------------------------------------------------------

def test_world_content_variance_is_categorical_over_happened_tokens():
    # every member names the same quoted world-content literal -> one recurrent token -> zero spread (ripe)
    assert _consolidate.world_content_variance(["status is coded 'A'", "the value is 'A' again"]) == 0.0
    # distinct quoted literals -> maximal spread over two members
    assert _consolidate.world_content_variance(["column is 'A'", "column is 'B'"]) == 0.5
    # no quoted literal: the normalized whole sentence is the token; two identical -> zero
    assert _consolidate.world_content_variance(["a plain sentence", "a plain sentence"]) == 0.0
    # 1 - modal fraction: three members, two share the modal token
    v = _consolidate.world_content_variance(["'x'", "'x'", "'y'"])
    assert abs(v - (1 - 2 / 3)) < 1e-9
    assert _consolidate.world_content_variance([]) == 0.0


def test_presentation_universality_fraction_of_shared_terms_that_are_pool_universal(monkeypatch):
    members = [{"anchor": {"call": "c1"}}, {"anchor": {"call": "c2"}}]
    call_shapes = {"c1": {"http-tool", "error-wrapping"}, "c2": {"http-tool"}}  # shared = {http-tool}
    monkeypatch.setattr(_consolidate, "pool_universal_terms", lambda *a, **k: {"http-tool"})
    assert _consolidate.presentation_universality(members, call_shapes) == 1.0  # the shared presentation is entirely universal
    monkeypatch.setattr(_consolidate, "pool_universal_terms", lambda *a, **k: set())
    assert _consolidate.presentation_universality(members, call_shapes) == 0.0  # nothing universal
    assert _consolidate.presentation_universality(members, {}) == 0.0  # no resolvable presentation at all


def test_ripeness_formula_and_the_universality_refusal():
    assert _consolidate.ripeness(3, 0.0, 0.0) == 3.0
    # a high-independence but presentation-universal cluster is refused: the item-56 false-ripeness trap
    assert _consolidate.ripeness(10, 0.0, 1.0) == 0.0
    # world-content spread pulls ripeness down proportionally
    assert _consolidate.ripeness(4, 0.5, 0.0) == 2.0


def test_rank_groups_floats_ripe_first_populates_slots_and_floors_small_piles(store):
    ripe = {"convention": "other(a)", "shape": ["other(a)"], "independence": 3, "sessions": ["S-1", "S-2", "S-3"],
            "world_content_variance": None, "presentation_universality": None,
            "observations": [{"name": "O-1", "session": "S-1", "happened": "value is 'A'", "anchor": {"path": "x"}},
                             {"name": "O-2", "session": "S-2", "happened": "value is 'A'", "anchor": {"path": "y"}},
                             {"name": "O-3", "session": "S-3", "happened": "value is 'A'", "anchor": {"path": "z"}}]}
    scattered = {"convention": "other(b)", "shape": ["other(b)"], "independence": 2, "sessions": ["S-4", "S-5"],
                 "world_content_variance": None, "presentation_universality": None,
                 "observations": [{"name": "O-4", "session": "S-4", "happened": "value is 'A'", "anchor": {"path": "p"}},
                                  {"name": "O-5", "session": "S-5", "happened": "value is 'Z'", "anchor": {"path": "q"}}]}
    below = {"convention": "other(c)", "shape": ["other(c)"], "independence": 1, "sessions": ["S-6"],
             "world_content_variance": None, "presentation_universality": None,
             "observations": [{"name": "O-6", "session": "S-6", "happened": "value is 'A'", "anchor": {"path": "r"}}]}
    ordered = _consolidate.rank_groups(store, [scattered, below, ripe])
    # ripe (var 0, indep 3) before scattered (var 0.5, indep 2); the below-floor pile last with ripeness None
    assert [g["convention"] for g in ordered] == ["other(a)", "other(b)", "other(c)"]
    assert ordered[0]["ripeness"] == 3.0 and ordered[0]["world_content_variance"] == 0.0
    assert ordered[1]["ripeness"] == 1.0  # 2 * (1 - 0.5)
    assert ordered[2]["ripeness"] is None, "a single-session pile is left unranked, not fabricated"


def test_the_brief_orders_groups_by_ripeness_and_annotates_them(store):
    s1 = _session(store, 1, [FAULTED], {"task_pass_rate": 0.5, "error_cause_present": 0.0})
    s2 = _session(store, 2, [FAULTED], {"task_pass_rate": 0.5, "error_cause_present": 0.0})
    _observe(store, s1, NO_CAUSE), _observe(store, s2, NO_CAUSE)
    record = Consolidation(id=store.mint("consolidation"), started_at=now(), after_pass=2, sessions_read=[s1.id, s2.id])
    brief = _consolidate.build_brief(store, record, [s1, s2])
    assert brief["groups"], "the two same-shape observations grouped"
    g = brief["groups"][0]
    assert g["world_content_variance"] == 0.0 and "presentation_universality" in g
    assert g["ripeness"] == 2.0, "two independent sessions, one recurrent world-content token, non-universal presentation"


# --- lever B: price-zero transcription -------------------------------------------------------

def test_transcription_writes_mechanical_happened_and_surfaces_the_ambiguous(store):
    brief = {"groups": [{"observations": [
        {"name": "O-1", "happened": "the status is stored as 'A' not 'approved'", "turned_on": "coded literals",
         "anchor": {"call": "weave:///c/1"}},
        {"name": "O-2", "happened": "the retry silently swallowed the cause", "turned_on": "the count uses COUNT(*)",
         "anchor": {"call": "weave:///c/2"}}]}], "unelicited": []}
    transcribed, surfaced = _consolidate.transcribe_happenstance(store, brief)
    assert len(transcribed) == 1 and isinstance(transcribed[0], Fact)
    fact = transcribed[0]
    assert fact.series.startswith("happenstance/") and "'A'" in fact.series and fact.value == 1.0
    assert fact.source == "weave:///c/1"
    # the ambiguous happened is surfaced to the human, not written; its `turned_on` (which names 'COUNT(*)') is never read
    assert [s["origin"] for s in surfaced] == ["O-2"]
    assert not any("COUNT" in f.series for f in transcribed), "turned_on is never transcribed"


def test_transcription_dedups_and_reads_unelicited_markers(store):
    brief = {"groups": [{"observations": [
        {"name": "O-1", "happened": "column 'order' must be quoted", "anchor": {"call": "c1"}},
        {"name": "O-2", "happened": "column 'order' must be quoted", "anchor": {"call": "c1"}}]}],
        "unelicited": [{"happened": "route '/v2' returned 404", "anchor": {"call": "c9"}, "ledger_entry": "H-9"},
                       {"happened": "task sum_numbers failed and elicited no convention", "anchor": {}, "ledger_entry": "H-8"}]}
    transcribed, surfaced = _consolidate.transcribe_happenstance(store, brief)
    # the duplicate (same happened + call) collapses; the unelicited marker with a quoted literal transcribes
    series = sorted(f.series for f in transcribed)
    assert len(transcribed) == 2 and any("'order'" in s for s in series) and any("/v2" in s for s in series)
    # the marker naming no checkable token is surfaced, never auto-written
    assert [s["origin"] for s in surfaced] == ["H-8"]


def test_consolidate_records_the_transcription_on_the_pass(store):
    s1 = _session(store, 1, [FAULTED], {"task_pass_rate": 0.5, "error_cause_present": 0.0})
    s2 = _session(store, 2, [FAULTED], {"task_pass_rate": 0.5, "error_cause_present": 0.0})
    _observe(store, s1, "the reserved column 'order' was not quoted"), _observe(store, s2, "the reserved column 'order' was not quoted")
    record = _consolidate.consolidate(store)
    assert record.transcribed and all(isinstance(f, Fact) for f in record.transcribed)
    assert any("'order'" in f.series for f in record.transcribed)
    assert "transcription" in record.brief and "surfaced" in record.brief["transcription"]
    # the pass record round-trips through the store with the typed facts intact
    reread = store.read("consolidation", record.id)
    assert [f.series for f in reread.transcribed] == [f.series for f in record.transcribed]
