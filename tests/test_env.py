"""The env file loader: the surfaces a run configures are read from the process environment,
and ``hgi.cli.load_env`` is what puts an ``.env`` there before any command runs."""

from __future__ import annotations

import os

import pytest

from hgi.cli import load_env


@pytest.fixture(autouse=True)
def environment():
    """The loader writes to the process environment; no test may leave an endpoint behind for the next one."""
    before = dict(os.environ)
    yield
    os.environ.clear()
    os.environ.update(before)

FILE = """\
# the frozen model
HGI_INFERENCE_BASE_URL=https://endpoint.example/v1
export HGI_MODEL_ID="some-model-7b"
HGI_WEAVE_PROJECT='hgi'

HGI_INFERENCE_API_KEY=
not a pair
"""


def env_file(tmp_path, body: str = FILE):
    path = tmp_path / ".env"
    path.write_text(body)
    return path


def test_loads_pairs_and_strips_quotes(tmp_path, monkeypatch):
    monkeypatch.delenv("HGI_MODEL_ID", raising=False)
    loaded = load_env(env_file(tmp_path))
    assert loaded["HGI_INFERENCE_BASE_URL"] == "https://endpoint.example/v1"
    assert loaded["HGI_MODEL_ID"] == "some-model-7b"  # the export prefix and the quotes are not part of the value
    assert loaded["HGI_WEAVE_PROJECT"] == "hgi"


def test_blank_value_reads_as_unset(tmp_path, monkeypatch):
    """So the default behind the surface stands: the api key falls back to hgi.model's own, not to the empty string."""
    monkeypatch.delenv("HGI_INFERENCE_API_KEY", raising=False)
    assert "HGI_INFERENCE_API_KEY" not in load_env(env_file(tmp_path))
    assert "HGI_INFERENCE_API_KEY" not in os.environ


def test_process_environment_wins_and_the_loader_is_idempotent(tmp_path, monkeypatch):
    monkeypatch.setenv("HGI_MODEL_ID", "exported-for-this-run")
    path = env_file(tmp_path)
    assert "HGI_MODEL_ID" not in load_env(path)
    assert load_env(path) == {}  # a second read sets nothing: every pair is already in the environment


def test_absent_file_is_the_normal_case(tmp_path):
    assert load_env(tmp_path / "nothing-here") == {}


def test_hgi_env_file_names_the_file(tmp_path, monkeypatch):
    monkeypatch.delenv("HGI_WEAVE_PROJECT", raising=False)
    monkeypatch.setenv("HGI_ENV_FILE", str(env_file(tmp_path, "HGI_WEAVE_PROJECT=named-by-the-variable\n")))
    assert load_env()["HGI_WEAVE_PROJECT"] == "named-by-the-variable"
