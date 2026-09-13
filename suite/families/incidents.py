"""The incidents family: the tenant-incident evidence bundles as budgeted diagnosis tasks, each worn four ways.

Each task states one incident brief — the surface, the signal, the blast
radius — and the readings an operator holds, served one per call at
``/readings/<name>``. The names are in the prompt, so listing the menu is
free and only fetching costs; the budget is the cause readings plus the
family's slack, so there is no room for a walk down the whole bundle. What
the family grades is therefore the route, not the prose: the answer must
name the class *and* cite a cause reading, and citing any of the bundle's
decoy readings — the readings keyed on the louder shape a naive read
reaches for first — fails the task however right the class is. The answer
carries an optional third key, ``ruled_out``, because a failed row that
names the readings the attempt opened and set aside states which reading it
trusted and which it disposed of, and that disposal is the world-fact the
close lens can notice — a bare wrong answer names neither. The decoy is
the convention of this world: the loud reading is the wrong one. Which loud
reading it is, is the bundle's **lesson** — ``decoy-<shape>`` from its
``shape.yml`` (:data:`suite.lessons.LESSONS`), the thing a stream deals the
pool over and a record could carry to the next bundle. The knowing floor is
one call per cause reading, so ``solution_economy`` here is the step count.

Source: ``hearth/tenant-incident/scenarios``, hand-authored; the brief, the
``evidence/`` readings and the ``shape.yml`` cause/decoy lists are read from
the local tree at fetch time, so a run needs no network.

**Clothes.** Nine bundles are nine samples, one per lesson per stream pass,
so each is worn :data:`CLOTHES` ways (:func:`redress`): dressing 0 is the
bundle as authored, dressings 1–3 rename every reading and every service,
shift the host ports by a thousand each and the clock by three hours each.
The clothes are deterministic and pairwise disjoint — no two dressings of a
scenario share a reading name, a service name or a route — so a record
admitted on one clothing is scored on an unseen one when the stream deals
the next, and a record that memorised ``pool-debug`` or ``orders`` or port
``8080`` transfers to none of them while one that learned the convention
transfers to all. Thirty-six tasks, ids ``incidents/<scenario>_<i>``.

**Two pools, one difference** (as ``curriculum`` / ``curriculum-strict``):
``incidents`` budgets the cause readings plus one, so a pass may open one
decoy and still land; ``incidents-strict`` budgets the cause readings
exactly, so only a pass that already knows which readings carry the cause
stays in budget.

``upstream-outage-b`` is the pool class's built-in look-alike control: a
gateway timeout storm with a genuinely saturated pool, where the saturation
is a consequence of provider latency — its pool readings are decoys, and a
policy that has learned "timeout storm ⇒ pool exhaustion" fails it in every
clothing.
"""

from __future__ import annotations

import random
import re
from typing import TYPE_CHECKING, Any

from suite.families import DATA, family
from suite.families.genesis import result_object
from suite.tasks import Task

if TYPE_CHECKING:
    from suite.agent import Script

SCENARIOS = DATA.parents[1] / "hearth" / "tenant-incident" / "scenarios"
CLASSES = ["pool-exhaustion", "bad-deploy", "poison-message", "upstream-outage"]
CLOTHES = 4
"""Dressings of every bundle: the source and three re-dressings of it."""
SLACK = {"incidents": 1, "incidents-strict": 0}
"""Calls a family's budgets leave beyond the cause readings: one wrong turn, or none."""
SHAPES = ("http-tool", "tool-budget", "task-planning")
"""How a bundle presents to a boot: readings over the API, a budget to plan the walk against."""

INSTRUCTION = ('Return as result an object {"class": one of [' + ", ".join(CLASSES) +
               '], "cause_readings": [the reading names that show the cause], '
               '"ruled_out": [the readings you opened and set aside]}.')

def answer_schema() -> dict:
    """``class`` and ``cause_readings`` are required; ``ruled_out`` is optional, so an answer that names no disposal is
    still well formed and the check is unchanged."""
    schema = result_object("class", "cause_readings")
    schema["properties"]["result"]["properties"] = {"ruled_out": {"type": "array"}}
    return schema


