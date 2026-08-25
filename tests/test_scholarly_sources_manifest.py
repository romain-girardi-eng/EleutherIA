from scripts.check_scholarly_sources_manifest import MANIFEST, read_rows, validate


def test_committed_scholarly_manifest_v2_is_valid() -> None:
    rows = read_rows(MANIFEST)
    assert validate(rows) == []
    assert all(row["manifest_schema_version"] == "2.0.0" for row in rows)


def test_no_scope_free_false_completion_claim_remains() -> None:
    rows = read_rows(MANIFEST)
    cleanthes = next(row for row in rows if row["publication_dir"] == "svf_cleanthes")
    assert cleanthes["fragment_count_total"] == 157
    assert cleanthes["kg_ingestion_status"] == "partial"
    assert "eleven selected" in cleanthes["ingestion_scope"]
