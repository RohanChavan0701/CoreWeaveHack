"""The lens battery (§ 9.2, slice 6a): decoy rejection scored in Weave, telemetry populated off ``design-stage``.

Offline the ``pass`` role is the stub, which files nothing for L-0003 and files a noticing for L-0004's genuine
signals; the battery scores exactly that and writes the computed telemetry onto the lens register.
"""

from __future__ import annotations

from hgi import index as _index
from hgi import lens_battery as lb
from hgi import lint as _lint
from hgi.store import Store
from hgi.types import LensTelemetry


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


def test_the_populated_store_stays_lint_green(store):
    result = lb.run_battery(store)
    lb.populate_telemetry(store, result.telemetry)
    reloaded = Store(store.root)
    _index.regenerate(reloaded)
    assert _lint.run(reloaded).green