READINGS = {
    "broker-health": ("bus-probe", "mq-probe", "relay-check"),
    "broker-metrics": ("bus-metrics", "mq-counters", "relay-stats"),
    "build-diff": ("artifact-diff", "bundle-delta", "image-diff"),
    "catalog-audit": ("inventory-audit", "listing-audit", "stock-review"),
    "connection-stats": ("socket-stats", "link-stats", "wire-counters"),
    "data-change-log": ("record-change-log", "row-change-log", "write-audit-log"),
    "datastore-health": ("db-probe", "store-probe", "backend-check"),
    "datastore-log": ("db-log", "store-log", "backend-journal"),
    "datastore-metrics": ("db-metrics", "store-counters", "backend-stats"),
    "dependency-health": ("egress-probe", "downstream-probe", "outbound-check"),
    "deploy-history": ("release-ledger", "rollout-ledger", "ship-log"),
    "gateway-log": ("edge-log", "proxy-log", "frontdoor-log"),
    "gateway-status": ("edge-status", "proxy-status", "frontdoor-state"),
    "host-metrics": ("node-metrics", "machine-stats", "box-counters"),
    "input-samples": ("payload-samples", "intake-samples", "inbound-records"),
    "known-good": ("last-good", "prior-good", "baseline-build"),
    "network-health": ("net-probe", "fabric-probe", "transit-check"),
    "pool-config": ("client-settings", "pooler-settings", "conn-settings"),
    "pool-debug": ("conn-counters", "pooler-counters", "lease-gauges"),
    "producer-log": ("publisher-log", "emitter-log", "sender-journal"),
    "provider-status": ("vendor-statuspage", "partner-statuspage", "supplier-state"),
    "queue-debug": ("stream-counters", "channel-counters", "backlog-gauges"),
    "queue-depth-history": ("stream-depth-history", "channel-depth-history", "backlog-trend"),
    "queue-head": ("stream-head", "channel-head", "backlog-head"),
    "replica-status": ("instance-status", "member-status", "peer-state"),
    "request-samples": ("call-samples", "ingress-samples", "hit-records"),
    "service-log": ("app-log", "workload-log", "unit-journal"),
    "service-metrics": ("app-metrics", "workload-metrics", "unit-stats"),
    "traffic-metrics": ("load-metrics", "volume-metrics", "throughput-stats"),
    "worker-log": ("consumer-log", "handler-log", "runner-journal"),
    "worker-metrics": ("consumer-metrics", "handler-stats", "runner-counters"),
}
"""Every reading name the nine bundles hold, and the three alternatives a dressing draws from; the mapping is total
and asserted in :func:`generate`."""

SERVICES = {
    "orders": ("purchases", "requisitions", "baskets"), "search": ("discovery", "lookup", "retrieval"),
    "catalog": ("inventory", "listings", "stock"), "billing": ("invoicing", "chargebook", "statements"),
    "checkout": ("cart", "tender", "till"), "pricing": ("quotes", "rates", "tariffs"),
    "notifications": ("alerts", "pings", "dispatches"), "jobs": ("tasks", "chores", "runs"),
    "payments": ("settlements", "remittances", "disbursements"), "dispatcher": ("courier", "router", "allocator"),
    "pay": ("settle", "remit", "clear"), "price": ("quote", "rate", "tariff"),
}
"""The services, queues and URL stems the briefs name — no replacement contains an original as a word."""

SUBS = READINGS | SERVICES
_WORD = re.compile(r"\b(" + "|".join(sorted(map(re.escape, SUBS), key=len, reverse=True)) + r")\b", re.I)
_PORT = re.compile(r"""(port[\s:='"`]+|(?<=[A-Za-z0-9\].]):|->)(\d{4})\b""", re.I)
"""A four-digit port: after ``port``, after a host's colon, or after a docker mapping's arrow — never a bare JSON number."""
_TIME = re.compile(r"(?<![\d:])([01]\d|2[0-3]):([0-5]\d)\b")
"""``HH:MM``, including the head of an ``HH:MM:SS`` or an ISO timestamp; the seconds ride along unshifted."""

assert all(len(a) >= CLOTHES - 1 for a in SUBS.values()), "a dressing per alternative"
assert len({a for alts in SUBS.values() for a in alts}) == sum(len(a) for a in SUBS.values()), "the alternatives are distinct"
assert not any(_WORD.search(a) for alts in SUBS.values() for a in alts), "no replacement holds an original name as a word"


def _list(shape: str, key: str) -> list[str]:
    """The ``key: [a, b, c]`` line of a ``shape.yml`` — one of the three lines of it this family reads."""
    m = re.search(rf"^{key}: \[(.*)\]\s*$", shape, re.M)
    return [n.strip() for n in m.group(1).split(",")] if m else []


