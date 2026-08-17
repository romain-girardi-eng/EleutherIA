#!/usr/bin/env python3
"""Pull EleutherIA answer feedback from the authenticated JSONL export.

Set ELEUTHERIA_ADMIN_TOKEN to a current JWT belonging to a users.role=admin
account. The token is intentionally read from the environment so it need not
appear in shell history.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def _export_url(base_url: str) -> str:
    base = base_url.rstrip("/")
    if base.endswith("/api"):
        return f"{base}/feedback/export"
    return f"{base}/api/feedback/export"


def main() -> int:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--api-url",
        default=os.getenv("ELEUTHERIA_API_URL", "https://free-will.app"),
        help="EleutherIA origin or API base URL",
    )
    parser.add_argument(
        "--output",
        default=f"eleutheria-answer-feedback-{stamp}.jsonl",
        help="Destination path, or '-' for stdout",
    )
    args = parser.parse_args()

    token = os.getenv("ELEUTHERIA_ADMIN_TOKEN", "").strip()
    if not token:
        print("ERROR: ELEUTHERIA_ADMIN_TOKEN must be set", file=sys.stderr)
        return 2

    request = Request(
        _export_url(args.api_url),
        headers={"Authorization": f"Bearer {token}", "Accept": "application/x-ndjson"},
    )
    try:
        with urlopen(request, timeout=60) as response:  # noqa: S310
            if args.output == "-":
                target = sys.stdout.buffer
                while chunk := response.read(64 * 1024):
                    target.write(chunk)
                target.flush()
            else:
                path = Path(args.output).expanduser()
                with path.open("wb") as target:
                    while chunk := response.read(64 * 1024):
                        target.write(chunk)
                print(f"Feedback export saved to {path}", file=sys.stderr)
    except HTTPError as exc:
        print(f"ERROR: feedback export returned HTTP {exc.code}", file=sys.stderr)
        return 1
    except URLError as exc:
        print(f"ERROR: feedback export failed: {exc.reason}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
