"""The curriculum family: every lesson of the world worn in many clothes, for the stream experiment.

A lesson (:data:`suite.lessons.LESSONS`) is a convention of this world that
a general model gets wrong on first contact — the five the ``conventions``
family carries by hand, plus an export that ends with a TOTAL row and a
route that answers 401 until the token in ``token.txt`` is passed. This
family generates :data:`CLOTHES` tasks per lesson, each a different
instance — other file names, counts, values, collections, endpoints,
columns — derived from one seeded generator per lesson, so a task the loop
has not seen turns on a lesson it may have. That is what a stream
experiment measures: whether a record admitted on one clothing of a lesson
scores on the next, unseen clothing.

Every task carries the naive first-contact policy as its scripted policy,
built from the same mechanisms ``conventions`` uses (the no-newline files,
the naive count, the naive comma split), so the deterministic stub's curve
on this family is flat and honest, and the naive outcome
(:func:`suite.lessons.naive_outcome`) is derivable for each task. The
clothes are disjoint from the file names, routes and endpoints
``conventions`` and ``transfer`` name.

Two families are generated from the same clothes and differ only in slack:
``curriculum`` budgets each task at the knowing policy's calls plus one, so
a pass may spend a call discovering the convention (a ``cat`` before the
count, the first page before the walk); ``curriculum-strict`` budgets at
the knowing policy's calls exactly, so the convention costs a call the
budget does not hold and only a pass that already knows it — from the
store, or from the model — stays within budget. The strict pool asks the
knowledge-base question directly: does the memory save the discovery.
"""

from __future__ import annotations

import csv
import io
import json
import random
from typing import TYPE_CHECKING, Any, Callable

from suite.families import family
from suite.families.conventions import BOM, _naive_count, _naive_csv, _no_newline
from suite.families.genesis import RESULT_INT, RESULT_STR, result_object
from suite.lessons import LESSONS
from suite.tasks import Task

if TYPE_CHECKING:
    from suite.agent import Script

CLOTHES = 12
"""Tasks generated per lesson."""

SLACK = {"curriculum": 1, "curriculum-strict": 0}
"""Calls a family's budgets leave beyond what the knowing policy needs."""

STEMS = ("batch", "segment", "shard", "slice", "block", "run", "trace", "feed", "dump", "extract", "spool", "capture")
EXTS = ("txt", "log", "out", "rec", "lst", "dat")
COLLECTIONS = ("entries", "orders", "events", "readings", "tickets", "invoices", "samples", "jobs", "alerts", "parcels", "sensors", "bids")
RESOURCES = ("projects", "devices", "teams", "nodes", "plans", "stores", "zones", "agents", "sites", "pools", "vaults", "fleets")
SECURE = ("balance", "quota", "ledger", "credits", "usage", "limits", "audit", "keys", "budget", "score", "tally", "meter")
NAMES = ("Lin", "Ada", "Grace", "Alan", "Linus", "Barbara", "Ken", "Dennis", "Margaret", "Radia", "Tim", "Anita")
CITIES = ("Berlin", "London", "Helsinki", "Lisbon", "Oslo", "Prague", "Vienna", "Zurich", "Dublin", "Madrid", "Riga", "Tallinn")
QUOTED_PEOPLE = ("Doe, Jane", "Smith, John", "Turing, Alan", "Hopper, Grace", "Lovelace, Ada", "Liskov, Barbara", "Kay, Alan", "Perlman, Radia")
PLAIN_PEOPLE = ("Ada Lovelace", "Grace Hopper", "Linus Torvalds", "Ken Thompson", "Dennis Ritchie", "Margaret Hamilton", "Tim Berners-Lee", "Anita Borg")
QUOTED_FIRMS = ("Acme, Inc.", "Initech, LLC", "Umbrella, Corp.", "Wonka, Ltd.", "Hooli, Inc.", "Vandelay, LLC")
PLAIN_FIRMS = ("Globex", "Tyrell", "Cyberdyne", "Soylent", "Stark", "Wayne")
KEYS = (("title", "items"), ("name", "entries"), ("label", "values"), ("project", "members"), ("release", "changes"), ("board", "cards"))


