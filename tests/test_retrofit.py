"""Retrofit: an old attached arm's recorded sessions spliced into a fresh store and re-closed and re-consolidated by today's
code, rows unchanged, references into the old store stripped, a snapshot after every pass, and the reading beside the
original from its history."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hgi import evolution as _evolution
from hgi import experiment as _experiment
from hgi import model as _model
from hgi import registry as _registry
from hgi import retrofit as _retrofit
from hgi.store import git

EXPERIMENTS = Path(__file__).resolve().parents[1] / "experiments"


@pytest.fixture(autouse=True)
def clean(monkeypatch):
    monkeypatch.delenv("HGI_WEAVE_PROJECT", raising=False)
    _model.reset()
    yield
    _model.reset()


def _plant(source: Path) -> None:
    """A reference into the old store on the recorded session, as a real arm's boot would have left: consulted D-0001, a fire seen."""
    path = source / "store" / "sessions" / "S-0002.json"
    s = json.loads(path.read_text())
    s["consulted"] = [{"record": "D-0001", "disposition": "U-0001"}]
    s["considered"].append({"record": "D-0001", "terms_matched": ["http-tool"], "via": "index", "guard_passed": True, "owed_act": "apply"})
    s["fires_seen"] = ["F-0001"]
    path.write_text(json.dumps(s, indent=2, sort_keys=True) + "\n")


def _rows(arm: Path, session: str) -> list[dict]:
    return json.loads((arm / "store" / "sessions" / f"{session}.json").read_text())["evaluation"]["rows"]


def test_a_stub_arm_retrofits_end_to_end_rows_unchanged_references_stripped_a_snapshot_per_pass(tmp_path):
    exp = _experiment.load(EXPERIMENTS / "smoke.toml")
    _experiment.run_arm(exp, "attached", tmp_path)
    source = tmp_path / "smoke" / "attached"
    _plant(source)
    out = tmp_path / "retrofit" / "smoke-attached"
    record = _retrofit.retrofit(source, out, teacher="stub")

    meta = record["retrofit"]
    assert meta["source"] == str(source.resolve()) and meta["teacher"] == "stub" and meta["pass_model"] == "stub"
    assert meta["source_commit"] == git("rev-parse", "HEAD", cwd=source) and meta["code_commit"] == git("rev-parse", "HEAD") and meta["cadence"] == 2
    assert (record["experiment"], record["arm"], record["sessions"]) == ("retrofit", "smoke-attached", ["S-0001", "S-0002"])
    for s in record["sessions"]:
        assert _rows(out, s) == _rows(source, s), "the forward pass is the record: the rows are spliced in unchanged"

    spliced = json.loads((out / "store" / "sessions" / "S-0002.json").read_text())
    assert spliced["consulted"] == [] and all(c["via"] == "constitution" for c in spliced["considered"]) and spliced["fires_seen"] == []
    assert spliced["closed_at"] and spliced["carry_forward"].startswith("pass 2 scored"), "today's close ran on the spliced session"

    snap1 = json.loads((out / "snapshots" / "after-pass-1.json").read_text())
    snap2 = json.loads((out / "snapshots" / "after-pass-2.json").read_text())
    assert set(snap1["store"]) >= {"decisions", "observations", "fires", "steers", "proposals", "consolidations"}
    assert snap1["consolidation"] is None and snap2["consolidation"]["id"] == "K-0001" and snap2["consolidation"]["after_pass"] == 2
    assert snap2["splice"]["consulted"] == ["D-0001"] and snap2["splice"]["considered"] == ["D-0001"] and snap2["splice"]["fires_seen"] == ["F-0001"]
    assert snap1["splice"]["consulted"] == [] and snap1["splice"]["fires_emitted"] == [] and snap1["pass"] == 1 and snap1["session"] == "S-0001"

    subjects = git("log", "--reverse", "--format=%s", cwd=out).splitlines()
    assert subjects[0].startswith("Genesis for retrofit/smoke-attached: priced for stub, consolidating every 2, constitution C-0001..C-0007; retrofit of smoke/attached at ")
    assert any(s.startswith("Splice S-0002 pass 2 from ") and "stripped D-0001 F-0001" in s for s in subjects)
    assert any(s.startswith("Close S-0001 pass 1") for s in subjects) and any(s.startswith("Consolidate K-0001 after pass 2") for s in subjects)
    assert any(s.startswith("Snapshot after pass 2:") for s in subjects) and subjects[-1].startswith("Retrofit retrofit/smoke-attached finished:")

    ids = _registry.read_json(out / "store" / "registry" / "ids.json")
    source_ids = _registry.read_json(source / "store" / "registry" / "ids.json")
    assert ids["S"] == 2 and ids["D"] >= source_ids["D"] == 2, "the counters start past the old store's: no new decision can wear an id a row already names"
    assert snap2["consolidation"]["admitted"] == ["D-0003", "D-0004"] and meta["id_counters"] == {"D": 2, "S": 2}
    assert _registry.load(out / "store").bars["consolidation_every_passes"] == 2

    synthesized, root = _experiment.from_dir(out)
    assert root == tmp_path.resolve() and synthesized.name == "retrofit" and "not a live run" in synthesized.description
    table = _experiment.report(synthesized, root)
    assert "| smoke-attached | stub | attached | 1×2 |" in table and "not a live run" in table

    text = _retrofit.compare([out], tmp_path / "results")
    reading = json.loads((tmp_path / "results" / "smoke-attached.json").read_text())
    assert [p["pass"] for p in reading["passes"]] == [1, 2]
    assert reading["passes"][0]["original"]["consolidation"] is None and reading["passes"][1]["original"]["consolidation"]["id"] == "K-0001"
    assert reading["passes"][1]["original"]["subject"].startswith("Consolidate K-0001 after pass 2"), "the original after pass 2 is read at its consolidation commit"
    assert reading["passes"][0]["original"]["rows"] == len(_rows(source, "S-0001"))
    md = (tmp_path / "results" / "smoke-attached.md").read_text()
    assert "## After each pass" in md and "## Where they diverge, and why" in md and "D-0001" in md
    shapes = snap2["store"]["observations"]["by_shape"]
    assert shapes and all(set(c) >= {"open", "promoted", "dismissed", "sessions", "names"} for c in shapes.values())
    assert set(snap1["store"]["observations"]["by_shape"]) == {"uncoded"}, "a shape is the coder's at the next consolidation"
    assert "## Observations by shape, pass by pass" in md and "| uncoded |" in md
    assert "| [smoke-attached](smoke-attached.md) | 2 | stub |" in text


