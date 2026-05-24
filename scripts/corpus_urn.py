"""Derive a work-level CTS URN from a work's passage URNs."""
from __future__ import annotations


def work_urn_of(passage_urn: str | None) -> str | None:
    if not passage_urn:
        return None
    parts = passage_urn.split(":")
    if len(parts) < 5 or not parts[3]:
        return None  # need urn:cts:<corpus>:<work>:<ref>
    return ":".join(parts[:4])


def derive_work_urn(passage_urns: list[str | None]) -> tuple[str | None, str]:
    found = {w for u in passage_urns if (w := work_urn_of(u))}
    if not found:
        return None, "unresolved"
    if len(found) > 1:
        return None, "ambiguous"
    return next(iter(found)), "resolved"
