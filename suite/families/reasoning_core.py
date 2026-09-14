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

Each difficulty tier is pinned into its own file — the moderate tier into
``suite/data/reasoning-core.jsonl``, the harder tier into
``suite/data/reasoning-core-hard.jsonl`` — at that tier's per-generator level
(Reasoning Core's integer ``level`` knob) and a stored seed each, so a run
needs neither the network nor the generation stack and the suite hash is
stable. The tier is a config value (:class:`suite.families._reasoning_core.Tier`),
so a harder tier is a data change, not a fork of the generation code. The
pinned record carries the presentation and the checker's inputs — the regex, or
the grammar and its start symbol and length floor — never a witness, so the
file cannot leak an answer. :mod:`suite.families._reasoning_core` holds the
checkers, the tiers and the seeded generator, and the ``source`` string pins
the revision and license.

Four families are built, a lax/strict pair per tier, differing only in slack,
as ``curriculum`` and ``curriculum-strict`` do. Within a tier the lax family
(``reasoning-core``, ``reasoning-core-hard``) budgets each task at the knowing
policy's one verification call plus one, so a pass may spend a call iterating on
a candidate; the strict family (``reasoning-core-strict``,
``reasoning-core-hard-strict``) budgets at exactly that one call, so a wrong
first candidate cannot be repaired within budget. The ``-hard`` pair draws from
the harder tier: deeper-nested patterns and larger grammars with longer members,
generated on seed bases disjoint from the moderate tier so the two tiers share
no instance. The strict twin of a tier shares that tier's instances. All
instances are disjoint from every other family's — a regex or a grammar, under
ids no other family uses.

Because a witness — a matching string, a grammar member — is something the
actor can often produce unaided, the hidden check grades the answer and the
answer would pass whether or not the call budget was respected; the budget
would then reach only the economy series and never pass or fail a row, and the
strict pool would not bite. So the check gates on the budget: the tool layer
marks a working directory over budget when it refuses a call past the pool's
limit (:data:`suite.tools.BUDGET_SENTINEL`), and a marked row fails
``task_pass_rate`` regardless of the answer, the way ``curriculum`` fails in
effect because its answer needs the call. The gate is on by default and is
lifted by setting :data:`BUDGET_GATE_ENV` to ``0``, which restores answer-only
grading. Each pool gates at its own budget: the strict pool fails the moment a
second call is refused, the lax pool only when the repair call's successor is.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable

from suite.families import family
from suite.families import _reasoning_core as rc
from suite.families.genesis import RESULT_STR
from suite.tasks import Check, Task
from suite.tools import BUDGET_SENTINEL

REGEX_N = 12
CFG_N = 12
"""Instances pinned per generator."""

SLACK = {"reasoning-core": 1, "reasoning-core-strict": 0,
         "reasoning-core-hard": 1, "reasoning-core-hard-strict": 0}
"""Calls a family's budgets leave beyond the one verification call a knowing policy needs; a tier's lax/strict pair carry the same slack as the moderate pair."""

KNOWING = {"shell": 1}
"""The floor the economy scorers grade against: a policy that knows the answer verifies it once."""

BUDGET_GATE_ENV = "HGI_REASONING_CORE_BUDGET_GATE"
"""The environment flag that lifts the budget gate: set it to ``0`` to grade the answer alone (the pre-gate behaviour)."""


def _budget_gates_pass() -> bool:
    """Whether an over-budget row fails ``task_pass_rate``. On by default; ``HGI_REASONING_CORE_BUDGET_GATE=0`` lifts it."""
    return os.environ.get(BUDGET_GATE_ENV, "1") != "0"


def _gated(answer_ok: Callable[[Any], bool]) -> Check:
    """Wrap a bare answer check so a row the tool layer marked over budget fails, unless the gate is lifted."""

    def check(result: Any, workdir: Path) -> bool:
        if _budget_gates_pass() and (Path(workdir) / BUDGET_SENTINEL).exists():
            return False
        return answer_ok(result)

    return check

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
                    _gated(lambda result, p=pattern: rc.regex_ok(p, result)),
                    shell_budget=budget, knowing=dict(KNOWING))
    grammar, start, min_tokens = record["grammar"], record["start"], record["min_tokens"]
    return Task(tid, _cfg_prompt(grammar, start, min_tokens, budget), ("shell-tool", "tool-budget"), RESULT_STR,
                _gated(lambda result, g=grammar, s=start, m=min_tokens: rc.cfg_ok(g, s, m, result)),
                shell_budget=budget, knowing=dict(KNOWING))


HARD_SOURCE = (f"sileod/reasoning-core ({rc.LICENSE}, rev {rc.REVISION[:7]}, v{rc.VERSION}, {rc.PAPER}); "
               "the harder tier — regex level 5, grammar level 3, ten-to-eighteen-token grammar members — "
               "graded by the generator's own checker (regex.fullmatch; NLTK Earley membership)")


def fetch(n: int) -> list[dict[str, Any]]:
    """Transcribe the pinned moderate instances: at most ``n`` of each generator, seeded and reproducible against the pinned revision."""
    return rc.records(min(n, REGEX_N), min(n, CFG_N), tier=rc.MODERATE)


def fetch_hard(n: int) -> list[dict[str, Any]]:
    """Transcribe the pinned harder instances (:data:`suite.families._reasoning_core.HARD`): at most ``n`` of each generator, seeded and reproducible against the pinned revision."""
    return rc.records(min(n, REGEX_N), min(n, CFG_N), tier=rc.HARD)


@family("reasoning-core", source=SOURCE + "; budgeted with one call to spare", fetch=fetch)
def tasks() -> list[Task]:
    from suite.families import FAMILIES

    return [_task(r, "reasoning-core") for r in FAMILIES["reasoning-core"].records()]


@family("reasoning-core-strict", source=SOURCE + "; the same instances, budgeted at exactly the knowing policy's one call")
def strict_tasks() -> list[Task]:
    from suite.families import FAMILIES

    return [_task(r, "reasoning-core-strict") for r in FAMILIES["reasoning-core"].records()]


@family("reasoning-core-hard", source=HARD_SOURCE + "; budgeted with one call to spare", fetch=fetch_hard)
def hard_tasks() -> list[Task]:
    from suite.families import FAMILIES

    return [_task(r, "reasoning-core-hard") for r in FAMILIES["reasoning-core-hard"].records()]


@family("reasoning-core-hard-strict", source=HARD_SOURCE + "; the same instances, budgeted at exactly the knowing policy's one call")
def hard_strict_tasks() -> list[Task]:
    from suite.families import FAMILIES

    return [_task(r, "reasoning-core-hard-strict") for r in FAMILIES["reasoning-core-hard"].records()]
