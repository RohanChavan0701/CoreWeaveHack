"""The blind coder shapes on the convention, not the tool (addressing decision 77's deeper reading).

The shape-radius sweep found the coder's shapes too generic: one tool-major term (`http-tool`) covered three
distinct lessons (moved-v2, paged-api, token-route), so even exact-match grouping put two lessons in one cluster and
no radius could recover the precision the join never had. The fix is the coding, not the radius: the coder now shapes
an observation on the world-convention its noticing names, so two misses of one convention share a shape and two of
different conventions differ even when both called the same tool. These tests pin that behavior and prove the coder
is still blind — the coding request it receives carries the noticing and nothing of the task's held-out lesson label.
"""

from __future__ import annotations

import json

from hgi import coder as _coder
from hgi import roles


# --- the convention vocabulary is registered ---------------------------------------------------

def test_the_axes_are_split_work_shape_hooks_convention_grouping(store):
    work_shape = set(store.registry.terms("work-shape"))
    convention = set(store.registry.terms("convention"))
    # the tool-major cues stay on work-shape — the boot classify keys hooks on them
    assert {"http-tool", "shell-tool", "tool-budget"} <= work_shape
    # the convention-major shapes the coder groups observations by live on the separate convention axis, not work-shape
    assert {"route-versioned", "listing-paged", "route-guarded", "field-quoted",
            "summary-row", "line-unterminated", "byte-order-mark", "schema-coded-value"} <= convention
    assert not (convention & work_shape), "the two axes share no term: grouping and hooks are separated (item 57)"


# --- one tool, two conventions, two shapes -----------------------------------------------------

def _code(store, observations):
    coded, _ = _coder.code(observations, store.registry.terms("convention"), session="K-test", records_in_context=[])
    return coded


def test_two_http_misses_of_different_conventions_get_different_shapes(store):
    """The conflation decision 77 measured: both call the HTTP tool, so the tool cue gave them one shape; the
    convention cue separates them."""
    coded = _code(store, [
        {"name": "o-moved", "noticed": "in task fetch_user the route answered 410 Gone and named its successor under /v2; the attempt did not follow the versioned route"},
        {"name": "o-token", "noticed": "in task list_secure the route answered 401 unauthorized; the attempt sent no token, and the secure route wanted the token authorized on the query"},
    ])
    assert coded["o-moved"] == ["route-versioned"]
    assert coded["o-token"] == ["route-guarded"]
    assert coded["o-moved"] != coded["o-token"]


def test_two_text2sql_misses_over_one_schema_share_the_schema_convention_shape(store):
    """The text-to-SQL family's transfer story: distinct schema quirks of one fixed database are one convention, so a
    coded-status miss and a text-date miss share a shape and a decision hooked on it can carry the whole schema."""
    coded = _code(store, [
        {"name": "o-status", "noticed": "task q117 filtered loans on the word 'paid' but the status is a coded value stored as a single-letter code A/B/C/D, so the query matched nothing"},
        {"name": "o-date", "noticed": "task q99 called a date function on the account date, but the date is text and needs strftime to read its year"},
    ])
    assert coded["o-status"] == coded["o-date"] == ["schema-coded-value"]


DECOY_SHAPES = {"pool-exhausted", "dependency-stalled", "release-regressed"}


def test_the_three_incident_world_facts_get_three_shapes(store):
    """The incidents family's transfer story: the decoy is the loud reading, so the shape must be the world-fact the
    bundle actually turned on. A saturated pool the world caused itself, a pool filled by a stalled dependency, and a
    spike that started at a deploy are three conventions, not one 'slow database' — a record admitted on the first
    fires on the second and must be set aside there, which only holds if the three code apart."""
    coded = _code(store, [
        {"name": "o-pool", "noticed": "in task tenant-slow the pool readings showed every backend busy and callers waiting for a connection under the tenant's own load; the attempt answered before reading them"},
        {"name": "o-dependency", "noticed": "in task checkout-latency the queries themselves ran fast but the backends sat idle in transaction while the third-party provider held the caller's connections open through the slow dependency; the attempt read the filling pool as the fault"},
        {"name": "o-release", "noticed": "in task orders-5xx the error rate stepped up at 14:02 exactly when the new version rolled out, the payload samples unchanged; the attempt read the samples and never opened the release history"},
    ])
    assert coded["o-pool"] == ["pool-exhausted"]
    assert coded["o-dependency"] == ["dependency-stalled"]
    assert coded["o-release"] == ["release-regressed"]
    assert len({tuple(coded[o]) for o in ("o-pool", "o-dependency", "o-release")}) == 3


