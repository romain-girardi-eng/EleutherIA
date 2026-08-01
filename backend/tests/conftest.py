"""Shared pytest configuration for backend tests.

The auth allowlist (AUTHORIZED_EMAILS) defaults to the production owner only.
Tests build fake users with example.com addresses, so authorize those here —
this affects the test process only, never a real deployment.
"""

import os

import pytest

_TEST_AUTHORIZED = "alice@example.com,bob@example.com,romain@free-will.app"


@pytest.fixture(autouse=True, scope="session")
def _authorize_test_emails() -> None:
    os.environ["AUTHORIZED_EMAILS"] = _TEST_AUTHORIZED