def _rng(lesson: str, i: int) -> random.Random:
    """One generator per lesson and clothing, shared by both families so their clothes are the same."""
    return random.Random(f"curriculum:{lesson}:{i}")


def _budget(n: int) -> str:
    return f"You have a budget of {n} shell call{'s' if n != 1 else ''}."


def _csv(columns: list[str], rows: list[list[Any]]) -> str:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(columns)
    w.writerows(rows)
    return buf.getvalue()


# --- the lessons, one generator each: (i) -> Task -----------------------------------------------

def _trailing_newline(fam: str, i: int, slack: int) -> Task:
    r = _rng("trailing-newline", i)
    stem, ext, k = STEMS[i % len(STEMS)], EXTS[i % len(EXTS)], r.randint(2, 5)
    names = [f"{stem}-{j}.{ext}" for j in range(1, k + 1)]
    counts = {n: r.randint(1, 9) for n in names}
    gold = sum(counts.values())
    return Task(f"{fam}/newline_{i:02d}",
                f"{k} files {', '.join(names)} are in the working directory. Return the total number of lines across them as result, "
                f"using the shell tool. {_budget(1 + slack)}",
                ("shell-tool", "tool-budget"), RESULT_INT, lambda res, w, g=gold: res == g, shell_budget=1 + slack,
                files=_no_newline(counts), stub=_naive_count(names), lesson="trailing-newline")


def _paged_api(fam: str, i: int, slack: int) -> Task:
    r = _rng("paged-api", i)
    coll, pages, per = COLLECTIONS[i % len(COLLECTIONS)], r.randint(2, 4), r.randint(2, 4)
    counting = i % 2 == 1
    routes: dict[str, Any] = {}
    gold = 0
    for p in range(1, pages + 1):
        path = f"/{coll}" if p == 1 else f"/{coll}?page={p}"
        if counting:
            items = [{"id": (p - 1) * per + j, "active": r.random() < 0.5} for j in range(1, per + 1)]
            gold += sum(1 for it in items if it["active"])
        else:
            items = [r.randint(1, 40) for _ in range(per)]
            gold += sum(items)
        routes[path] = {"items": items, "next": f"/{coll}?page={p + 1}" if p < pages else None}
    if counting:
        prompt = f"GET /{coll} from the API and return the number of {coll} whose active field is true as result."
        stub = lambda s, c=coll: sum(1 for it in s.get(f"/{c}")["items"] if it["active"])  # noqa: E731
    else:
        prompt = f"GET /{coll} from the API and return the sum of every item as result."
        stub = lambda s, c=coll: sum(s.get(f"/{c}")["items"])  # noqa: E731
    return Task(f"{fam}/paged_{i:02d}", prompt, ("http-tool", "error-wrapping"), RESULT_INT, lambda res, w, g=gold: res == g,
                http_budget=pages + slack, routes=routes, stub=stub, lesson="paged-api")


def _moved_v2(fam: str, i: int, slack: int) -> Task:
    r = _rng("moved-v2", i)
    res, ident = RESOURCES[i % len(RESOURCES)], r.randint(3, 99)
    old, new = f"/{res}/{ident}", f"/v2/{res}/{ident}"
    gone = {"$error": {"message": f"GET {old} failed", "cause": f"HTTP 410 Gone: this API serves {new}"}}
    if i % 2 == 0:
        name = NAMES[i % len(NAMES)]
        return Task(f"{fam}/moved_{i:02d}", f"GET {old} and return the {res[:-1]}'s name as result.", ("http-tool", "error-wrapping"),
                    RESULT_STR, lambda r_, w, g=name: r_ == g, http_budget=1 + slack, routes={old: gone, new: {"id": ident, "name": name}},
                    stub=lambda s, p=old: s.get(p)["name"], lesson="moved-v2")
    return Task(f"{fam}/moved_{i:02d}", f"GET {old} and return the string 'ok' as result when the response's ok field is true.",
                ("http-tool", "error-wrapping"), RESULT_STR, lambda r_, w: r_ == "ok", http_budget=1 + slack,
                routes={old: gone, new: {"id": ident, "ok": True}}, stub=lambda s, p=old: "ok" if s.get(p)["ok"] else "not ok", lesson="moved-v2")


