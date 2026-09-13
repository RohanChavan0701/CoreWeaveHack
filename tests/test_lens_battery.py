"""The lens battery (§ 9.2, slice 6a): decoy rejection scored in Weave, telemetry populated off ``design-stage``.

Offline the ``pass`` role is the stub, which files nothing for L-0003 and files a noticing for L-0004's genuine
signals; the battery scores exactly that and writes the computed telemetry onto the lens register.
"""

from __future__ import annotations

import json

from hgi import drafting as _drafting
from hgi import index as _index
from hgi import lens_battery as lb
from hgi import lint as _lint
from hgi import model as _model
from hgi import steers as _steers
from hgi.store import Store, now
from hgi.types import Draft, LensTelemetry, Session


# --- the filing rule and the scorers -----------------------------------------------------------

def test_a_finding_files_only_when_it_cites_something():
    assert lb.is_filed({"record": "D-0007"})
    assert lb.is_filed({"anchor": {"call": "weave:///c/1"}})
    assert lb.is_filed({"noticed": "x", "anchor": {"path": "suite/tools.py:54"}})
    assert not lb.is_filed({"noticed": "invented, no id"})
    assert not lb.is_filed({"anchor": {}})
    assert not lb.filed_any([])
    assert lb.filed_any([{"noticed": "y"}, {"record": "D-0001"}])


def test_decoy_rejection_scores_the_plant_only():
    s = lb.DecoyRejection()
    assert s.score(output={"filed": False}, is_decoy=True) == {"value": 1.0}
    assert s.score(output={"filed": True}, is_decoy=True) == {"value": 0.0}
    unevaluable = s.score(output={"filed": True}, is_decoy=False)
    assert unevaluable["value"] is None and unevaluable["unevaluable"]


def test_signal_caught_scores_the_genuine_signal_only():
    s = lb.SignalCaught()
    assert s.score(output={"filed": True}, is_decoy=False) == {"value": 1.0}
    assert s.score(output={"filed": False}, is_decoy=False) == {"value": 0.0}
    assert s.score(output={"filed": True}, is_decoy=True)["value"] is None


# --- the dataset -------------------------------------------------------------------------------

def test_the_battery_plants_a_balance_of_decoys_and_signals_per_close_lens(store):
    lenses = store.registry.lenses("close")
    rows = lb.dataset_rows(lenses)
    assert {l.id for l in lenses} == {"L-0003", "L-0004"}
    for lens_id in ("L-0003", "L-0004"):
        of_lens = [r for r in rows if r["lens"] == lens_id]
        assert sum(r["is_decoy"] for r in of_lens) == 2
        assert sum(not r["is_decoy"] for r in of_lens) == 2
        assert all(r["lens_spec"]["id"] == lens_id for r in of_lens)  # predict reads the spec off the row


# --- the run -----------------------------------------------------------------------------------

def test_the_battery_scores_decoy_rejection_and_computes_telemetry(store):
    result = lb.run_battery(store)

    # every close lens rejects every planted decoy on the honest stub answerer
    for lens_id in ("L-0003", "L-0004"):
        assert result.telemetry[lens_id].decoy_rejection.startswith("1.00")
    # L-0004 discriminates (rejects decoys, catches signals) so its filings vary; L-0003 files nothing, so no spread
    assert result.telemetry["L-0004"].answer_variance.startswith("0.25")
    assert result.telemetry["L-0003"].answer_variance.startswith("0.00")
    # the telemetry is off design-stage and carries the battery's name as provenance
    for t in result.telemetry.values():
        assert "design-stage" not in t.decoy_rejection and "design-stage" not in t.answer_variance
        assert lb.LENS_BATTERY in t.decoy_rejection

    # the scorer facts are a series named <evaluation>/<scorer>, landed with the run as source
    assert set(result.facts) == {"decoy_rejection", "signal_caught"}
    assert result.facts["decoy_rejection"].series == f"{lb.LENS_BATTERY}/decoy_rejection"
    assert result.facts["decoy_rejection"].value == 1.0  # 4/4 decoys rejected across both lenses
    assert result.facts["signal_caught"].value == 0.5     # L-0004 catches both, L-0003 misses both


