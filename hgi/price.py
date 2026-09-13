"""Re-pricing: moving a record's ``priced_for`` to the model the store now runs on.

Every record carrying authored conditioning text — a lens's angle, a
constitution article, a decision's sentence — records the frozen model it was
authored against (spec § 6, § 9.6). A model swap re-prices all of them in both
directions: text written to condition one model does not condition another,
and swapping back does not restore what the first swap cost.

Re-pricing has two halves and this module does one of them. Re-authoring the
text against the new model is authoring work, done by a model or a hand, and
nothing here does it. Moving the stamp is mechanical, and ``hgi price
--restamp`` does it without claiming the other half: a restamped record keeps
``priced_for.authored_for`` at the model its text was really written against,
so ``model-pricing`` goes on warning until the text is replaced. Without that
field the stamp would launder the swap — a store priced for a model it was
never authored for, and a green floor saying so.

    hgi price                            # the size of the swap to $HGI_MODEL_ID
    hgi price --model <id>               # the size of the swap to that model
    hgi price --model <id> --restamp     # move the stamp; keep what authored it

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


def restamp(store: Store, model_id: str) -> list[dict[str, Any]]:
    """Move the stamp on every conditioning record not already priced for ``model_id``; return the rows that moved.

    A lens lives in the registry and is rewritten there; an article and a
    decision are frozen records, and pricing is the one field on them that is
    not evidence — it names the reader the text was written for, not what was
    observed — so it is corrected in place rather than by a successor record.
    """
    moved, lenses = [], []
    for kind, record in store.conditioning():
        if record.priced_for.model_id == model_id:
            continue
        pricing = _restamped(record.priced_for, model_id)
        if kind == "lens":
            lenses.append((record.id, pricing))
        else:
            data = dump(record) | {"priced_for": pricing}
            store.write(store.parse(kind, data))
        moved.append({"kind": kind, "id": record.id, "priced_for": model_id, "authored_for": pricing["authored_for"]})
    if lenses:
        pricings = dict(lenses)
        path = store.registry.path("lenses")
        write_json(path, [item | {"priced_for": pricings[item["id"]]} if item["id"] in pricings else item
                          for item in read_json(path)])
    return moved


def report(store: Store, model_id: str, moved: list[dict[str, Any]] | None = None) -> str:
    """The size of the swap to ``model_id``, or what a restamp moved when ``moved`` is given."""
    all_rows = rows(store, model_id)
    listed = moved if moved is not None else [r for r in all_rows if not r["matches"]]
    done = moved is not None
    lines = [f"{'restamped' if done else 'to re-price'} for {model_id}: "
             f"{len(listed)} of {len(all_rows)} conditioning records"]
    lines += [f"  {r['kind']:<12} {r['id']:<8} "
              + (f"authored for {r['authored_for'] or model_id}" if done else f"priced for {r['priced_for'] or 'nothing'}")
              for r in listed]
    if not listed:
        return lines[0]
    if not done:
        lines.append("re-pricing is re-authoring the text against the model; --restamp moves the stamp alone, "
                     "and model-pricing goes on warning until the text follows")
    elif any(r["authored_for"] for r in listed):
        lines.append("their text has not moved with the stamp; model-pricing warns on each until it is replaced")
    else:
        lines.append("the stamp and the text agree, so model-pricing is quiet on them")
    return "\n".join(lines)


def register(add, store_of, finish) -> None:
    p = add("price", "the size of a model swap over the conditioning records, and the stamp")
    p.add_argument("--model", help="the model to price for (default: $HGI_MODEL_ID)")
    p.add_argument("--restamp", action="store_true", help="move the stamp, keeping what the text was authored for")
    p.set_defaults(fn=lambda args: _cmd(args, store_of, finish))


def _cmd(args, store_of, finish) -> int:
    model_id = args.model or os.environ.get("HGI_MODEL_ID")
    if not model_id:
        print("name the model with --model, or set $HGI_MODEL_ID")
        return 1
    store = store_of(args)
    if not args.restamp:
        print(report(store, model_id))
        return 0
    moved = restamp(store, model_id)
    print(report(store, model_id, moved))
    if moved:
        finish(store, args, f"Re-price {len(moved)} conditioning records for {model_id}")
    return 0