def _csv_quoted(fam: str, i: int, slack: int) -> Task:
    r = _rng("csv-quoted", i)
    stem = STEMS[i % len(STEMS)]
    name = f"{stem}.csv"
    if i % 2 == 0:  # count the people in one city; at least one of them has a quoted name, so the naive split undercounts
        city = CITIES[i % len(CITIES)]
        others = [c for c in CITIES if c != city]
        rows = [[p, city, r.randint(20, 80)] for p in r.sample(QUOTED_PEOPLE, r.randint(1, 3))]
        rows += [[p, r.choice(others), r.randint(20, 80)] for p in r.sample(QUOTED_PEOPLE, 2)]
        rows += [[p, r.choice([city, *others]), r.randint(20, 80)] for p in r.sample(PLAIN_PEOPLE, 4)]
        r.shuffle(rows)
        gold = sum(1 for row in rows if row[1] == city)
        return Task(f"{fam}/csv_{i:02d}",
                    f"{name} is in the working directory with columns name,city,age. Return the number of people whose city is {city} as result, "
                    f"using the shell tool. {_budget(1 + slack)}",
                    ("shell-tool", "file-tool", "tool-budget"), RESULT_INT, lambda res, w, g=gold: res == g, shell_budget=1 + slack,
                    files={name: _csv(["name", "city", "age"], rows)}, stub=_naive_csv(2, city, name), lesson="csv-quoted")
    firm = QUOTED_FIRMS[i % len(QUOTED_FIRMS)]
    rows = [[1000 + j, r.choice([firm, *PLAIN_FIRMS, *QUOTED_FIRMS]), round(r.uniform(5, 900), 2)] for j in range(1, r.randint(5, 8))]
    rows[r.randrange(len(rows))][1] = firm
    gold = round(sum(row[2] for row in rows if row[1] == firm), 2)
    return Task(f"{fam}/csv_{i:02d}",
                f"{name} is in the working directory with columns order,customer,total. Return the sum of the total column over the orders whose "
                f"customer is \"{firm}\" as result, using the shell tool. {_budget(1 + slack)}",
                ("shell-tool", "file-tool", "tool-budget"), {"type": "object", "required": ["result"], "properties": {"result": {"type": "number"}}},
                lambda res, w, g=gold: isinstance(res, (int, float)) and abs(res - g) < 0.011, shell_budget=1 + slack,
                files={name: _csv(["order", "customer", "total"], rows)},
                stub=lambda s, n=name, f=firm: float(s.shell(f"awk -F, 'NR>1 && $2==\"{f}\" {{t+=$3}} END {{print t+0}}' {n}").strip()), lesson="csv-quoted")


