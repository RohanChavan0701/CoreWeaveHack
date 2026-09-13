"""The incidents family: the tenant-incident evidence bundles as budgeted diagnosis tasks.

Each task states one incident brief — the surface, the signal, the blast
radius — and the readings an operator holds, served one per call at
``/readings/<name>``. The names are in the prompt, so listing the menu is
free and only fetching costs; the budget is the cause readings plus two, so
there is room for one recovered transient failure and none for a walk down
the whole bundle. What the family grades is therefore the route, not the
prose: the answer must name the class *and* cite a cause reading, and citing
any of the bundle's decoy readings — the readings keyed on the louder shape a
naive read reaches for first — fails the task however right the class is.
The decoy is the convention of this world: the loud reading is the wrong one.

Source: ``hearth/tenant-incident/scenarios``, hand-authored; the brief, the
``evidence/`` readings and the ``shape.yml`` cause/decoy lists are read from
the local tree at fetch time, so a run needs no network.

``upstream-outage-b`` is the pool class's built-in look-alike control: a
gateway timeout storm with a genuinely saturated pool, where the saturation
is a consequence of provider latency — its pool readings are decoys, and a
policy that has learned "timeout storm ⇒ pool exhaustion" fails it.
"""

from __future__ import annotations

import re
from typing import Any

from suite.families import DATA, family
from suite.families.genesis import result_object
from suite.tasks import Task

SCENARIOS = DATA.parents[1] / "hearth" / "tenant-incident" / "scenarios"
CLASSES = ["pool-exhaustion", "bad-deploy", "poison-message", "upstream-outage"]
BUDGET_SLACK = 2
"""Calls the budget allows beyond the cause readings: one wrong turn, or one transient failure recovered from."""
SHAPES = ("http-tool", "tool-budget", "task-planning")
"""How a bundle presents to a boot: readings over the API, a budget to plan the walk against."""

INSTRUCTION = ('Return as result an object {"class": one of [' + ", ".join(CLASSES) +
               '], "cause_readings": [the reading names that show the cause]}.')


def _list(shape: str, key: str) -> list[str]:
    """The ``key: [a, b, c]`` line of a ``shape.yml`` — the only two lines of it this family reads."""
    m = re.search(rf"^{key}: \[(.*)\]\s*$", shape, re.M)
    return [n.strip() for n in m.group(1).split(",")] if m else []


def fetch(n: int) -> list[dict[str, Any]]:
    """Transcribe at most ``n`` local scenario directories into pinned records."""
    out: list[dict[str, Any]] = []
    for d in sorted(SCENARIOS.iterdir()):
        if len(out) == n:
            break
        brief = d / "brief.evidence-bundle.md"
        if not brief.is_file():
            continue
        shape = (d / "shape.yml").read_text()
        out.append({"id": d.name, "class": re.sub(r"-[a-z]$", "", d.name), "brief": brief.read_text(),
                    "readings": {p.name: p.read_text() for p in sorted((d / "evidence").iterdir()) if p.is_file()},
                    "cause_readings": _list(shape, "cause_readings"), "decoy_readings": _list(shape, "decoy_readings")})
    return out


def prompt(record: dict[str, Any]) -> str:
    """The brief with its ``## Evidence`` section replaced by the API the operator answers on."""
    names = sorted(record["readings"])
    api = (f"- The operator serves readings over the API: GET /readings/<name>. Readings held: {', '.join(names)}. "
           "Each GET costs one call.")
    brief = re.sub(r"## Evidence\n.*?(?=\n## )", f"## Evidence\n\n{api}\n", record["brief"], flags=re.S)
    return f"{brief.strip()}\n\n{INSTRUCTION}"


def routes(record: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {"/readings": {"readings": sorted(record["readings"])}}
    out.update({f"/readings/{name}": {"name": name, "text": text} for name, text in record["readings"].items()})
    return out


def check_for(record: dict[str, Any]):
    """The hidden test: the right class, at least one cause reading cited, and no decoy reading cited."""
    cause, decoy = set(record["cause_readings"]), set(record["decoy_readings"])

    def check(result: Any, workdir) -> bool:
        if not isinstance(result, dict) or result.get("class") != record["class"]:
            return False
        cited = {c for c in (result.get("cause_readings") or []) if isinstance(c, str)}
        return bool(cited & cause) and not (cited & decoy)

    return check


@family("incidents", source="hearth/tenant-incident/scenarios evidence bundles, hand-authored; the brief, the readings and the "
                            "shape.yml cause/decoy lists read from the local tree", fetch=fetch)
def tasks() -> list[Task]:
    from suite.families import FAMILIES

    return [Task(f"incidents/{r['id']}", prompt(r), SHAPES,
                 result_object("class", "cause_readings"), check_for(r),
                 http_budget=len(r["cause_readings"]) + BUDGET_SLACK, routes=routes(r))
            for r in FAMILIES["incidents"].records()]