def test_the_battery_attaches_signal_caught_per_lens(store):
    result = lb.run_battery(store)

    # the per-lens signal-caught cell is populated off design-stage and carries the battery's name as provenance
    for lens_id in ("L-0003", "L-0004"):
        assert "design-stage" not in result.telemetry[lens_id].signal_caught
        assert lb.LENS_BATTERY in result.telemetry[lens_id].signal_caught
    # L-0004 files its noticing on both genuine signals; L-0003's honest stub files nothing, so it misses every signal
    assert result.telemetry["L-0004"].signal_caught.startswith("1.00")
    assert result.telemetry["L-0003"].signal_caught.startswith("0.00")
    # a lens missing its signals reads a fraction strictly below one — the partial signal-miss the decoy axis alone hides
    fraction = float(result.telemetry["L-0003"].signal_caught.split(" ", 1)[0])
    assert fraction < 1.0


def test_the_signal_caught_cell_lands_on_the_lens_register(store):
    result = lb.run_battery(store)
    lb.populate_telemetry(store, result.telemetry)
    telemetry = {l.id: l.telemetry for l in Store(store.root).registry.lenses()}
    assert telemetry["L-0004"].signal_caught.startswith("1.00")
    assert telemetry["L-0003"].signal_caught.startswith("0.00")
    assert telemetry["L-0001"].signal_caught == "design-stage"  # boot lenses untouched


def test_boot_lenses_are_not_battered(store):
    result = lb.run_battery(store)
    assert set(result.telemetry) == {"L-0003", "L-0004"}  # L-0001/L-0002 are boot lenses, no decoy dataset


def test_the_emission_runs_on_the_offline_tracing_path(store):
    # with no HGI_WEAVE_PROJECT the evaluation still runs; the run URI reads None, never a crash, and the facts are computed
    result = lb.run_battery(store)
    assert result.run is None
    assert result.outputs and len(result.outputs) == 8
    assert all(f.as_of is not None for f in result.facts.values())


# --- persistence -------------------------------------------------------------------------------

def test_populate_moves_the_lens_register_off_design_stage(store):
    before = {l.id: l.telemetry.decoy_rejection for l in store.registry.lenses()}
    assert before["L-0003"] == "design-stage" and before["L-0001"] == "design-stage"

    result = lb.run_battery(store)
    updated = lb.populate_telemetry(store, result.telemetry)
    assert set(updated) == {"L-0003", "L-0004"}

    reloaded = Store(store.root)  # read the register back from disk
    telemetry = {l.id: l.telemetry for l in reloaded.registry.lenses()}
    assert telemetry["L-0003"].decoy_rejection.startswith("1.00")
    assert telemetry["L-0004"].answer_variance.startswith("0.25")
    assert telemetry["L-0001"].decoy_rejection == "design-stage"  # boot lenses untouched
    assert isinstance(telemetry["L-0003"], LensTelemetry)


def test_populate_wires_the_miss_stream_from_a_citing_steer(store, monkeypatch):
    # a human note naming a lens becomes a steer that cites it
    s = Session(id="S-0001", pass_=1, started_at=now())
    monkeypatch.setattr(_steers, "notes_for", lambda session: [{"call": "weave:///t/call/1", "note": "L-0004 missed the uncaused failure its angle should catch"}])
    [steer] = _steers.capture(store, s)
    assert steer.indicts.record == "L-0004"

    result = lb.run_battery(store)
    lb.populate_telemetry(store, result.telemetry)
    telemetry = {l.id: l.telemetry for l in Store(store.root).registry.lenses()}
    # the cited lens reads the steer in its miss stream, off the static literal; a battered lens no steer cites reads none
    assert "1 steer cites this lens" in telemetry["L-0004"].miss_stream and steer.id in telemetry["L-0004"].miss_stream
    assert telemetry["L-0003"].miss_stream == f"no steer cites this lens ({lb.LENS_BATTERY})"


