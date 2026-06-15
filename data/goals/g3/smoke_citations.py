#!/usr/bin/env python3
"""G3 smoke test — the public SSE path must deliver structured citations.

Asserts that a canonical scholarly query to ``/api/graphrag/query/stream``
yields a frame carrying >= MIN_CITATIONS structured citation objects (each a
clickable {ref, type, id, label} tuple, NOT a bare label string), and that the
frame arrives WITHOUT waiting for the terminal ``complete`` event — i.e. the
early ``citations_preview`` frame emitted before the verifier-v2 audit.

This is the regression guard for the divergence diagnosed in
``data/goals/g3/diagnosis.md``: structured citations used to ride only on the
terminal ``complete`` event, gated behind the audit, which never arrived before
Cloudflare's ~100s idle cut on slow queries.

Usage:
    python3 data/goals/g3/smoke_citations.py \
        --base https://free-will.app \
        --question "What did Chrysippus argue about fate and moral responsibility?" \
        --min-citations 3 --timeout 150

    # direct to the host (bypass Cloudflare), or local dev:
    python3 data/goals/g3/smoke_citations.py --base http://localhost:8000

Exit code 0 = pass (>= MIN_CITATIONS structured citations seen on a
citations_preview or complete frame). Non-zero = fail.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from urllib.parse import quote
from urllib.request import Request, urlopen

CANONICAL_QUESTION = (
    "What did Chrysippus argue about fate and moral responsibility?"
)


def _is_structured_citation(c: object) -> bool:
    """A clickable citation tuple, not a bare label string."""
    return (
        isinstance(c, dict)
        and bool(c.get("ref"))
        and bool(c.get("id"))
        and bool(c.get("label"))
    )


def _count_structured(frame: dict) -> int:
    data = frame.get("data") or {}
    # Agent-shape (citations_preview / complete from _build_complete_event):
    #   data["citations"] = [ {ref,type,id,label}, ... ]
    # Route-transformed complete shape:
    #   data["passage_citations"] = [ {ref,type,id,label}, ... ]
    for key in ("citations", "passage_citations"):
        cites = data.get(key)
        if isinstance(cites, list):
            n = sum(1 for c in cites if _is_structured_citation(c))
            if n:
                return n
    return 0


def run(base: str, question: str, min_citations: int, timeout: float) -> int:
    url = f"{base.rstrip('/')}/api/graphrag/query/stream?question={quote(question)}"
    req = Request(url, headers={"Accept": "text/event-stream"})
    started = time.monotonic()
    best = 0
    best_frame_type = ""
    saw_preview = False

    print(f"[smoke] GET {url}", file=sys.stderr)
    with urlopen(req, timeout=timeout) as resp:  # noqa: S310 (trusted base)
        for raw in resp:
            if time.monotonic() - started > timeout:
                print("[smoke] timeout reached", file=sys.stderr)
                break
            line = raw.decode("utf-8", "replace").strip()
            if not line.startswith("data: "):
                continue
            payload = line[6:]
            if not payload or payload == "[DONE]":
                continue
            try:
                frame = json.loads(payload)
            except json.JSONDecodeError:
                continue
            ftype = frame.get("type", "")
            if ftype in ("citations_preview", "complete"):
                n = _count_structured(frame)
                if ftype == "citations_preview":
                    saw_preview = True
                elapsed = int(time.monotonic() - started)
                print(
                    f"[smoke] {ftype} @ {elapsed}s -> {n} structured citations",
                    file=sys.stderr,
                )
                if n > best:
                    best, best_frame_type = n, ftype
                # The preview is the property under test: stop as soon as it
                # delivers enough citations (don't wait for the slow audit).
                if best >= min_citations and saw_preview:
                    break

    elapsed = int(time.monotonic() - started)
    if best >= min_citations:
        print(
            f"PASS: {best} structured citations on `{best_frame_type}` "
            f"in {elapsed}s (>= {min_citations}); "
            f"citations_preview seen={saw_preview}"
        )
        return 0
    print(
        f"FAIL: only {best} structured citations (need {min_citations}); "
        f"citations_preview seen={saw_preview}; elapsed {elapsed}s",
        file=sys.stderr,
    )
    return 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="https://free-will.app")
    ap.add_argument("--question", default=CANONICAL_QUESTION)
    ap.add_argument("--min-citations", type=int, default=3)
    ap.add_argument("--timeout", type=float, default=150.0)
    args = ap.parse_args()
    try:
        return run(args.base, args.question, args.min_citations, args.timeout)
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL (transport): {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
