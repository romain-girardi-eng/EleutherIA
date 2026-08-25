from __future__ import annotations

import uuid
from typing import Any

import pytest
from fastapi import HTTPException

from backend.services.usage_limits import enforce_user_usage_limits

USER_ID = uuid.UUID("10000000-0000-0000-0000-000000000001")


class _DB:
    def __init__(self, row: dict[str, Any] | None) -> None:
        self.row = row

    async def fetchrow(self, _query: str, *_args: Any) -> dict[str, Any] | None:
        return self.row


def _usage(**overrides: Any) -> dict[str, Any]:
    row = {
        "monthly_token_limit": None,
        "monthly_cost_limit_usd": None,
        "monthly_query_limit": None,
        "allow_deep_mode": True,
        "month_queries": 4,
        "month_tokens": 1200,
        "month_cost_usd": 0.42,
    }
    row.update(overrides)
    return row


@pytest.mark.asyncio
async def test_unlimited_user_is_admitted() -> None:
    result = await enforce_user_usage_limits(_DB(_usage()), USER_ID, mode="deep")
    assert result["month_tokens"] == 1200


@pytest.mark.asyncio
async def test_deep_mode_cap_is_enforced_server_side() -> None:
    with pytest.raises(HTTPException) as error:
        await enforce_user_usage_limits(
            _DB(_usage(allow_deep_mode=False)), USER_ID, mode="deep"
        )
    assert error.value.status_code == 403
    assert error.value.detail["code"] == "deep_mode_disabled"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("field", "limit", "dimension"),
    [
        ("monthly_query_limit", 4, "queries"),
        ("monthly_token_limit", 1200, "tokens"),
        ("monthly_cost_limit_usd", 0.42, "cost_usd"),
    ],
)
async def test_monthly_caps_reject_the_next_query(
    field: str, limit: int | float, dimension: str
) -> None:
    with pytest.raises(HTTPException) as error:
        await enforce_user_usage_limits(
            _DB(_usage(**{field: limit})), USER_ID, mode="fast"
        )
    assert error.value.status_code == 429
    assert error.value.detail["dimension"] == dimension


@pytest.mark.asyncio
async def test_missing_or_inactive_user_is_rejected() -> None:
    with pytest.raises(HTTPException) as error:
        await enforce_user_usage_limits(_DB(None), USER_ID, mode="fast")
    assert error.value.status_code == 403
