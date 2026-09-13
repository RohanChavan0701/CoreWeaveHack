"""The admitting commit, derived from git history: a commit cannot carry its own hash, so the anchor
is the oldest commit whose message names the id — including the range the genesis message writes."""

from __future__ import annotations

import pytest

from hgi import registry as _registry
from hgi.genesis import seed
from hgi.store import Store, admitting_commit, commits_naming, git, ids_named
from tests.conftest import NOW, adjudicator, adjudicated_entry, draft


@pytest.fixture
def repo(tmp_path):
    """A seeded store inside a fresh git repository, with the genesis commit already made."""
    root = tmp_path / "store"
    reg = seed(root, model_id="stub", now=NOW)
    token = _registry.use(reg)
    git("init", "-q", cwd=tmp_path)
    git("config", "user.email", "committer@example.invalid", cwd=tmp_path)
    git("config", "user.name", "the committer", cwd=tmp_path)
    store = Store(root, registry=reg)
    _commit(store, "Genesis: seed the registry and the constitution C-0001..C-0007")
    yield store
    _registry.reset(token)


def _commit(store: Store, message: str) -> None:
    git("add", "-A", str(store.root.resolve()), cwd=store.root.parent)
    git("commit", "-q", "-m", message, cwd=store.root.parent)


def _commit_touching(store: Store, message: str) -> None:
    """A later commit; it must touch the store to appear in a log scoped to the store root."""
    (store.root / "index" / "note.txt").write_text(message)
    _commit(store, message)


def _admit(store: Store) -> str:
    d = draft(store)
    store.write_draft(d)
    entry = adjudicated_entry(store, d.uid)
    entry.verdict = "admit"
    return store.admit(d, entry, adjudicator()).id


def test_a_range_names_every_id_it_spans():
    assert ids_named("Consolidate K-0002 after pass 4: admitted D-0003, flipped D-0001") == {"K-0002", "D-0003", "D-0001"}
    assert ids_named("Genesis: seed the registry and the constitution C-0001..C-0007") == {f"C-{n:04d}" for n in range(1, 8)}
    assert ids_named("Regenerate projections") == set()


def test_the_admitting_commit_is_the_oldest_naming_the_id(repo):
    id = _admit(repo)
    _commit(repo, f"Consolidate K-0001 after pass 2: admitted {id}")
    _commit_touching(repo, f"Consolidate K-0002 after pass 4: admitted D-0002, flipped {id}")
    at = admitting_commit(repo, id)
    assert at is not None and at["subject"] == f"Consolidate K-0001 after pass 2: admitted {id}"
    assert [c["subject"] for c in commits_naming(repo, id)][0].startswith("Consolidate K-0002")


def test_the_genesis_range_anchors_an_article(repo):
    at = admitting_commit(repo, "C-0003")
    assert at is not None and at["subject"].startswith("Genesis:")


def test_an_uncommitted_record_has_no_admitting_commit(repo):
    assert admitting_commit(repo, _admit(repo)) is None


def test_a_store_outside_a_repository_has_no_admitting_commit(tmp_path):
    root = tmp_path / "store"
    reg = seed(root, model_id="stub", now=NOW)
    token = _registry.use(reg)
    assert admitting_commit(Store(root, registry=reg), "C-0001") is None
    _registry.reset(token)

