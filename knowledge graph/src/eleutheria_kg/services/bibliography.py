"""Modern-scholarship bibliography aggregation.

Framework-free so it can be imported (and unit-tested) without the
optional FastAPI dependency pulled in by the API layer.
"""

import json
import re
from typing import Any


def collect_modern_scholarship(nodes: list[dict[str, Any]]) -> list[str]:
    """Aggregate unique modern-scholarship citations across nodes.

    References live either on the node itself (``modern_scholarship``) or in
    its metadata, where legacy imports stored them as JSON-encoded strings.
    """
    refs: set[str] = set()
    for node in nodes:
        ms = node.get("modern_scholarship")
        if not ms:
            ms = (node.get("metadata") or {}).get("modern_scholarship")
        if isinstance(ms, str):
            try:
                ms = json.loads(ms)
            except json.JSONDecodeError, ValueError:
                ms = [ms]
        if not isinstance(ms, list):
            continue
        for ref in ms:
            if isinstance(ref, dict):
                ref = ref.get("citation") or ref.get("text") or ref.get("title")
            if isinstance(ref, str) and ref.strip():
                refs.add(ref.strip())
    return sorted(refs, key=lambda r: re.split(r"[,.]", r, maxsplit=1)[0].lower())
