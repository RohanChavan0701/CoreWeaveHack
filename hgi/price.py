"""Re-pricing: moving a record's ``priced_for`` to the model the store now runs on.

Every record carrying authored conditioning text — a lens's angle, a
constitution article, a decision's sentence — records the frozen model it was
authored against (spec § 6, § 9.6). A model swap re-prices all of them in both
directions: text written to condition one model does not condition another,
and swapping back does not restore what the first swap cost.

Re-pricing has two halves. Moving the stamp is mechanical, and ``hgi price
--restamp`` does it without claiming the other half: a restamped record keeps
``priced_for.authored_for`` at the model its text was really written against,
so ``model-pricing`` goes on warning until the text is replaced. Without that
field the stamp would launder the swap — a store priced for a model it was
never authored for, and a green floor saying so.

Re-authoring the text against the new model is the other half, and ``hgi price
--reauthor`` does it: the ``reauthor`` role rewrites each conditioning field to
condition the new model, and the record is stamped with the text and the
authoring agreeing (``authored_for`` null), so ``model-pricing`` is quiet
because the text actually followed the stamp. It calls a model — the stub
offline, an endpoint live — where ``--restamp`` calls none.

    hgi price                            # the size of the swap to $HGI_MODEL_ID
    hgi price --model <id>               # the size of the swap to that model
    hgi price --model <id> --restamp     # move the stamp; keep what authored it
    hgi price --model <id> --reauthor    # re-author the text, then move both

An unpriced record — ``priced_for.model_id`` null, which is what ``hgi
genesis`` writes with no ``$HGI_MODEL_ID`` — is priced rather than re-priced:
it made no claim about which model its text conditions, so there is none to
keep, and it restamps with ``authored_for`` still null. That makes ``hgi price
--restamp`` the non-destructive equivalent of ``HGI_MODEL_ID=<id> hgi genesis
--force``, which prices a seed by writing it fresh and resets the store with
it.
"""

from __future__ import annotations

import os
from typing import Any

from hgi.registry import read_json, write_json
from hgi.store import Store, dump

AUTHORED_TEXT: dict[str, tuple[str, ...]] = {
    "lens": ("angle", "counterfactual"),
    "constitution": ("article", "counterfactual"),
    "decision": ("decision", "counterfactual"),
}
"""The conditioning text of each kind: the fields a model reads as written for it, and the ``reauthor`` role rewrites."""


def rows(store: Store, model_id: str) -> list[dict[str, Any]]:
    """Every conditioning record: what it is priced for, what authored its text, and whether the swap leaves it alone."""
    out = []
    for kind, record in store.conditioning():
        priced = record.priced_for
        out.append({"kind": kind, "id": record.id, "priced_for": priced.model_id,
                    "authored_for": priced.authored_for or priced.model_id,
                    "matches": priced.model_id == model_id})
    return out


def _restamped(priced: Any, model_id: str) -> dict[str, str | None]:
    """The new pricing: the stamp moves, and what authored the text is kept unless the swap goes back to it."""
    authored = priced.authored_for or priced.model_id
    return {"model_id": model_id, "authored_for": None if authored == model_id else authored}


def _write_lenses(store: Store, patches: dict[str, dict[str, Any]]) -> None:
    """Merge a per-lens patch into the lens register in place; a lens not named is left as it stands."""
    path = store.registry.path("lenses")
    write_json(path, [item | patches[item["id"]] if item["id"] in patches else item for item in read_json(path)])


def _apply(store: Store, kind: str, record: Any, patch: dict[str, Any], lenses: list[tuple[str, dict[str, Any]]]) -> None:
    """Write ``patch`` onto a record: a lens is deferred to a batch registry rewrite, an article or decision is
    corrected in place — pricing and conditioning text are the fields a re-price touches, and a successor record
    would carry the same warrant for a text-only change."""
    if kind == "lens":
        lenses.append((record.id, patch))
    else:
        store.write(store.parse(kind, dump(record) | patch))


def restamp(store: Store, model_id: str) -> list[dict[str, Any]]:
    """Move the stamp on every conditioning record not already priced for ``model_id``; return the rows that moved."""
    moved, lenses = [], []
    for kind, record in store.conditioning():
        if record.priced_for.model_id == model_id:
            continue
        pricing = _restamped(record.priced_for, model_id)
        _apply(store, kind, record, {"priced_for": pricing}, lenses)
        moved.append({"kind": kind, "id": record.id, "priced_for": model_id, "authored_for": pricing["authored_for"]})
    if lenses:
        _write_lenses(store, dict(lenses))
    return moved


