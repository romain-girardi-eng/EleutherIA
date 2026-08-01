#!/usr/bin/env python3
"""Enforce the login allowlist in the database.

Makes the authorized email(s) the ONLY accounts that can sign in:
  * ensures each authorized email exists as an active `admin` user;
  * deactivates (is_active = FALSE) every other user, revoking their access
    immediately (the backend rejects inactive users on every request).

Passwordless login means these accounts never need a usable password, so a
random unguessable bcrypt hash is stored to satisfy the NOT NULL constraint.

Idempotent — safe to re-run. Reads DATABASE_URL from the environment.

Usage:
    export DATABASE_URL=postgresql://...
    python database/scripts/set_allowlist.py                 # uses AUTHORIZED_EMAILS
    python database/scripts/set_allowlist.py romain@x.com    # explicit email(s)
    python database/scripts/set_allowlist.py --dry-run
"""

from __future__ import annotations

import asyncio
import os
import secrets
import sys

import asyncpg
import bcrypt

_DEFAULT_AUTHORIZED = "romain-girardi@hotmail.fr"


def _emails_from_args(argv: list[str]) -> list[str]:
    explicit = [a for a in argv if not a.startswith("-")]
    if explicit:
        raw = ",".join(explicit)
    else:
        raw = os.getenv("AUTHORIZED_EMAILS", _DEFAULT_AUTHORIZED)
    return [e.strip().lower() for e in raw.split(",") if e.strip()]


def _random_hash() -> str:
    return bcrypt.hashpw(secrets.token_hex(32).encode(), bcrypt.gensalt()).decode()


async def _run(emails: list[str], dry_run: bool) -> int:
    dsn = os.environ.get("DATABASE_URL", "").strip()
    if not dsn:
        print("ERROR: DATABASE_URL is not set.", file=sys.stderr)
        return 2

    conn = await asyncpg.connect(dsn, statement_cache_size=0)
    try:
        for email in emails:
            existing = await conn.fetchrow(
                "SELECT user_id FROM free_will.users WHERE lower(email) = $1", email
            )
            if existing:
                if not dry_run:
                    await conn.execute(
                        "UPDATE free_will.users SET is_active = TRUE, role = 'admin' "
                        "WHERE lower(email) = $1",
                        email,
                    )
                print(f"  authorized (activated, admin): {email}")
            else:
                username = email.split("@")[0][:50] or "owner"
                if not dry_run:
                    await conn.execute(
                        "INSERT INTO free_will.users "
                        "(username, email, hashed_password, role, is_active) "
                        "VALUES ($1, $2, $3, 'admin', TRUE) "
                        "ON CONFLICT (email) DO NOTHING",
                        username,
                        email,
                        _random_hash(),
                    )
                print(f"  authorized (created admin): {email}  [username={username}]")

        placeholders = ", ".join(f"${i + 1}" for i in range(len(emails)))
        others = await conn.fetch(
            f"SELECT email FROM free_will.users "
            f"WHERE is_active = TRUE AND lower(email) NOT IN ({placeholders})",
            *emails,
        )
        for row in others:
            print(f"  REVOKED (deactivated): {row['email']}")
        if not dry_run and others:
            await conn.execute(
                f"UPDATE free_will.users SET is_active = FALSE "
                f"WHERE lower(email) NOT IN ({placeholders})",
                *emails,
            )

        print(
            f"\n{'DRY-RUN — no changes written' if dry_run else 'Done'}: "
            f"{len(emails)} authorized, {len(others)} revoked."
        )
        return 0
    finally:
        await conn.close()


def main() -> int:
    argv = sys.argv[1:]
    dry_run = "--dry-run" in argv
    emails = _emails_from_args(argv)
    if not emails:
        print("ERROR: no authorized emails given.", file=sys.stderr)
        return 2
    print(f"Authorized emails: {', '.join(emails)}")
    return asyncio.run(_run(emails, dry_run))


if __name__ == "__main__":
    raise SystemExit(main())