def test_the_populated_store_stays_lint_green(store):
    result = lb.run_battery(store)
    lb.populate_telemetry(store, result.telemetry)
    reloaded = Store(store.root)
    _index.regenerate(reloaded)
    assert _lint.run(reloaded).green


# --- the seeded-positive controls ---------------------------------------------------------------

def test_the_examiner_control_plants_a_fault_and_a_clean_draft_per_examiner_lens(store):
    lenses = store.registry.lenses("examiner")
    rows = lb.examiner_rows(store, lenses)
    assert [l.id for l in lenses] == ["L-0006", "L-0007"] and len(rows) == 4
    for lens in lenses:
        of_lens = [r for r in rows if r["lens"] == lens.id]
        assert [r["kind"] for r in of_lens] == ["decoy", "signal"]
        assert all(store.parse_as(Draft, r["draft"]) for r in of_lens), "every plant is a draft the floor would read"
    by_item = {r["item"]: r for r in rows}
    assert "transient" in by_item["L-0006/signal/1"]["draft"]["body"]["warrant"]["premises"][0]["statement"]
    assert "sum_numbers" in by_item["L-0007/signal/1"]["draft"]["body"]["decision"]
    assert lb.EXAMINER_FAULTS.keys() == {l.id for l in lenses}, "a class the code reads has no plant"


def test_the_examiner_control_scores_each_angle_in_its_own_context_through_the_stubs_own_rules(store, monkeypatch):
    seen = []
    real = _model.complete

    def spy(role, payload, **kw):
        seen.append((role, json.loads(payload)))
        return real(role, payload, **kw)

    monkeypatch.setattr(_model, "complete", spy)
    result = lb.run_examiner_control(store)
    attacks = [(role, req["lens"]["id"]) for role, req in seen if req.get("request") == "attack"]
    # the evaluation walks its rows concurrently, so the order is the multiset's: one angle per context, one context per plant
    assert sorted(attacks) == [("examiner", l) for l in ("L-0006", "L-0006", "L-0007", "L-0007")]
    assert set(result.telemetry) == {"L-0006", "L-0007"}
    for t in result.telemetry.values():
        assert t.decoy_rejection.startswith("1.00") and t.answer_variance.startswith("0.25")  # lands on the fault, not on the clean draft
    assert result.facts["signal_caught"].value == 1.0 and result.facts["decoy_rejection"].value == 1.0
    assert all(any(c["landed"] for c in o["claims"]) == (o["kind"] == "signal") for o in result.outputs)


def test_the_examiner_control_lands_on_the_lens_register_and_leaves_the_boot_lenses_alone(store):
    updated = lb.populate_telemetry(store, lb.run_examiner_control(store).telemetry)
    assert set(updated) == {"L-0006", "L-0007"}
    telemetry = {l.id: l.telemetry for l in Store(store.root).registry.lenses()}
    assert telemetry["L-0006"].decoy_rejection.startswith("1.00") and telemetry["L-0001"].decoy_rejection == "design-stage"
    assert lb.run_battery(store).telemetry.keys() == {"L-0003", "L-0004"}, "the close-lens battery is unchanged by the control"


def test_the_coder_control_scores_the_term_and_the_escape_and_writes_controls_json(store):
    payload = lb.run_coder_control(store)
    coder = payload[lb.CODER]
    assert coder["signal_caught"].startswith("1.00") and coder["decoy_rejection"].startswith("1.00")
    items = {i["item"]: i for i in coder["items"]}
    assert "listing-paged" in items["coder/signal/0"]["terms"] and items["coder/decoy/1"]["terms"] == ["other(unclassified)"]
    lb.write_controls(store, payload)
    path = store.index_dir / "controls.json"
    assert path.exists() and json.loads(path.read_text())[lb.CODER]["items"][1]["expected"] is None
    _index.regenerate(store)
    assert path.exists() and "controls" not in _index.PROJECTIONS, "a telemetry file beside the projections, regenerated by nothing"
    assert _lint.run(store).green
