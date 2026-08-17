"""The packaged edge_types.json must never drift from the canonical ontology.

The inverse-edge view is derived at snapshot load from this file; inside an
installed wheel only the packaged copy exists, so a stale copy would silently
change retrieval semantics in production.
"""

from pathlib import Path

from eleutheria_kg.services import snapshot


def test_packaged_edge_types_matches_canonical() -> None:
    canonical = snapshot.DEFAULT_EDGE_TYPES_PATH
    packaged = snapshot.PACKAGED_EDGE_TYPES_PATH
    assert packaged.is_file(), "packaged edge_types.json missing from the wheel"
    if not canonical.is_file():
        return  # installed context: only the packaged copy exists
    assert packaged.read_text(encoding="utf-8") == canonical.read_text(
        encoding="utf-8"
    ), "packaged edge_types.json is out of sync with knowledge graph/ontology/"


def test_inverse_relations_resolve_without_repo_layout(monkeypatch) -> None:
    monkeypatch.setattr(
        snapshot, "DEFAULT_EDGE_TYPES_PATH", Path("/nonexistent/edge_types.json")
    )
    inverses = snapshot._load_inverse_relations()
    assert inverses.get("opposes") == "opposed_by"
