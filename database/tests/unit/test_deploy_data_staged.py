import asyncio
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from scripts.deploy_data_staged import (
    OLD_SUFFIX,
    PARITY_VIOLATION_CLASSES,
    SOURCE_DEPENDENCY_INVENTORY,
    STAGING_SUFFIX,
    TARGET_TABLES,
    DependencyInventory,
    ForeignKeyDependency,
    TriggerDependency,
    VerificationError,
    ViewDependency,
    _is_nonservable_discovery_node,
    expected_source_counts,
    generate_swap_sql,
    load_parity_baseline,
    rewrite_fk_reference,
    rewrite_trigger_target,
    verify_generation,
    write_parity_baseline,
)
from scripts.sync_corpus_to_db import load_corpus_payload

ROOT = Path(__file__).resolve().parents[3]


class ParityVerificationConnection:
    def __init__(self, rows):
        self.rows = rows

    async def fetchval(self, _query):
        return 1

    async def fetchrow(self, _query):
        return {
            "citation_to_passage": 0,
            "citation_to_kg_node": 0,
            "kg_edges": 0,
            "passage_to_work": 0,
            "duplicate_citations": 0,
        }

    async def fetch(self, _query):
        return self.rows


def empty_parity_baseline():
    return {name: [] for name in PARITY_VIOLATION_CLASSES}


def expected_single_row_counts():
    return dict.fromkeys(TARGET_TABLES, 1)


def sample_inventory() -> DependencyInventory:
    return DependencyInventory(
        foreign_keys=[
            ForeignKeyDependency(
                source_schema="free_will",
                source_table="kg_edges",
                name="kg_edges_source_id_fkey",
                target_schema="free_will",
                target_table="kg_nodes",
                definition=(
                    "FOREIGN KEY (source_id) REFERENCES "
                    "free_will.kg_nodes(node_id) ON DELETE CASCADE"
                ),
                validated=True,
            ),
            ForeignKeyDependency(
                source_schema="free_will",
                source_table="textual_variants",
                name="textual_variants_passage_id_fkey",
                target_schema="free_will",
                target_table="passages",
                definition=(
                    "FOREIGN KEY (passage_id) REFERENCES "
                    "free_will.passages(passage_id) ON DELETE CASCADE"
                ),
                validated=True,
            ),
        ],
        views=[
            ViewDependency(
                schema="free_will",
                name="passage_search",
                kind="v",
                definition="SELECT passage_id FROM free_will.passages;",
            )
        ],
        triggers=[
            TriggerDependency(
                table="kg_nodes",
                name="kg_nodes_bump_version",
                definition=(
                    "CREATE TRIGGER kg_nodes_bump_version AFTER INSERT ON "
                    "free_will.kg_nodes FOR EACH STATEMENT EXECUTE FUNCTION "
                    "free_will.bump_kg_version()"
                ),
            )
        ],
    )


def test_reference_and_trigger_rewriting_targets_staging():
    fk = rewrite_fk_reference(
        "FOREIGN KEY (passage_id) REFERENCES free_will.passages(passage_id)",
        target_schema="free_will",
        target_table="passages",
        suffix=STAGING_SUFFIX,
    )
    assert 'REFERENCES "free_will"."passages__staging"(passage_id)' in fk

    trigger = sample_inventory().triggers[0]
    rewritten = rewrite_trigger_target(
        trigger.definition,
        schema="free_will",
        table="kg_nodes",
        suffix=STAGING_SUFFIX,
    )
    assert 'ON "free_will"."kg_nodes__staging"' in rewritten


def test_deploy_swap_sql_is_one_transaction_and_rebinds_dependencies():
    statements = generate_swap_sql("free_will", sample_inventory())
    assert statements[0] == "BEGIN"
    assert statements[-1] == "COMMIT"
    assert any("VALIDATE CONSTRAINT" in statement for statement in statements)
    assert any(
        statement == 'ALTER TABLE "free_will"."kg_nodes" RENAME TO "kg_nodes__old"'
        for statement in statements
    )
    assert any(
        statement == 'ALTER TABLE "free_will"."kg_nodes__staging" RENAME TO "kg_nodes"'
        for statement in statements
    )
    assert any(
        statement.startswith('CREATE OR REPLACE VIEW "free_will"."passage_search"')
        for statement in statements
    )
    assert any("DROP TABLE IF EXISTS" in statement for statement in statements)