def _scalar(shape: str, key: str) -> str:
    """The ``key: value`` line of a ``shape.yml``; ``decoy`` is the shape the bundle's decoy readings are keyed on."""
    m = re.search(rf"^{key}: (\S+)\s*$", shape, re.M)
    return m.group(1) if m else ""


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
                    "cause_readings": _list(shape, "cause_readings"), "decoy_readings": _list(shape, "decoy_readings"),
                    "decoy": _scalar(shape, "decoy")})
    return out


def _substitution(scenario: str, i: int) -> dict[str, str]:
    """Dressing ``i``'s map over every name. The alternatives are shuffled per scenario and per name — seeded without
    the dressing — and the dressing takes the ``i``-th of that order, so the clothes of one scenario never collide
    while no dressing is the same dictionary across scenarios."""
    return {name: sorted(alts, key=lambda a: random.Random(f"incidents:{scenario}:{name}:{a}").random())[(i - 1) % len(alts)]
            for name, alts in SUBS.items()}


def redress(record: dict[str, Any], i: int) -> dict[str, Any]:
    """Clothing ``i`` of a bundle: dressing 0 is the record as authored; 1–3 rename the readings and the services,
    shift the host ports by ``i`` thousand and the clock by ``i`` times three hours. The reading names are substituted
    in the cause and decoy lists and inside the reading texts too, so the bundle's cross-references still resolve."""
    if i == 0:
        return record
    subs = _substitution(record["id"], i)

    def dress(text: str) -> str:
        text = _WORD.sub(lambda m: subs[m[1].lower()].capitalize() if m[1][0].isupper() else subs[m[1].lower()], text)
        text = _PORT.sub(lambda m: m[1] + (str(3000 + (int(m[2]) - 3000 + 1000 * i) % 7000) if 3000 <= int(m[2]) <= 9999 else m[2]), text)
        return _TIME.sub(lambda m: f"{(int(m[1]) + 3 * i) % 24:02d}:{m[2]}", text)

    return dict(record, brief=dress(record["brief"]),
                readings={subs[n]: dress(t) for n, t in record["readings"].items()},
                cause_readings=[subs[n] for n in record["cause_readings"]],
                decoy_readings=[subs[n] for n in record["decoy_readings"]])


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


def naive_for(record: dict[str, Any]):
    """First contact: walk the readings in the order the prompt lists them, one call each, then answer from the first
    cause reading. Every bundle holds more readings than the budget allows, so the walk dies on the budget — the naive
    outcome of every task here is that error, and a pass that over-probes reproduces it."""
    names = sorted(record["readings"])
    answer = {"class": record["class"], "cause_readings": record["cause_readings"][:1], "ruled_out": []}

    def policy(s: "Script"):
        for name in names:
            s.get(f"/readings/{name}")
        return answer

    return policy


def check_for(record: dict[str, Any]):
    """The hidden test: the right class, at least one cause reading cited, and no decoy reading cited."""
    cause, decoy = set(record["cause_readings"]), set(record["decoy_readings"])

    def check(result: Any, workdir) -> bool:
        if not isinstance(result, dict) or result.get("class") != record["class"]:
            return False
        cited = {c for c in (result.get("cause_readings") or []) if isinstance(c, str)}
        return bool(cited & cause) and not (cited & decoy)

    return check


def generate(fam: str) -> list[Task]:
    """Every pinned bundle in every clothing, budgeted at the cause readings plus the family's slack."""
    from suite.families import FAMILIES

    out = []
    for pinned in FAMILIES["incidents"].records():
        assert not set(pinned["readings"]) - set(READINGS), f"unmapped readings: {sorted(set(pinned['readings']) - set(READINGS))}"
        for i in range(CLOTHES):
            r = redress(pinned, i)
            out.append(Task(f"{fam}/{r['id']}_{i}", prompt(r), SHAPES, answer_schema(), check_for(r),
                            http_budget=len(r["cause_readings"]) + SLACK[fam], routes=routes(r), stub=naive_for(r),
                            lesson=f"decoy-{r['decoy']}", knowing={"http": len(r["cause_readings"])}))
    return out


@family("incidents", source="hearth/tenant-incident/scenarios evidence bundles, hand-authored; the brief, the readings and the "
                            f"shape.yml cause/decoy lists read from the local tree, each bundle worn {CLOTHES} ways", fetch=fetch)
def tasks() -> list[Task]:
    return generate("incidents")


@family("incidents-strict", source=f"the same {CLOTHES} clothes of the same nine pinned bundles, budgeted at exactly the cause readings")
def strict_tasks() -> list[Task]:
    return generate("incidents-strict")
