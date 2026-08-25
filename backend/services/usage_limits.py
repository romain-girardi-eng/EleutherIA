"""Server-side admission checks for per-user monthly LLM budgets."""

from __future__ import annotations

import uuid
from typing import Any

from eleutheria_database.services.db import DatabaseService
from fastapi import HTTPException


async def enforce_user_usage_limits(
    db: DatabaseService,
    user_id: str | uuid.UUID,
    *,
    mode: str,
) -> dict[str, Any]:
    """Reject a new LLM request once an admin-defined monthly cap is reached.

    Accounting is based on provider-reported tokens persisted in
    ``query_traces``. A request already admitted may cross the remaining cap;
    the next request is rejected. This avoids inventing pre-call token costs.
    """
    row = await db.fetchrow(
        """
        SELECT p.monthly_token_limit,
               p.monthly_cost_limit_usd::double precision AS monthly_cost_limit_usd,
               p.monthly_query_limit,
               COALESCE(p.allow_deep_mode, true) AS allow_deep_mode,
               count(t.trace_id)::int AS month_queries,
               COALESCE(sum(t.total_tokens), 0)::bigint AS month_tokens,
               COALESCE(sum(t.total_cost_usd), 0)::double precision AS month_cost_usd
        FROM free_will.users u
        LEFT JOIN free_will.user_access_policies p ON p.user_id=u.user_id
        LEFT JOIN free_will.query_traces t
          ON t.user_id=u.user_id
         AND t.started_at >= date_trunc('month', now())
        WHERE u.user_id=$1 AND u.is_active
        GROUP BY p.monthly_token_limit, p.monthly_cost_limit_usd,
                 p.monthly_query_limit, p.allow_deep_mode
        """,
        uuid.UUID(str(user_id)),
    )
    if not row:
        raise HTTPException(status_code=403, detail="User is inactive or missing")
    usage = dict(row)
    if mode == "deep" and not usage.get("allow_deep_mode", True):
        raise HTTPException(
            status_code=403,
            detail={"code": "deep_mode_disabled", "message": "Deep mode is disabled"},
        )
    checks = (
        ("monthly_query_limit", "month_queries", "queries"),
        ("monthly_token_limit", "month_tokens", "tokens"),
        ("monthly_cost_limit_usd", "month_cost_usd", "cost_usd"),
    )
    for limit_key, used_key, dimension in checks:
        limit = usage.get(limit_key)
        used = usage.get(used_key) or 0
        if limit is not None and float(used) >= float(limit):
            raise HTTPException(
                status_code=429,
                detail={
                    "code": "monthly_usage_limit_reached",
                    "dimension": dimension,
                    "limit": float(limit),
                    "used": float(used),
                },
                headers={"Retry-After": "3600"},
            )
    return usage
