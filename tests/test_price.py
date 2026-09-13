"""Re-pricing: the stamp moves for a model swap, what authored the text does not, and the floor
goes on warning until the text is re-authored — which ``--reauthor`` mechanizes so the text follows."""

from __future__ import annotations

import pytest

from hgi import lint as _lint
from hgi import model as _model
from hgi import price as _price
from hgi import registry as _registry
from hgi.cli import main
from hgi.genesis import seed
from hgi.store import Store
from tests.conftest import NOW, adjudicator, adjudicated_entry, draft


def _admit(store) -> str:
    d = draft(store)
    store.write_draft(d)
    entry = adjudicated_entry(store, d.uid)
    entry.verdict = "admit"
    return store.admit(d, entry, adjudicator()).id


def test_conditioning_is_every_lens_article_and_accepted_decision(store):
    _admit(store)
    kinds = [kind for kind, _ in store.conditioning()]
    assert kinds.count("lens") == len(store.registry.lenses())
    assert kinds.count("constitution") == len(store.articles())
    assert kinds.count("decision") == 1
    assert all(r["priced_for"] == "stub" for r in _price.rows(store, "m-2"))


def test_the_floor_is_quiet_on_the_model_the_store_is_priced_for(store):
    assert not _lint.check_pricing(store, "stub")
    assert not _lint.check_pricing(store, None)
    assert len(_lint.check_pricing(store, "m-2")) == len(store.conditioning())


def test_a_restamp_moves_the_stamp_and_keeps_what_authored_the_text(store):
    _admit(store)
    moved = _price.restamp(store, "m-2")
    assert len(moved) == len(store.conditioning())
    assert {r["authored_for"] for r in moved} == {"stub"}
    reread = store.__class__(store.root)
    assert {kind for kind, r in reread.conditioning() if r.priced_for.model_id != "m-2"} == set()
    assert {r.priced_for.authored_for for _, r in reread.conditioning()} == {"stub"}


def test_a_restamp_does_not_buy_a_green_floor(store):
    _price.restamp(store, "m-2")
    findings = _lint.check_pricing(store, "m-2")
    assert len(findings) == len(store.conditioning())
    assert all("authored for 'stub'" in f.message for f in findings)
    assert all(f.level == "warn" for f in findings)


def test_swapping_back_restores_an_honest_stamp(store):
    _price.restamp(store, "m-2")
    _price.restamp(store, "stub")
    assert {r.priced_for.authored_for for _, r in store.conditioning()} == {None}
    assert not _lint.check_pricing(store, "stub")


def test_a_second_restamp_keeps_the_original_authoring(store):
    _price.restamp(store, "m-2")
    _price.restamp(store, "m-3")
    assert {r.priced_for.authored_for for _, r in store.conditioning()} == {"stub"}
    assert _price.restamp(store, "m-3") == []


@pytest.fixture
def stub():
    """The re-author role calls a model; offline the stub answers it. Install it as the default so no endpoint is reached."""
    _model.use(_model.Stub())
    yield
    _model.reset()


def _text(kind, record) -> tuple[str, ...]:
    return tuple(getattr(record, f) for f in _price.AUTHORED_TEXT[kind])


def test_a_reauthor_moves_the_text_and_agrees_the_stamp_with_authoring(store, stub):
    _admit(store)
    before = {(k, r.id): _text(k, r) for k, r in store.conditioning()}
    moved = _price.reauthor(store, "m-2")
    assert len(moved) == len(store.conditioning())
    assert {r["authored_for"] for r in moved} == {None}
    reread = store.__class__(store.root)
    assert {r.priced_for.model_id for _, r in reread.conditioning()} == {"m-2"}
    assert {r.priced_for.authored_for for _, r in reread.conditioning()} == {None}
    after = {(k, r.id): _text(k, r) for k, r in reread.conditioning()}
    assert all(after[key] != before[key] for key in before)  # every conditioning field followed the model


def test_a_reauthor_buys_a_green_floor(store, stub):
    _admit(store)
    _price.reauthor(store, "m-2")
    assert not _lint.check_pricing(store, "m-2")  # the text followed the stamp, so model-pricing is quiet


def test_a_restamp_leaves_the_warning_and_a_reauthor_then_clears_it(store, stub):
    _admit(store)
    _price.restamp(store, "m-2")
    assert len(_lint.check_pricing(store, "m-2")) == len(store.conditioning())  # stamp-only: the warning stands
    moved = _price.reauthor(store, "m-2")
    assert len(moved) == len(store.conditioning())  # every restamped record still owes its text
    assert not _lint.check_pricing(store, "m-2")  # now the text has followed


def test_a_reauthor_leaves_alone_what_is_already_authored(store, stub):
    _admit(store)
    _price.reauthor(store, "m-2")
    assert _price.reauthor(store, "m-2") == []  # stamp and authoring already agree; nothing to move


def test_the_cli_reauthor_path_clears_the_warning(store, stub, monkeypatch, capsys):
    monkeypatch.setenv("HGI_ENV_FILE", str(store.root / "no-env-file"))
    assert main(["--store", str(store.root), "price", "--model", "m-2", "--reauthor", "--no-commit"]) == 0
    assert "re-authored for m-2" in capsys.readouterr().out
    assert not _lint.check_pricing(store.__class__(store.root), "m-2")


def test_restamp_and_reauthor_are_mutually_exclusive(store, capsys):
    assert main(["--store", str(store.root), "price", "--model", "m-2", "--restamp", "--reauthor", "--no-commit"]) == 1
    assert "choose one" in capsys.readouterr().out


def test_an_unpriced_record_is_priced_rather_than_re_priced(tmp_path):
    """A seed with no ``$HGI_MODEL_ID`` claims no model, so a stamp erases no authoring and the floor stays quiet."""
    root = tmp_path / "store"
    reg = seed(root, model_id=None, now=NOW)
    token = _registry.use(reg)
    unpriced = Store(root, registry=reg)
    assert {r.priced_for.model_id for _, r in unpriced.conditioning()} == {None}
    assert {r["authored_for"] for r in _price.restamp(unpriced, "m-2")} == {None}
    assert not _lint.check_pricing(unpriced, "m-2")
    _registry.reset(token)
