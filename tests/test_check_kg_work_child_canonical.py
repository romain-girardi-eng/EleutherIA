from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from scripts.check_kg_work_child_canonical import (
    canonical_cts,
    find_mismatches,
    is_allowlisted,
)

ROOT = Path(__file__).resolve().parents[1]


def node(node_id: str, node_type: str, metadata: dict) -> dict:
    return {"id": node_id, "node_id": node_id, "type": node_type, "metadata": metadata}


def edge(source: str, target: str) -> dict:
    return {"source": source, "target": target, "relation": "part_of"}


def test_canonical_cts_normalizes_project_spellings() -> None:
    expected = "urn:cts:greekLit:tlg0732.tlg014"
    assert canonical_cts("urn:cts:greekLit:tlg0732.tlg014.1st1K-grc1:12") == expected
    assert canonical_cts("tlg0732.tlg014") == expected
    assert canonical_cts("first1k:tlg0732.tlg014.1st1K-grc1") == expected
    assert canonical_cts("urn_cts_greeklit_tlg0732_tlg014_grc") == expected
    assert canonical_cts("urn:cts:latinLit:stoa0040.stoa003:3.7") == (
        "urn:cts:latinLit:stoa0040.stoa003"
    )


def test_detects_parent_vs_unanimous_children_mismatch() -> None:
    nodes = [
        node("w", "work", {"cts_urn": "urn:cts:greekLit:tlg9999.tlg001"}),
        node(
            "p1",
            "passage",
            {"work_canonical_id": "tlg0732.tlg014", "cts_urn": "x"},
        ),
        node(
            "p2",
            "passage",
            {"work_canonical_id": "first1k:tlg0732.tlg014.1st1K-grc1"},
        ),
    ]
    findings = find_mismatches(
        nodes,
        [edge("p1", "w"), edge("p2", "w")],
        [
            {
                "canonical_id": "tlg0732_tlg014_grc",
                "title": "De Fato",
                "author": "Alexander",
                "status": "in_corpus",
                "passages": 2,
            }
        ],
    )
    assert len(findings) == 1
    assert findings[0]["work_id"] == "w"
    assert findings[0]["child_canonical"] == "urn:cts:greekLit:tlg0732.tlg014"
    assert findings[0]["attested_children"] == 2
    assert findings[0]["manifest_matches"][0]["title"] == "De Fato"


def test_ignores_split_child_identity_until_scholarly_adjudication() -> None:
    nodes = [
        node("w", "work", {"cts_urn": "urn:cts:greekLit:tlg0007.tlg138"}),
        node("p1", "passage", {"work_canonical_id": "tlg0007.tlg135"}),
        node("p2", "passage", {"work_canonical_id": "tlg0007.tlg138"}),
    ]
    assert find_mismatches(nodes, [edge("p1", "w"), edge("p2", "w")], []) == []


def test_allowlist_requires_exact_work_and_child_identities() -> None:
    finding = {
        "work_candidates": ["urn:cts:greekLit:tlg0007.tlg138"],
        "child_canonical": "urn:cts:greekLit:tlg0007.tlg135",
    }
    entry = {
        "work_candidates": ["urn:cts:greekLit:tlg0007.tlg138"],
        "child_canonical": "urn:cts:greekLit:tlg0007.tlg135",
    }
    assert is_allowlisted(finding, entry)
    entry["child_canonical"] = "urn:cts:greekLit:tlg0007.tlg136"
    assert not is_allowlisted(finding, entry)


def test_skips_incomplete_child_identity_evidence() -> None:
    nodes = [
        node("w", "work", {"cts_urn": "urn:cts:greekLit:tlg9999.tlg001"}),
        node("p1", "passage", {"work_canonical_id": "tlg0732.tlg014"}),
        node("p2", "passage", {"cts_urn": "urn:cts:greekLit:tlg0732.tlg014:2"}),
    ]
    manifest = [
        {
            "canonical_id": "tlg0732_tlg014_grc",
            "status": "in_corpus",
            "passages": 2,
        }
    ]
    assert find_mismatches(nodes, [edge("p1", "w"), edge("p2", "w")], manifest) == []


