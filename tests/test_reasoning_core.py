"""The reasoning-core family, read offline from its pinned file: each instance is graded by the
generator's own checker — a regex match by ``regex.fullmatch``, a grammar string by NLTK membership —
never by a comparison against a stored answer, and the strict twin carries the same instances one call tighter."""

from __future__ import annotations

from suite.families import FAMILIES
from suite.families import _reasoning_core as rc
from suite.tasks import SuiteSpec, build

INSTANCES = 24
"""Pinned instances: twelve regex-following and twelve cfg-generation."""

REGEX_ID = "reasoning-core/regex_04"
"""One pinned regex task with hand-checkable matches: the pattern ``(?:((F)Y)+)``."""
REGEX_MATCHES = ("FY", "FYFY")
REGEX_NON_MATCHES = ("F", "FYF", "")

CFG_ID = "reasoning-core/cfg_00"
"""One pinned grammar task whose language a member can be written for by hand."""
CFG_MEMBER = "boy boy boy boy boy boy boy boy boy boy floor"  # eleven terminals; the grammar's `S -> 'boy' S` chain
# members of the language but under the token floor, then a string over the floor that the grammar does not derive
CFG_NON_MEMBERS = ("floor", "boy floor", "< floor >", "boy boy boy boy boy boy boy boy boy boy nope")


def _by_id(name: str):
    return {t.id: t for t in FAMILIES[name].tasks()}


def test_both_families_load_the_same_pinned_instances_one_call_apart():
    counts = {name: len(FAMILIES[name].tasks()) for name in ("reasoning-core", "reasoning-core-strict")}
    assert counts == {"reasoning-core": INSTANCES, "reasoning-core-strict": INSTANCES}
    for name, n in counts.items():
        assert len(_by_id(name)) == n, f"{name}: task ids are not unique"

    lax, strict = _by_id("reasoning-core"), _by_id("reasoning-core-strict")
    names = {i.split("/", 1)[1] for i in lax}
    assert names == {i.split("/", 1)[1] for i in strict}, "the strict twin carries the same instances"
    for short in names:
        lt, st = lax[f"reasoning-core/{short}"], strict[f"reasoning-core-strict/{short}"]
        assert lt.shapes == st.shapes == ("shell-tool", "tool-budget")
        assert lt.knowing == st.knowing == {"shell": 1}
        assert lt.shell_budget == 2 and st.shell_budget == 1, "lax leaves one call to spare; strict holds exactly the floor"

    world = build(SuiteSpec(families=["reasoning-core", "reasoning-core-strict"]))
    assert len(world.by_id) == 2 * INSTANCES and world.families() == counts


def test_the_pinned_file_carries_the_checker_inputs_and_no_witness():
    for r in FAMILIES["reasoning-core"].records():
        assert r["kind"] in ("regex-following", "cfg-generation")
        assert "witness" not in r and "answer" not in r and "string" not in r and "tokens" not in r
        if r["kind"] == "regex-following":
            assert set(r) == {"id", "kind", "level", "seed", "rc_task", "pattern", "witness_len"}
        else:
            assert set(r) == {"id", "kind", "level", "seed", "rc_task", "grammar", "start", "min_tokens"}


def test_a_regex_task_grades_by_full_match_not_by_a_stored_string(tmp_path):
    spec = _by_id("reasoning-core")[REGEX_ID]
    assert "fully matches" in spec.prompt and "budget of 2 shell calls" in spec.prompt
    for good in REGEX_MATCHES:  # two distinct strings both match — a membership verdict, not one gold string
        assert spec.check(good, tmp_path), f"{good!r} matches the pattern and must pass"
    for bad in REGEX_NON_MATCHES:
        assert not spec.check(bad, tmp_path), f"{bad!r} does not match and must fail"
    assert not spec.check("F Y", tmp_path), "a match with whitespace is not an admissible sample"
    assert not spec.check(42, tmp_path), "a non-string result never passes"


def test_a_cfg_task_grades_by_grammar_membership_over_the_token_floor(tmp_path):
    spec = _by_id("reasoning-core")[CFG_ID]
    record = next(r for r in FAMILIES["reasoning-core"].records() if f"reasoning-core/{r['id']}" == CFG_ID)
    assert record["start"] in spec.prompt and str(record["min_tokens"]) in spec.prompt
    assert spec.check(CFG_MEMBER, tmp_path), "a string the grammar derives at the token floor must pass"
    for bad in CFG_NON_MEMBERS:
        assert not spec.check(bad, tmp_path), f"{bad!r} is under the floor or not derivable and must fail"
    assert not spec.check(("< " * 200).strip(), tmp_path), "a string past the token cap is refused unparsed"
    assert not spec.check(7, tmp_path), "a non-string result never passes"


def test_the_regex_checker_is_reasoning_cores_full_match_verdict():
    assert rc.regex_ok(r"(?:((F)Y)+)", "FYFY") and not rc.regex_ok(r"(?:((F)Y)+)", "FYF")
    assert not rc.regex_ok(r"a(", "a")  # an invalid pattern is a failed task, not a raise from the grader
