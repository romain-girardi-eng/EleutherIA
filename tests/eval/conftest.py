"""Pytest configuration for the GraphRAG eval harness.

The full evaluation is intended to be driven by ``run_eval.py`` (CLI) against a
running backend. The pytest entry point exists so CI can opt-in to a small
smoke-test subset via:

    pytest tests/eval/ -v --run-eval

By default the eval marker is skipped, so a normal ``pytest`` invocation will
not hit the backend.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--run-eval",
        action="store_true",
        default=False,
        help="Run the GraphRAG evaluation harness against a live backend.",
    )
    parser.addoption(
        "--eval-base-url",
        default=os.environ.get("ELEUTHERIA_BASE_URL", "http://localhost:8000"),
        help="Backend base URL for eval tests (default: env ELEUTHERIA_BASE_URL "
        "or http://localhost:8000).",
    )
    parser.addoption(
        "--eval-limit",
        type=int,
        default=3,
        help="Number of queries to include in the pytest smoke subset (default 3).",
    )


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "eval: marks tests as live-backend evaluation (deselect with -m 'not eval')",
    )


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    if config.getoption("--run-eval"):
        return
    skip_eval = pytest.mark.skip(
        reason="eval tests skipped by default; pass --run-eval to enable"
    )
    for item in items:
        # Only skip items explicitly marked with @pytest.mark.eval. We avoid
        # ``"eval" in item.keywords`` because the keyword set also includes
        # path components (the file lives under tests/eval/), which would
        # silently skip the pure unit tests too.
        if any(mark.name == "eval" for mark in item.iter_markers()):
            item.add_marker(skip_eval)


@pytest.fixture(scope="session")
def eval_base_url(pytestconfig: pytest.Config) -> str:
    return str(pytestconfig.getoption("--eval-base-url"))


@pytest.fixture(scope="session")
def eval_limit(pytestconfig: pytest.Config) -> int:
    return int(pytestconfig.getoption("--eval-limit"))


@pytest.fixture(scope="session")
def queries_path() -> Path:
    return Path(__file__).parent / "queries.yaml"
