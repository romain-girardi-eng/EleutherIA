import asyncio
import json
from pathlib import Path

from scripts.deploy_data_staged import (
    OLD_SUFFIX,
    PARITY_VIOLATION_CLASSES,
    SOURCE_DEPENDENCY_INVENTORY,
    STAGING_SUFFIX,
    TARGET_TABLES,
    DependencyInventory,
    ForeignKeyDependency,
    TriggerDependency,
    ViewDependency,
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
