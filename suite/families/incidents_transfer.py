"""The incidents-transfer family: the nine incident bundles, re-dressed.

The ``incidents`` family grades whether the convention of that world is
learned — *the loud reading is the wrong one*, so the class must be named and
a cause reading cited while citing the bundle's decoy fails the task. This
family grades whether the *lesson* transferred rather than the bundle. Every
task here is one of the nine, worn in different clothes: the readings are
renamed (``pool-debug`` is ``conn-counters``, ``provider-status`` is
``vendor-statuspage``), the services are renamed (``orders`` is
``purchases``, ``search`` is ``discovery``), the host ports are shifted by a
thousand and every clock time by three hours. What is *not* re-dressed is the
class vocabulary — it is the answer — and the shape of the walk: the same
budget of the cause readings plus two, the same readings at
``/readings/<name>``, the same hidden check.

So a record that learned the convention — read the quiet configuration and
the service's own log, distrust the loud one — transfers and scores here; a
record that memorised ``pool-debug`` or ``orders`` or port ``8080`` does not.
A record admitted while scoring ``incidents`` is scored again on a suite that
holds this family beside it.

The bundles are not re-authored: the records are the pinned records of
``incidents``, substituted through :func:`redress`, and the prompt, the
routes and the check are ``incidents``' own functions handed the re-dressed
record — the two families therefore share one convention and differ only in
their clothes. ``incidents-transfer/upstream-outage-b`` is still the pool
class's look-alike control: a timeout storm with a genuinely saturated pool
whose saturation is a consequence of provider latency, its pool readings
(here ``conn-counters`` and ``client-settings``) decoys.
"""

from __future__ import annotations

import re
from typing import Any

from suite.families import family
from suite.families.genesis import result_object
from suite.families.incidents import BUDGET_SLACK, SHAPES, check_for, prompt, routes
from suite.tasks import Task

READINGS = {
    "broker-health": "bus-probe", "broker-metrics": "bus-metrics", "build-diff": "artifact-diff",
    "catalog-audit": "inventory-audit", "connection-stats": "socket-stats", "data-change-log": "record-change-log",
    "datastore-health": "db-probe", "datastore-log": "db-log", "datastore-metrics": "db-metrics",
    "dependency-health": "egress-probe", "deploy-history": "release-ledger", "gateway-log": "edge-log",
    "gateway-status": "edge-status", "host-metrics": "node-metrics", "input-samples": "payload-samples",
    "known-good": "last-good", "network-health": "net-probe", "pool-config": "client-settings",
    "pool-debug": "conn-counters", "producer-log": "publisher-log", "provider-status": "vendor-statuspage",
    "queue-debug": "stream-counters", "queue-depth-history": "stream-depth-history", "queue-head": "stream-head",
    "replica-status": "instance-status", "request-samples": "call-samples", "service-log": "app-log",
    "service-metrics": "app-metrics", "traffic-metrics": "load-metrics", "worker-log": "consumer-log",
    "worker-metrics": "consumer-metrics",
}
"""Every reading name the nine bundles hold, renamed; the mapping is total and asserted in :func:`tasks`."""

SERVICES = {
    "orders": "purchases", "search": "discovery", "catalog": "inventory", "billing": "invoicing",
    "checkout": "cart", "pricing": "quotes", "notifications": "alerts", "jobs": "tasks",
    "payments": "settlements", "dispatcher": "courier", "pay": "settle", "price": "quote",
}
"""The services, queues and URL stems the briefs name — no replacement contains an original as a word."""

SUBS = READINGS | SERVICES
_WORD = re.compile(r"\b(" + "|".join(sorted(map(re.escape, SUBS), key=len, reverse=True)) + r")\b", re.I)
_PORT = re.compile(r"""(port[\s:='"`]+|(?<=[A-Za-z0-9\].]):|->)(\d{4})\b""", re.I)
"""A four-digit port: after ``port``, after a host's colon, or after a docker mapping's arrow — never a bare JSON number."""
_TIME = re.compile(r"(?<![\d:])([01]\d|2[0-3]):([0-5]\d)\b")
"""``HH:MM``, including the head of an ``HH:MM:SS`` or an ISO timestamp; the seconds ride along unshifted."""


def redress(text: str) -> str:
    """Rename the readings and services, shift the ports by a thousand and the clock by three hours."""
    text = _WORD.sub(lambda m: SUBS[m[1].lower()].capitalize() if m[1][0].isupper() else SUBS[m[1].lower()], text)
    text = _PORT.sub(lambda m: m[1] + (str(int(m[2]) + 1000) if 3000 <= int(m[2]) <= 9999 else m[2]), text)
    return _TIME.sub(lambda m: f"{(int(m[1]) + 3) % 24:02d}:{m[2]}", text)


def record_of(record: dict[str, Any]) -> dict[str, Any]:
    """One ``incidents`` record in the other clothes: same id, same class, everything else substituted."""
    return dict(record, brief=redress(record["brief"]),
                readings={READINGS[n]: redress(t) for n, t in record["readings"].items()},
                cause_readings=[READINGS[n] for n in record["cause_readings"]],
                decoy_readings=[READINGS[n] for n in record["decoy_readings"]])


@family("incidents-transfer", source="derived from the `incidents` family's pinned records — the same nine bundles and the same "
                                     "convention, with the readings, services, ports and clock times re-dressed")
def tasks() -> list[Task]:
    from suite.families import FAMILIES

    out = []
    for pinned in FAMILIES["incidents"].records():
        assert not set(pinned["readings"]) - set(READINGS), f"unmapped readings: {sorted(set(pinned['readings']) - set(READINGS))}"
        r = record_of(pinned)
        out.append(Task(f"incidents-transfer/{r['id']}", prompt(r), SHAPES, result_object("class", "cause_readings"),
                        check_for(r), http_budget=len(r["cause_readings"]) + BUDGET_SLACK, routes=routes(r)))
    return out