def test_rollback_sql_toggles_live_and_old_without_dropping_old():
    statements = generate_swap_sql("free_will", sample_inventory(), rollback=True)
    assert not any("DROP TABLE IF EXISTS" in statement for statement in statements)
    assert any(
        f'ALTER TABLE "free_will"."kg_nodes{OLD_SUFFIX}" '
        'RENAME TO "kg_nodes"' == statement
        for statement in statements
    )
    assert any(
        f'ALTER TABLE "free_will"."kg_nodes{STAGING_SUFFIX}" '
        f'RENAME TO "kg_nodes{OLD_SUFFIX}"' == statement
        for statement in statements
    )


def test_source_dependency_inventory_matches_canonical_schema_files():
    schema = (ROOT / "database/schema/schema.sql").read_text(encoding="utf-8")
    migrations = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            ROOT / "database/migrations/20260515_08_kg_version_tracking.sql",
            ROOT / "database/migrations/20260610_01_add_passage_id_to_oga_tokens.sql",
            ROOT / "database/migrations/20260610_02_unify_fts_simple_unaccent.sql",
            ROOT / "database/migrations/20260610_03_text_integrity.sql",
        )
    )
    source = schema + migrations

    for external_table, targets in SOURCE_DEPENDENCY_INVENTORY[
        "external_foreign_keys"
    ].items():
        assert f"{external_table} (" in source or f"{external_table}(" in source
        for target in targets:
            assert f"REFERENCES free_will.{target}" in source or (
                f"REFERENCES {target}" in source
            )
    for view in SOURCE_DEPENDENCY_INVENTORY["views"]:
        assert f"VIEW {view}" in source or f"VIEW free_will.{view}" in source
    for table, triggers in SOURCE_DEPENDENCY_INVENTORY["triggers"].items():
        assert table in source
        for trigger in triggers:
            assert f"TRIGGER {trigger}" in source
    assert "GENERATED ALWAYS AS" in source
    assert "idx_passages_search_vector_gin" in source
    assert "f_unaccent" in source


def test_corpus_loader_preserves_distinct_citation_types(tmp_path):
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / "manifest.jsonl").write_text(
        '{"canonical_id":"work_a","title":"A","author":"Author"}\n',
        encoding="utf-8",
    )
    (corpus / "passages.jsonl").write_text(
        '{"passage_id":"00000000-0000-0000-0000-000000000001",'
        '"work_canonical_id":"work_a","canonical_ref":"1",'
        '"text_content":"text"}\n',
        encoding="utf-8",
    )
    (corpus / "citations.jsonl").write_text(
        '{"passage_id":"00000000-0000-0000-0000-000000000001",'
        '"kg_node_id":"passage_a","citation_type":"primary"}\n'
        '{"passage_id":"00000000-0000-0000-0000-000000000001",'
        '"kg_node_id":"passage_a","citation_type":"translation"}\n',
        encoding="utf-8",
    )

    payload = load_corpus_payload(tmp_path)
    assert len(payload.citations) == 2
    assert payload.citations[0][0] != payload.citations[1][0]


def test_corpus_loader_preserves_translation_role_and_source_link(tmp_path):
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    original_id = "00000000-0000-0000-0000-000000000001"
    translation_id = "00000000-0000-0000-0000-000000000002"
    (corpus / "manifest.jsonl").write_text(
        '{"canonical_id":"work_grc","title":"Greek","author":"Author"}\n'
        '{"canonical_id":"work_eng","title":"English","author":"Translator"}\n',
        encoding="utf-8",
    )
    # Put the translation first to prove the loader reorders immediate self-FKs.
    (corpus / "passages.jsonl").write_text(
        '{"passage_id":"'
        + translation_id
        + '","work_canonical_id":"work_eng","canonical_ref":"1",'
        '"text_content":"translation","passage_role":"translation",'
        '"source_passage_id":"' + original_id + '"}\n'
        '{"passage_id":"'
        + original_id
        + '","work_canonical_id":"work_grc","canonical_ref":"1",'
        '"text_content":"original","passage_role":"original"}\n',
        encoding="utf-8",
    )
    (corpus / "citations.jsonl").write_text("", encoding="utf-8")

    payload = load_corpus_payload(tmp_path)

    assert payload.passages[0][0] == original_id
    by_id = {str(row[0]): row for row in payload.passages}
    assert by_id[original_id][8:] == ("original", None)
    assert by_id[translation_id][8:] == ("translation", original_id)