def test_skips_missing_duplicate_or_incoherent_manifest_authority() -> None:
    nodes = [
        node("w", "work", {"cts_urn": "urn:cts:greekLit:tlg9999.tlg001"}),
        node("p", "passage", {"work_canonical_id": "tlg0732.tlg014"}),
    ]
    edges = [edge("p", "w")]
    authority = {
        "canonical_id": "tlg0732_tlg014_grc",
        "source": "scaife:urn:cts:greekLit:tlg0732.tlg014.1st1K-grc1",
        "status": "in_corpus",
        "passages": 1,
    }
    assert find_mismatches(nodes, edges, []) == []
    assert find_mismatches(nodes, edges, [authority, dict(authority)]) == []
    inconsistent = {
        **authority,
        "source": "scaife:urn:cts:greekLit:tlg9999.tlg002.1st1K-grc1",
    }
    assert find_mismatches(nodes, edges, [inconsistent]) == []


def test_one_correct_parent_field_does_not_hide_another_wrong_field() -> None:
    nodes = [
        node(
            "w",
            "work",
            {
                "cts_urn": "urn:cts:greekLit:tlg0732.tlg014",
                "canonical_id": "urn:cts:greekLit:tlg9999.tlg001",
            },
        ),
        node("p", "passage", {"work_canonical_id": "tlg0732.tlg014"}),
    ]
    manifest = [
        {
            "canonical_id": "tlg0732_tlg014_grc",
            "status": "in_corpus",
            "passages": 1,
        }
    ]
    findings = find_mismatches(nodes, [edge("p", "w")], manifest)
    assert len(findings) == 1
    assert findings[0]["work_candidates"] == [
        "urn:cts:greekLit:tlg0732.tlg014",
        "urn:cts:greekLit:tlg9999.tlg001",
    ]


def test_metadata_json_string_and_non_passage_children() -> None:
    work = node("w", "work", {})
    work["metadata"] = '{"cts_urn":"urn:cts:greekLit:tlg9999.tlg001"}'
    passage = node("p", "passage", {})
    passage["metadata"] = '{"work_canonical_id":"tlg0732.tlg014"}'
    synthesis = node("s", "synthesis", {"work_canonical_id": "tlg0000.tlg000"})
    manifest = [
        {
            "canonical_id": "tlg0732_tlg014_grc",
            "status": "in_corpus",
            "passages": 1,
        }
    ]
    findings = find_mismatches(
        [work, passage, synthesis],
        [edge("p", "w"), edge("s", "w")],
        manifest,
    )
    assert len(findings) == 1
    assert findings[0]["total_children"] == 1


def test_manifest_alias_protects_clement_corpus_slug() -> None:
    work = node(
        "work_clement_stromateis",
        "work",
        {"cts_urn": "urn:cts:greekLit:tlg0555.tlg004"},
    )
    passage = node(
        "passage_clement_strom_2_3_11",
        "passage",
        {"work_canonical_id": "work_clement_stromateis_grc"},
    )
    manifest = [
        {
            "canonical_id": "work_clement_stromateis_grc",
            "source": "local TEI: tlg0555.tlg004.perseus-grc2",
            "status": "in_corpus",
            "passages": 61,
        }
    ]
    assert (
        find_mismatches([work, passage], [edge(passage["id"], work["id"])], manifest)
        == []
    )

    work["metadata"]["cts_urn"] = "urn:cts:greekLit:tlg9999.tlg001"
    findings = find_mismatches(
        [work, passage], [edge(passage["id"], work["id"])], manifest
    )
    assert len(findings) == 1
    assert findings[0]["child_canonical"] == "urn:cts:greekLit:tlg0555.tlg004"


def test_work_repair_cli_imports_without_pythonpath_override() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/apply_2026_08_18_work_canonical_repairs.py"),
            "--help",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
