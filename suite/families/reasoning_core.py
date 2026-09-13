"""The reasoning-core family: Reasoning Core's procedural generators as produce-and-verify tasks.

Each task states a small formal-language problem and is graded by the
generator's own checker rather than by a comparison against a stored answer.
Two generators are carried, both of which make the agent churn shell calls to
verify a candidate before it answers:

- **regex-following** — produce a non-empty visible-ASCII string that a given
  regular expression fully matches; the hidden check is Reasoning Core's
  ``regex.fullmatch`` verdict;
- **cfg-generation** — produce a string of at least ``min_tokens`` terminals
  that a given context-free grammar derives; the hidden check is grammar
  membership under the Earley chart parser Reasoning Core's grammar tasks use.

The instances are pinned into ``suite/data/reasoning-core.jsonl`` at a fixed
difficulty level per generator (Reasoning Core's integer ``level`` knob) and a
stored seed each, so a run needs neither the network nor the generation stack
and the suite hash is stable. The pinned record carries the presentation and
the checker's inputs — the regex, or the grammar and its start symbol and
length floor — never a witness, so the file cannot leak an answer.
:mod:`suite.families._reasoning_core` holds the checkers and the seeded
generator, and the ``source`` string pins the revision and license.

Two families are built from the same instances and differ only in slack, as
``curriculum`` and ``curriculum-strict`` do: ``reasoning-core`` budgets each
task at the knowing policy's one verification call plus one, so a pass may
spend a call iterating on a candidate; ``reasoning-core-strict`` budgets at
exactly that one call, so a wrong first candidate cannot be repaired within
budget. The instances are disjoint from every other family's — a regex or a
grammar, under ids no other family uses.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from suite.families import family
from suite.families import _reasoning_core as rc
from suite.families.genesis import RESULT_STR
from suite.tasks import Task

REGEX_N = 12
CFG_N = 12
"""Instances pinned per generator."""

SLACK = {"reasoning-core": 1, "reasoning-core-strict": 0}
"""Calls a family's budgets leave beyond the one verification call a knowing policy needs."""

KNOWING = {"shell": 1}
"""The floor the economy scorers grade against: a policy that knows the answer verifies it once."""

SOURCE = (f"sileod/reasoning-core ({rc.LICENSE}, rev {rc.REVISION[:7]}, v{rc.VERSION}, {rc.PAPER}); "
          "regex-following and cfg-generation instances graded by the generator's own checker "
          "(regex.fullmatch; NLTK Earley membership)")


def _budget(n: int) -> str:
    return f"You have a budget of {n} shell call{'s' if n != 1 else ''}."


def _regex_prompt(pattern: str, budget: int) -> str:
    return ("Produce a string that fully matches this regular expression, then return it as result. "
            "The string must be non-empty, printable ASCII, and contain no whitespace.\n\n"
            f"    {pattern}\n\n"
            "Check a candidate with the shell tool before you answer — for example "
            "`python3 -c \"import re,sys; print(bool(re.fullmatch(sys.argv[1], sys.argv[2])))\" <pattern> <candidate>`. "
            f"{_budget(budget)}")


def _cfg_prompt(grammar: str, start: str, min_tokens: int, budget: int) -> str:
    return (f"The following context-free grammar has start symbol {start}:\n\n{grammar}\n\n"
            f"Return as result a string of at least {min_tokens} space-separated tokens that the grammar derives — a "
            "member of its language. Every token must be a terminal of the grammar; terminals are shown quoted in the "
            "rules, so write them unquoted and separated by single spaces. "
            "Check membership with the shell tool before you answer (Python's NLTK is available: "
            "`nltk.CFG.fromstring`, then `nltk.parse.earleychart.EarleyChartParser`). "
            f"{_budget(budget)}")


def _task(record: dict[str, Any], fam: str) -> Task:
    slack = SLACK[fam]
    budget = KNOWING["shell"] + slack
    tid = f"{fam}/{record['id']}"
    if record["kind"] == "regex-following":
        pattern = record["pattern"]
        return Task(tid, _regex_prompt(pattern, budget), ("shell-tool", "tool-budget"), RESULT_STR,
                    lambda result, w, p=pattern: rc.regex_ok(p, result),
                    shell_budget=budget, knowing=dict(KNOWING))
    grammar, start, min_tokens = record["grammar"], record["start"], record["min_tokens"]
    return Task(tid, _cfg_prompt(grammar, start, min_tokens, budget), ("shell-tool", "tool-budget"), RESULT_STR,
                lambda result, w, g=grammar, s=start, m=min_tokens: rc.cfg_ok(g, s, m, result),
                shell_budget=budget, knowing=dict(KNOWING))


def fetch(n: int) -> list[dict[str, Any]]:
    """Transcribe the pinned instances: at most ``n`` of each generator, seeded and reproducible against the pinned revision."""
    return rc.records(min(n, REGEX_N), min(n, CFG_N))


@family("reasoning-core", source=SOURCE + "; budgeted with one call to spare", fetch=fetch)
def tasks() -> list[Task]:
    from suite.families import FAMILIES

    return [_task(r, "reasoning-core") for r in FAMILIES["reasoning-core"].records()]


@family("reasoning-core-strict", source=SOURCE + "; the same instances, budgeted at exactly the knowing policy's one call")
def strict_tasks() -> list[Task]:
    from suite.families import FAMILIES

    return [_task(r, "reasoning-core-strict") for r in FAMILIES["reasoning-core"].records()]