def test_corpus_loader_preserves_ancient_translation_without_inventing_source(
    tmp_path,
):
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    latin_id = "00000000-0000-0000-0000-000000000003"
    (corpus / "manifest.jsonl").write_text(
        '{"canonical_id":"irenaeus_lat","title":"AH III",'
        '"author":"Irenaeus / anonymous ancient translator"}\n',
        encoding="utf-8",
    )
    (corpus / "passages.jsonl").write_text(
        '{"passage_id":"'
        + latin_id
        + '","work_canonical_id":"irenaeus_lat",'
        '"canonical_ref":"III.20.3","language":"lat",'
        '"text_content":"ancient Latin","passage_role":"translation",'
        '"translation_type":"ancient_human_literal",'
        '"source_passage_status":"lost_continuous_greek_not_mapped"}\n',
        encoding="utf-8",
    )
    (corpus / "citations.jsonl").write_text("", encoding="utf-8")

    payload = load_corpus_payload(tmp_path)

    assert len(payload.passages) == 1
    assert payload.passages[0][0] == latin_id
    assert payload.passages[0][8:] == ("translation", None)


def test_corpus_loader_explicitly_excludes_nonservable_research_records(tmp_path):
    data_root = tmp_path
    corpus = data_root / "corpus"
    kg = data_root / "kg"
    corpus.mkdir()
    kg.mkdir()
    original_id = "00000000-0000-0000-0000-000000000001"
    unresolved_id = "00000000-0000-0000-0000-000000000002"
    (corpus / "manifest.jsonl").write_text(
        '{"canonical_id":"work_a","title":"A","author":"Author"}\n',
        encoding="utf-8",
    )
    passages = [
        {
            "passage_id": original_id,
            "work_canonical_id": "work_a",
            "canonical_ref": "1",
            "text_content": "primary text",
            "passage_role": "original",
        },
        {
            "passage_id": unresolved_id,
            "work_canonical_id": "work_a",
            "canonical_ref": "research note",
            "text_content": "not a verified primary text",
            "passage_role": "unresolved_english_research_record",
            "citability": "discoverable_only",
            "identity_status": "source_identity_unresolved",
            "language": "eng",
            "manifestation_id": "research_manifestation",
        },
    ]
    citations = [
        {
            "passage_id": original_id,
            "kg_node_id": "passage_primary",
            "citation_type": "snapshot_passage_node",
        },
        {
            "passage_id": unresolved_id,
            "kg_node_id": "passage_research_only",
            "citation_type": "snapshot_passage_node",
        },
    ]
    (corpus / "passages.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in passages), encoding="utf-8"
    )
    (corpus / "citations.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in citations), encoding="utf-8"
    )
    (kg / "nodes.jsonl").write_text('{"id":"node_a"}\n', encoding="utf-8")
    (kg / "edges.jsonl").write_text('{"id":"edge_a"}\n', encoding="utf-8")

    payload = load_corpus_payload(data_root)

    assert [str(row[0]) for row in payload.passages] == [original_id]
    assert {str(row[1]) for row in payload.citations} == {original_id}
    assert payload.excluded_nonservable["passages"] == {
        "count": 1,
        "passage_ids_sha256": hashlib.sha256(unresolved_id.encode()).hexdigest(),
    }
    assert payload.excluded_nonservable["passage_citations"]["count"] == 1
    assert payload.excluded_nonservable_node_ids == frozenset({"passage_research_only"})
    assert payload.excluded_nonservable["kg_nodes"] == {
        "count": 1,
        "kg_node_ids_sha256": hashlib.sha256(
            b"passage_research_only"
        ).hexdigest(),
    }

    expected, source_report = expected_source_counts(
        data_root,
        SimpleNamespace(kg_nodes=[object()], kg_edges=[object()]),
        payload,
    )
    assert expected["passages"] == 1
    assert expected["passage_citations"] == 1
    assert source_report["passages"] == 2
    assert source_report["servable_jsonl_counts"]["passages"] == 1
    assert source_report["excluded_nonservable"] == payload.excluded_nonservable


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("citability", "citable"),
        ("identity_status", "resolved"),
        ("language", "lat"),
        ("manifestation_id", ""),
        ("citable_as_primary", True),
        ("source_passage_id", "00000000-0000-0000-0000-000000000001"),
    ],
)
def test_corpus_loader_refuses_incomplete_nonservable_contract(
    tmp_path, field, value
):
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / "manifest.jsonl").write_text(
        '{"canonical_id":"work_a","title":"A","author":"Author"}\n',
        encoding="utf-8",
    )
    row = {
        "passage_id": "00000000-0000-0000-0000-000000000002",
        "work_canonical_id": "work_a",
        "canonical_ref": "research note",
        "text_content": "not a verified primary text",
        "passage_role": "unresolved_english_research_record",
        "citability": "discoverable_only",
        "identity_status": "source_identity_unresolved",
        "language": "eng",
        "manifestation_id": "research_manifestation",
    }
    row[field] = value
    (corpus / "passages.jsonl").write_text(
        json.dumps(row) + "\n", encoding="utf-8"
    )
    (corpus / "citations.jsonl").write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="complete discoverable-only"):
        load_corpus_payload(tmp_path)