def test_divergences_name_the_context_the_original_had_and_the_consolidation_outcomes():
    store = {"decisions": [], "observations": {"open": [], "by_state": {}}, "fires": [], "steers": [], "proposals": [], "queue": [], "consolidations": [], "ledger": {}}
    close = {"dispositions": [{"record": "D-0001", "disposition": "applied", "note": None}], "observations_filed": ["O-0001"], "steers_filed": [], "ledger_entries": [], "proposals": 1, "carry_forward": ""}
    o = {"pass": 3, "in_context": ["D-0001"], "off_map": False, "close": close, "store": store,
         "consolidation": {"id": "K-0002", "admitted": [], "flipped": [], "dismissed": [], "retired": [], "nominations": [{"subject": "x", "outcome": "draft refused at parse: not_this"}]}}
    r = {"pass": 3, "in_context": [], "off_map": True, "close": close | {"observations_filed": ["O-0001", "O-0002"]}, "store": store,
         "consolidation": {"id": "K-0002", "admitted": ["D-0002"], "flipped": [], "dismissed": ["O-0001"], "retired": [], "nominations": [{"subject": "x", "outcome": "admitted D-0002"}]}}
    lines = _retrofit.divergences(o, r)
    assert lines[0].startswith("pass 3: the original booted with D-0001 in context (D-0001 applied)") and lines[0].endswith("read the failed rows as off-map")
    assert any("filed 1 observation originally and 2 retrofitted" in l for l in lines)
    assert any("K-0002 admitted nothing; the retrofit K-0002 admitted D-0002" in l for l in lines)
    assert any("noise filter dismissed O-0001" in l for l in lines)
    assert _retrofit.divergences(None, r) == ["pass 3: the original's history holds no commit after this pass; nothing to read beside"]


def test_a_stream_arm_retrofits_batch_by_batch_with_the_revisit_and_stops_at_upto(tmp_path):
    exp = _experiment.load(EXPERIMENTS / "stream-smoke.toml")
    _experiment.run_arm(exp, "attached", tmp_path)
    source = tmp_path / "stream-smoke" / "attached"
    out = tmp_path / "retrofit" / "stream-smoke-attached"
    record = _retrofit.retrofit(source, out, teacher="stub")
    assert record["sessions"] == [f"S-000{n}" for n in range(1, 6)] and record["stream"]["passes"]["5"] == 1
    assert sorted(p.name for p in (out / "snapshots").glob("*.json")) == sorted(f"after-pass-{n}.json" for n in range(1, 6))
    assert (out / "store" / "consolidations" / "K-0002.json").exists() and not (out / "store" / "consolidations" / "K-0003.json").exists(), "no consolidation after the revisit"
    log = json.loads((out / "evolution.json").read_text())
    assert log["warning"].startswith("retrofitted from stream-smoke/attached") and "not a live run" in log["warning"]
    assert [p["kind"] for p in log["passes"]] == ["stream"] * 4 + ["revisit"] and all(p["in_context"] == [] for p in log["passes"])
    synthesized, root = _experiment.from_dir(tmp_path / "retrofit")
    assert _evolution.write_experiment(synthesized, root).startswith("# retrofit — evolution: not a live run")

    partial = _retrofit.retrofit(source, tmp_path / "retrofit" / "partial", teacher="stub", upto=2)
    assert partial["sessions"] == ["S-0001", "S-0002"] and partial["retrofit"]["upto"] == 2
    with pytest.raises(SystemExit, match="exists; pass --force"):
        _retrofit.retrofit(source, tmp_path / "retrofit" / "partial", teacher="stub")


def test_only_an_attached_arm_retrofits(tmp_path):
    exp = _experiment.load(EXPERIMENTS / "smoke.toml")
    _experiment.run_arm(exp, "detached", tmp_path, commit=False)
    with pytest.raises(SystemExit, match="only an attached arm"):
        _retrofit.retrofit(tmp_path / "smoke" / "detached", tmp_path / "retrofit" / "x", teacher="stub")