def test_a_noticing_about_the_loop_names_no_incident_world_fact(store):
    """Loop talk is not a world-fact: a noticing about how the attempt used its own store names nothing the world did,
    so none of the three decoy shapes may claim it — that is what keeps the shapes about the incident."""
    coded = _code(store, [
        {"name": "o-loop", "noticed": "in task tenant-slow the attempt did not consult the detection record it was given in context before it answered"},
    ])
    assert not (DECOY_SHAPES & set(coded["o-loop"]))


def test_two_misses_of_one_convention_share_a_shape_across_wordings(store):
    """Different clothes, one convention: the shapes must be equal so exact-match grouping joins them."""
    coded = _code(store, [
        {"name": "o-a", "noticed": "task count_people made a shell call but the last line carried no trailing newline, so wc -l counted one fewer"},
        {"name": "o-b", "noticed": "task tally_rows read the file whose final row is left without a newline; the count came up short by one"},
    ])
    assert coded["o-a"] == coded["o-b"] == ["line-unterminated"]


def test_a_shell_footer_and_a_shell_newline_do_not_share_a_shape(store):
    """`shell-tool` covered {csv-quoted, footer-row, trailing-newline}; the convention cue splits them."""
    coded = _code(store, [
        {"name": "o-footer", "noticed": "task sum_sales counted the rows of the export but its last line is a TOTAL summary row that is not a record"},
        {"name": "o-newline", "noticed": "task count_lines missed one line because the file has no terminating newline on its last line"},
    ])
    assert coded["o-footer"] == ["summary-row"]
    assert coded["o-newline"] == ["line-unterminated"]
    assert coded["o-footer"] != coded["o-newline"]  # the shell tool no longer collapses them into one shape


def test_a_way_of_working_with_no_convention_escapes_on_the_convention_axis(store):
    """A budget miss turns on the way of working itself, not a world-convention — the convention axis has no term for it,
    so it escapes rather than borrowing a tool term (which now lives only on the separate work-shape hook axis)."""
    coded = _code(store, [
        {"name": "o-budget", "noticed": "task fan_out exceeded its shell budget: independent calls were issued one per input instead of batched"},
    ])
    shape = coded["o-budget"]
    assert all(t.startswith("other(") for t in shape)  # no convention covers a bare way of working; it escapes
    conventions = {"route-versioned", "listing-paged", "route-guarded", "field-quoted", "summary-row", "line-unterminated", "byte-order-mark"}
    assert not (conventions & set(shape))


def test_a_convention_the_vocabulary_lacks_escapes_rather_than_borrowing_a_tool_term(store):
    coded = _code(store, [
        {"name": "o-locale", "noticed": "task parse_amount read the decimal comma of a European locale as a thousands separator, off by a factor the world's number format explains"},
    ])
    (shape,) = [coded["o-locale"]]
    assert shape == ["other(unclassified)"] or all(t.startswith("other(") for t in shape)
    assert "shell-tool" not in shape and "http-tool" not in shape


# --- the coder is blind: no held-out label reaches it ------------------------------------------

def test_the_coding_request_carries_the_noticing_and_no_lesson_label(store):
    """Leakage guard: the request the coder answers holds only the observation name and its noticing (plus the flat
    term list) — never the task id, the declared lesson, or a score. The convention terms align with the scoring
    lessons because both enumerate the same world-conventions, but the coder infers the term from the noticing prose,
    it is never handed the answer."""
    from hgi.contract import BUILDERS

    from hgi.store import now
    from hgi.types import Observation

    store.write(Observation(uid=store.new_uid(), name="O-0001", noticed_at=now(), session="S-0001",
                            happened="the route answered 410 and named its /v2 successor", anchor={"call": "weave:///t/c"}))
    role, payload = BUILDERS["coding"](store, None)  # the coding builder assembles the request the coder answers
    obj = json.loads(payload)
    assert role == "coder" and obj["request"] == "coding"
    leaks = {"lesson", "task", "label", "score", "scores", "gold", "answer"}
    for o in obj["observations"]:
        assert set(o) == {"name", "noticed"}, f"an observation carried more than its name and noticing: {set(o)}"
        assert not (leaks & set(o))
    # the whole request object names no lesson channel either
    assert not (leaks & set(obj))