def _needs_authoring(priced: Any, model_id: str) -> bool:
    """True when the text is not already authored for ``model_id``: priced for another model, or restamped and not yet followed."""
    return priced.model_id != model_id or priced.authored_for is not None


def _rewrite(kind: str, record: Any, model_id: str) -> dict[str, str]:
    """The record's conditioning fields, re-authored for ``model_id`` by the role; a field the role leaves out keeps its text."""
    from hgi import model as _model, roles

    fields = {f: getattr(record, f) for f in AUTHORED_TEXT[kind]}
    priced = record.priced_for
    payload = roles.request("reauthor", kind=kind, id=record.id,
                            was_authored_for=priced.authored_for or priced.model_id, model_id=model_id, text=fields)
    out = _model.complete("reauthor", payload).json()
    rewritten = out.get("text", {}) if isinstance(out, dict) else {}
    return {f: str(rewritten[f]) if isinstance(rewritten.get(f), str) else fields[f] for f in fields}


def reauthor(store: Store, model_id: str) -> list[dict[str, Any]]:
    """Re-author the text of every conditioning record not already authored for ``model_id``, then stamp the text and the
    authoring together, so ``model-pricing`` is quiet because the text followed the model — which a restamp does not do.

    Return the rows that moved. The role's live output requires a real model; offline, the stub answers in the role's
    reply shape and the mechanism runs the same.
    """
    moved, lenses = [], []
    for kind, record in store.conditioning():
        if not _needs_authoring(record.priced_for, model_id):
            continue
        patch = _rewrite(kind, record, model_id) | {"priced_for": {"model_id": model_id, "authored_for": None}}
        _apply(store, kind, record, patch, lenses)
        moved.append({"kind": kind, "id": record.id, "priced_for": model_id, "authored_for": None})
    if lenses:
        _write_lenses(store, dict(lenses))
    return moved


def report(store: Store, model_id: str, moved: list[dict[str, Any]] | None = None, *, verb: str = "restamped") -> str:
    """The size of the swap to ``model_id``, or what a run moved when ``moved`` is given (``verb`` names the run)."""
    all_rows = rows(store, model_id)
    listed = moved if moved is not None else [r for r in all_rows if not r["matches"]]
    done = moved is not None
    lines = [f"{verb if done else 'to re-price'} for {model_id}: "
             f"{len(listed)} of {len(all_rows)} conditioning records"]
    lines += [f"  {r['kind']:<12} {r['id']:<8} "
              + (f"authored for {r['authored_for'] or model_id}" if done else f"priced for {r['priced_for'] or 'nothing'}")
              for r in listed]
    if not listed:
        return lines[0]
    if not done:
        lines.append("re-pricing is re-authoring the text against the model; --restamp moves the stamp alone and leaves "
                     "model-pricing warning until the text follows, --reauthor moves the text with it")
    elif any(r["authored_for"] for r in listed):
        lines.append("their text has not moved with the stamp; model-pricing warns on each until it is replaced")
    else:
        lines.append("their text was re-authored with the stamp, so model-pricing is quiet on them")
    return "\n".join(lines)


def register(add, store_of, finish) -> None:
    p = add("price", "the size of a model swap over the conditioning records, and the stamp")
    p.add_argument("--model", help="the model to price for (default: $HGI_MODEL_ID)")
    p.add_argument("--restamp", action="store_true", help="move the stamp, keeping what the text was authored for")
    p.add_argument("--reauthor", action="store_true", help="re-author the text for the model, then move the stamp with it")
    p.set_defaults(fn=lambda args: _cmd(args, store_of, finish))


def _cmd(args, store_of, finish) -> int:
    model_id = args.model or os.environ.get("HGI_MODEL_ID")
    if not model_id:
        print("name the model with --model, or set $HGI_MODEL_ID")
        return 1
    if args.restamp and args.reauthor:
        print("--restamp moves the stamp alone and --reauthor moves the text with it; choose one")
        return 1
    store = store_of(args)
    if not (args.restamp or args.reauthor):
        print(report(store, model_id))
        return 0
    if args.reauthor:
        moved = reauthor(store, model_id)
        print(report(store, model_id, moved, verb="re-authored"))
        message = f"Re-author {len(moved)} conditioning records for {model_id}"
    else:
        moved = restamp(store, model_id)
        print(report(store, model_id, moved))
        message = f"Re-price {len(moved)} conditioning records for {model_id}"
    if moved:
        finish(store, args, message)
    return 0
