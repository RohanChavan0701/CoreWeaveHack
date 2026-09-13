"""The common flags. ``--store`` and ``--no-commit`` are declared once and mean the same thing on
either side of the subcommand, because the root a caller names and the root a command writes to
cannot differ: an argparse default on a subparser overwrote the root named before the subcommand,
and ``hgi --store /elsewhere genesis --force`` reseeded ``./store``."""

from __future__ import annotations

import os

import pytest

from hgi import registry as _registry
from hgi.cli import _root, build_parser, main
from hgi.genesis import seed
from tests.conftest import NOW


@pytest.fixture(autouse=True)
def environment():
    """``$HGI_STORE`` is the fallback under test and ``main`` reads an env file; neither may leak into the next test."""
    before = dict(os.environ)
    token = _registry.use(None)
    yield
    _registry.reset(token)
    os.environ.clear()
    os.environ.update(before)


TAILS = [["genesis", "--force"], ["lint"], ["index"], ["lineage", "D-0001"],
         ["boot", "--pass", "1"], ["consolidate"], ["price", "--model", "stub"], ["consult"]]
"""One invocation a subcommand, each carrying whatever that subcommand requires."""


@pytest.mark.parametrize("tail", TAILS, ids=lambda tail: tail[0])
def test_the_store_flag_names_the_same_root_in_either_position(tail, tmp_path):
    named, parser = tmp_path / "named", build_parser()
    before = parser.parse_args(["--store", str(named), *tail])
    after = parser.parse_args([*tail, "--store", str(named)])
    assert _root(before) == _root(after) == named


@pytest.mark.parametrize("tail", TAILS, ids=lambda tail: tail[0])
def test_no_commit_holds_in_either_position(tail):
    parser = build_parser()
    assert parser.parse_args(["--no-commit", *tail]).no_commit
    assert parser.parse_args([*tail, "--no-commit"]).no_commit
    assert not parser.parse_args(tail).no_commit  # the default is to commit, and nothing else sets it


def test_an_unflagged_invocation_falls_back_to_the_environment(tmp_path, monkeypatch):
    monkeypatch.setenv("HGI_STORE", str(tmp_path / "from-the-environment"))
    assert _root(build_parser().parse_args(["index"])) == tmp_path / "from-the-environment"


def test_genesis_seeds_the_store_the_caller_named_and_leaves_the_default_alone(tmp_path, monkeypatch, capsys):
    """The hazard the positions differing carried: a reseed of the store nobody named."""
    default, named = tmp_path / "default", tmp_path / "named"
    seed(default, model_id="stub", now=NOW)
    monkeypatch.setenv("HGI_STORE", str(default))
    monkeypatch.setenv("HGI_ENV_FILE", str(tmp_path / "no-env-file-here"))

    assert main(["--store", str(named), "genesis", "--no-commit"]) == 0
    assert (named / "registry" / "vocabulary.json").is_file()

    assert main(["--store", str(default), "genesis", "--no-commit"]) == 1  # the refusal still stands
    assert f"{default} already holds a registry" in capsys.readouterr().err
    assert main(["--store", str(default), "genesis", "--force", "--no-commit"]) == 0  # and --force still reseeds