def _footer_row(fam: str, i: int, slack: int) -> Task:
    r = _rng("footer-row", i)
    stem = STEMS[(i + 3) % len(STEMS)]
    name = f"{stem}-export.csv"
    rows = [[f"R{100 + j}", r.choice(PLAIN_FIRMS), r.randint(10, 500)] for j in range(1, r.randint(4, 9))]
    total = sum(row[2] for row in rows)
    body = _csv(["ref", "account", "amount"], rows) + f"TOTAL,,{total}\n"
    if i % 2 == 0:
        return Task(f"{fam}/footer_{i:02d}",
                    f"{name} is in the working directory with columns ref,account,amount. Return the sum of the amount column as result, "
                    f"using the shell tool. {_budget(1 + slack)}",
                    ("shell-tool", "file-tool", "tool-budget"), RESULT_INT, lambda res, w, g=total: res == g, shell_budget=1 + slack, files={name: body},
                    stub=lambda s, n=name: int(s.shell(f"awk -F, 'NR>1 {{t+=$3}} END {{print t+0}}' {n}").strip()), lesson="footer-row")
    return Task(f"{fam}/footer_{i:02d}",
                f"{name} is in the working directory with columns ref,account,amount. Return the number of records in it as result, "
                f"using the shell tool. {_budget(1 + slack)}",
                ("shell-tool", "file-tool", "tool-budget"), RESULT_INT, lambda res, w, g=len(rows): res == g, shell_budget=1 + slack, files={name: body},
                stub=lambda s, n=name: int(s.shell(f"awk 'NR>1' {n} | wc -l").strip()), lesson="footer-row")


def _token_route(fam: str, i: int, slack: int) -> Task:
    r = _rng("token-route", i)
    what, token, value = SECURE[i % len(SECURE)], "".join(r.choices("abcdef0123456789", k=8)), r.randint(1, 9999)
    path = f"/secure/{what}"
    routes = {path: {"$error": {"message": f"GET {path} failed", "cause": f"HTTP 401 Unauthorized: routes under /secure require ?token=<the token in token.txt>"}},
              f"{path}?token={token}": {what: value}}
    return Task(f"{fam}/token_{i:02d}", f"GET {path} and return the {what} field as result.", ("http-tool", "file-tool", "error-wrapping"),
                RESULT_INT, lambda res, w, g=value: res == g, http_budget=1 + slack, files={"token.txt": token + "\n"}, routes=routes,
                stub=lambda s, p=path, k=what: s.get(p)[k], lesson="token-route")


def _bom(fam: str, i: int, slack: int) -> Task:
    r = _rng("bom", i)
    key, items = KEYS[i % len(KEYS)]
    name = f"{STEMS[(i + 7) % len(STEMS)]}.json"
    title = f"{r.choice(('Q1', 'Q2', 'Q3', 'Q4', 'H1', 'H2'))}-{r.randint(2020, 2029)}"
    n = r.randint(2, 7)
    payload = {key: title, items: [f"{items[:-1]}-{j}" for j in range(n)]}

    def naive(s: "Script", nm=name, k=key, it=items):
        data = json.loads(s.read(nm))  # raises on the byte order mark
        return {k: data[k], "count": len(data[it])}

    return Task(f"{fam}/bom_{i:02d}",
                f"Read {name}, then return {{\"{key}\": <{key} from the file>, \"count\": <number of entries in {items}>}} as result.",
                ("file-tool", "output-schema"), result_object(key, "count"), lambda res, w, k=key, t=title, c=n: res == {k: t, "count": c},
                files={name: BOM + json.dumps(payload)}, stub=naive, lesson="bom")


GENERATORS: dict[str, Callable[[str, int, int], Task]] = {
    "trailing-newline": _trailing_newline, "paged-api": _paged_api, "moved-v2": _moved_v2, "csv-quoted": _csv_quoted,
    "footer-row": _footer_row, "token-route": _token_route, "bom": _bom,
}
assert set(GENERATORS) == set(LESSONS), "every lesson has a generator and every generator a lesson"


def generate(fam: str) -> list[Task]:
    return [gen(fam, i, SLACK[fam]) for lesson, gen in GENERATORS.items() for i in range(CLOTHES)]


@family("curriculum", source=f"generated; every lesson of the world in {CLOTHES} clothes each, budgeted with one call to spare, for the stream experiment")
def tasks() -> list[Task]:
    return generate("curriculum")


@family("curriculum-strict", source=f"generated; the same {CLOTHES} clothes per lesson, budgeted at exactly the knowing policy's calls")
def strict_tasks() -> list[Task]:
    return generate("curriculum-strict")