def test_source_counts_reject_unaccounted_loader_deduplication(tmp_path):
    corpus = tmp_path / "corpus"
    kg = tmp_path / "kg"
    corpus.mkdir()
    kg.mkdir()
    passage_id = "00000000-0000-0000-0000-000000000001"
    (corpus / "manifest.jsonl").write_text(
        '{"canonical_id":"work_a","title":"A","author":"Author"}\n',
        encoding="utf-8",
    )
    (corpus / "passages.jsonl").write_text(
        json.dumps(
            {
                "passage_id": passage_id,
                "work_canonical_id": "work_a",
                "canonical_ref": "1",
                "text_content": "primary text",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    citation = {
        "passage_id": passage_id,
        "kg_node_id": "passage_primary",
        "citation_type": "snapshot_passage_node",
    }
    (corpus / "citations.jsonl").write_text(
        json.dumps(citation) + "\n" + json.dumps(citation) + "\n",
        encoding="utf-8",
    )
    (kg / "nodes.jsonl").write_text('{"id":"node_a"}\n', encoding="utf-8")
    (kg / "edges.jsonl").write_text('{"id":"edge_a"}\n', encoding="utf-8")
    payload = load_corpus_payload(tmp_path)

    with pytest.raises(VerificationError, match="filtered or deduplicated"):
        expected_source_counts(
            tmp_path,
            SimpleNamespace(kg_nodes=[object()], kg_edges=[object()]),
            payload,
        )


def test_verify_generation_allows_legacy_parity_violation():
    connection = ParityVerificationConnection(
        [
            {
                "node_id": "passage_legacy",
                "passage_id": "00000000-0000-0000-0000-000000000001",
                "has_citation": True,
                "canonical_ref_mismatch": False,
                "cts_urn_mismatch": True,
            }
        ]
    )
    baseline = empty_parity_baseline()
    baseline["cts_urn_mismatch"] = ["passage_legacy"]

    result = asyncio.run(
        verify_generation(
            connection,
            "free_will",
            STAGING_SUFFIX,
            expected_single_row_counts(),
            parity_baseline=baseline,
        )
    )

    parity = result["kg_corpus_locus_parity"]
    assert result["passed"] is True
    assert parity["legacy_debt"]["total"] == 1
    assert parity["new_violations"]["total"] == 0


def test_verify_generation_rejects_new_parity_violation_with_node_id():
    connection = ParityVerificationConnection(
        [
            {
                "node_id": "passage_regression",
                "passage_id": "00000000-0000-0000-0000-000000000001",
                "has_citation": True,
                "canonical_ref_mismatch": True,
                "cts_urn_mismatch": False,
            }
        ]
    )

    result = asyncio.run(
        verify_generation(
            connection,
            "free_will",
            STAGING_SUFFIX,
            expected_single_row_counts(),
            parity_baseline=empty_parity_baseline(),
        )
    )

    parity = result["kg_corpus_locus_parity"]
    assert result["passed"] is False
    assert parity["new_violations"] == {
        "total": 1,
        "by_class": {
            "cts_urn_mismatch": [],
            "canonical_ref_mismatch": ["passage_regression"],
            "missing_twin": [],
        },
    }


def test_verify_generation_exempts_exact_nonservable_discovery_node():
    connection = ParityVerificationConnection(
        [
            {
                "node_id": "passage_discovery_only",
                "passage_id": None,
                "has_citation": False,
                "nonservable_discovery": True,
                "canonical_ref_mismatch": False,
                "cts_urn_mismatch": False,
            }
        ]
    )

    result = asyncio.run(
        verify_generation(
            connection,
            "free_will",
            STAGING_SUFFIX,
            expected_single_row_counts(),
            parity_baseline=empty_parity_baseline(),
            allowed_nonservable_node_ids={"passage_discovery_only"},
        )
    )

    parity = result["kg_corpus_locus_parity"]
    assert result["passed"] is True
    assert parity["excluded_nonservable_discovery_nodes"] == 1
    assert parity["missing_twins"] == 0
    assert parity["new_violations"]["total"] == 0


def test_nonservable_discovery_contract_is_exact_and_fail_closed():
    exact = {
        "passage_role": "unresolved_english_research_record",
        "citability": "discoverable_only",
        "identity_status": "source_identity_unresolved",
        "language": "eng",
        "manifestation_id": "unresolved_english_manifestation",
        "source": "ai_translation",
        "translation_type": "machine",
    }
    assert _is_nonservable_discovery_node(exact) is True
    assert _is_nonservable_discovery_node({**exact, "citable_as_primary": False}) is True
    assert _is_nonservable_discovery_node({**exact, "citability": "citable"}) is False
    assert _is_nonservable_discovery_node({**exact, "identity_status": "verified"}) is False
    assert _is_nonservable_discovery_node({**exact, "citable_as_primary": True}) is False
    assert _is_nonservable_discovery_node({**exact, "language": "lat"}) is False
    assert _is_nonservable_discovery_node({**exact, "manifestation_id": ""}) is False
    assert _is_nonservable_discovery_node({**exact, "source": "published"}) is False
    assert _is_nonservable_discovery_node({**exact, "translation_type": "human"}) is False
    assert _is_nonservable_discovery_node({**exact, "citable_as_primary": "0"}) is False
    assert _is_nonservable_discovery_node({**exact, "citable_as_primary": "off"}) is False
    assert _is_nonservable_discovery_node({**exact, "citable_as_primary": {}}) is False


def test_nonservable_discovery_candidate_outside_allowlist_still_fails_parity():
    connection = ParityVerificationConnection(
        [
            {
                "node_id": "passage_allowed",
                "passage_id": None,
                "has_citation": False,
                "nonservable_discovery": True,
                "canonical_ref_mismatch": False,
                "cts_urn_mismatch": False,
            },
            {
                "node_id": "passage_not_allowlisted",
                "passage_id": None,
                "has_citation": False,
                "nonservable_discovery": True,
                "canonical_ref_mismatch": False,
                "cts_urn_mismatch": False,
            },
        ]
    )

    result = asyncio.run(
        verify_generation(
            connection,
            "free_will",
            STAGING_SUFFIX,
            expected_single_row_counts(),
            parity_baseline=empty_parity_baseline(),
            allowed_nonservable_node_ids={"passage_allowed"},
        )
    )

    assert result["passed"] is False
    assert result["kg_corpus_locus_parity"]["new_violations"]["by_class"][
        "missing_twin"
    ] == ["passage_not_allowlisted"]


def test_parity_baseline_generator_is_deterministic(tmp_path):
    data_root = tmp_path / "data"
    (data_root / "kg").mkdir(parents=True)
    (data_root / "corpus").mkdir(parents=True)
    passage_ids = {
        "passage_z": "00000000-0000-0000-0000-000000000002",
        "passage_a": "00000000-0000-0000-0000-000000000001",
    }
    nodes = [
        {
            "id": node_id,
            "type": "passage",
            "metadata": {
                "db_passage_id": passage_id,
                "canonical_ref": "1",
                "cts_urn": f"urn:kg:{node_id}",
            },
        }
        for node_id, passage_id in passage_ids.items()
    ]
    passages = [
        {
            "passage_id": passage_id,
            "canonical_ref": "1",
            "cts_urn": f"urn:corpus:{node_id}",
        }
        for node_id, passage_id in passage_ids.items()
    ]
    citations = [
        {"passage_id": passage_id, "kg_node_id": node_id}
        for node_id, passage_id in passage_ids.items()
    ]
    for path, rows in (
        (data_root / "kg/nodes.jsonl", reversed(nodes)),
        (data_root / "corpus/passages.jsonl", passages),
        (data_root / "corpus/citations.jsonl", reversed(citations)),
    ):
        path.write_text(
            "".join(json.dumps(row) + "\n" for row in rows),
            encoding="utf-8",
        )

    first_path = tmp_path / "first.json"
    second_path = tmp_path / "second.json"
    write_parity_baseline(data_root, first_path)
    write_parity_baseline(data_root, second_path)

    assert first_path.read_bytes() == second_path.read_bytes()
    assert load_parity_baseline(first_path)["cts_urn_mismatch"] == [
        "passage_a",
        "passage_z",
    ]
