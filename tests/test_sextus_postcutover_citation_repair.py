from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

import scripts.apply_2026_08_24_sextus_exact_cohort_repair as core
import scripts.apply_2026_08_24_sextus_postcutover_citation_repair as repair

ROOT = Path(__file__).resolve().parents[1]


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            for row in rows
        )
        + "\n",
        encoding="utf-8",
    )


def current_snapshot() -> repair.Snapshot:
    return repair.load_snapshot(ROOT / "data")


def pre_repair_citations(snapshot: repair.Snapshot | None = None) -> list[dict]:
    snapshot = snapshot or current_snapshot()
    citations = copy.deepcopy(snapshot.citations)
    by_key = {core.citation_key(row): row for row in citations}
    old_keys = {
        core.citation_key(repair.old_row(decision))
        for decision in core.CITATION_REWIRE_DECISIONS
    }
    new_keys = {
        core.citation_key(repair.new_row(decision))
        for decision in core.CITATION_REWIRE_DECISIONS
    }
    if old_keys.issubset(by_key) and not new_keys & set(by_key):
        return citations
    quarantine_path = ROOT / "data" / repair.QUARANTINE_RELATIVE
    assert quarantine_path.exists()
    before = [
        row["record"]
        for row in core.read_jsonl(quarantine_path)
        if row["record_type"] == "corpus_citation_before"
    ]
    assert {core.citation_key(row) for row in before} == old_keys
    citations = [row for row in citations if core.citation_key(row) not in new_keys]
    citations.extend(before)
    return citations


def write_fixture(data_root: Path, snapshot: repair.Snapshot, citations: list[dict]) -> None:
    write_jsonl(data_root / "kg/nodes.jsonl", snapshot.nodes)
    write_jsonl(data_root / "corpus/passages.jsonl", snapshot.passages)
    write_jsonl(data_root / "corpus/citations.jsonl", citations)


def test_four_decisions_are_exact_one_to_one_locus_adjudications() -> None:
    expected = {
        "citation_school_pyrrhonism_definition": (
            "07eccd35-ab0b-532d-b5e7-17c77b9c85bc",
            repair.core.PH_EDITION_URN + ":1.4",
        ),
        "citation_school_pyrrhonism_name": (
            "d66487f3-b40e-5187-9537-f2e312f2ce3e",
            repair.core.PH_EDITION_URN + ":1.7",
        ),
        "citation_posidonius_philosophy_image": (
            "baf8352f-a651-5381-a5c5-3ee1f8adc26d",
            repair.core.AM_EDITION_URN + ":7.19",
        ),
        "citation_posidonius_timaeus": (
            "e61f21d8-3027-5a0c-a4df-9874ae4a58ee",
            repair.core.AM_EDITION_URN + ":7.93",
        ),
    }
    assert len(core.CITATION_REWIRE_DECISIONS) == 4
    for decision in core.CITATION_REWIRE_DECISIONS:
        assert (
            repair.target_passage_id(decision),
            repair.target_cts_urn(decision),
        ) == expected[decision.decision_id]


def test_pre_repair_transform_changes_exactly_four_and_is_idempotent() -> None:
    snapshot = current_snapshot()
    before = pre_repair_citations(snapshot)
    first = repair.transform(snapshot.nodes, snapshot.passages, before)
    assert first.changes == 4
    assert len(first.quarantine) == 4
    assert len(first.report["adjudications"]) == 4
    assert first.report["validation"] == {
        "dangling_citation_nodes": 0,
        "dangling_citation_passages": 0,
        "exact_adjudicated_citations": 4,
    }
    second = repair.transform(snapshot.nodes, snapshot.passages, first.citations)
    assert second.changes == 0
    assert second.quarantine == []
    assert second.citations == first.citations


def test_dry_run_and_copy_write_contract(tmp_path: Path) -> None:
    snapshot = current_snapshot()
    data_root = tmp_path / "data"
    write_fixture(data_root, snapshot, pre_repair_citations(snapshot))
    citations_path = data_root / "corpus/citations.jsonl"
    before_hash = file_sha256(citations_path)
    assert repair.main(["--data-root", str(data_root)]) == 0
    assert file_sha256(citations_path) == before_hash
    assert not (data_root / repair.QUARANTINE_RELATIVE).exists()

    assert repair.main(["--write", "--data-root", str(data_root)]) == 0
    applied = repair.load_snapshot(data_root)
    assert repair.validate(applied.nodes, applied.passages, applied.citations) == {
        "dangling_citation_nodes": 0,
        "dangling_citation_passages": 0,
        "exact_adjudicated_citations": 4,
    }
    quarantine = core.read_jsonl(data_root / repair.QUARANTINE_RELATIVE)
    assert len(quarantine) == 4
    report = json.loads((data_root / repair.REPORT_RELATIVE).read_text())
    assert report["changes"] == 4
    after_hash = file_sha256(citations_path)
    assert after_hash != before_hash
    assert repair.main(["--write", "--data-root", str(data_root)]) == 0
    assert file_sha256(citations_path) == after_hash


def test_production_write_requires_second_lock() -> None:
    with pytest.raises(SystemExit):
        repair.main(["--write", "--data-root", str(ROOT / "data")])


def test_transaction_rejects_drift_since_snapshot_a(tmp_path: Path) -> None:
    source = current_snapshot()
    data_root = tmp_path / "data"
    write_fixture(data_root, source, pre_repair_citations(source))
    snapshot = repair.load_snapshot(data_root)
    result = repair.transform(snapshot.nodes, snapshot.passages, snapshot.citations)
    passage_path = data_root / "corpus/passages.jsonl"
    drift = passage_path.read_bytes() + b"\n"
    passage_path.write_bytes(drift)
    with pytest.raises(RuntimeError, match="since post-cutover snapshot A"):
        repair.write_result(data_root, result, snapshot.original_bytes)
    assert passage_path.read_bytes() == drift
    assert not (data_root / repair.QUARANTINE_RELATIVE).exists()
    assert not list(data_root.rglob(".sextus-stage-*"))


def test_transaction_rolls_back_injected_replace_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = current_snapshot()
    data_root = tmp_path / "data"
    write_fixture(data_root, source, pre_repair_citations(source))
    snapshot = repair.load_snapshot(data_root)
    result = repair.transform(snapshot.nodes, snapshot.passages, snapshot.citations)
    real_replace = core._replace_staged_file
    calls = 0

    def fail_third(staged: Path, target: Path) -> None:
        nonlocal calls
        calls += 1
        if calls == 3:
            raise OSError("injected post-cutover rollback")
        real_replace(staged, target)

    monkeypatch.setattr(core, "_replace_staged_file", fail_third)
    with pytest.raises(OSError, match="injected post-cutover rollback"):
        repair.write_result(data_root, result, snapshot.original_bytes)
    paths = {
        "nodes": data_root / "kg/nodes.jsonl",
        "passages": data_root / "corpus/passages.jsonl",
        "citations": data_root / "corpus/citations.jsonl",
    }
    assert {name: path.read_bytes() for name, path in paths.items()} == snapshot.original_bytes
    assert not (data_root / repair.QUARANTINE_RELATIVE).exists()
    assert not (data_root / repair.REPORT_RELATIVE).exists()
    assert not list(data_root.rglob(".sextus-stage-*"))


def test_hard_crash_recovery_journal_rolls_back_on_next_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = current_snapshot()
    data_root = tmp_path / "data"
    write_fixture(data_root, source, pre_repair_citations(source))
    snapshot = repair.load_snapshot(data_root)
    result = repair.transform(snapshot.nodes, snapshot.passages, snapshot.citations)
    real_replace = core._replace_staged_file
    calls = 0

    def hard_crash_before_citation_replace(staged: Path, target: Path) -> None:
        nonlocal calls
        calls += 1
        if calls == 4:
            raise KeyboardInterrupt("simulated process death")
        real_replace(staged, target)

    monkeypatch.setattr(core, "_replace_staged_file", hard_crash_before_citation_replace)
    with pytest.raises(KeyboardInterrupt, match="simulated process death"):
        repair.write_result(data_root, result, snapshot.original_bytes)
    assert (data_root / repair.RECOVERY_RELATIVE).exists()
    assert (data_root / repair.QUARANTINE_RELATIVE).exists()
    assert (data_root / repair.REPORT_RELATIVE).exists()
    assert (
        data_root / "corpus/citations.jsonl"
    ).read_bytes() == snapshot.original_bytes["citations"]

    monkeypatch.setattr(core, "_replace_staged_file", real_replace)
    assert repair.recover_if_needed(data_root) == "rolled_back"
    assert not (data_root / repair.RECOVERY_RELATIVE).exists()
    assert not (data_root / repair.QUARANTINE_RELATIVE).exists()
    assert not (data_root / repair.REPORT_RELATIVE).exists()
    assert not list(data_root.rglob(".sextus-stage-*"))
    assert (
        data_root / "corpus/citations.jsonl"
    ).read_bytes() == snapshot.original_bytes["citations"]


def test_current_phase_matches_artifact_and_never_hides_partial_state() -> None:
    snapshot = current_snapshot()
    result = repair.transform(snapshot.nodes, snapshot.passages, snapshot.citations)
    artifact = ROOT / "data" / repair.QUARANTINE_RELATIVE
    if artifact.exists():
        assert result.changes == 0
        assert repair.validate(snapshot.nodes, snapshot.passages, snapshot.citations)[
            "exact_adjudicated_citations"
        ] == 4
    else:
        assert result.changes == 4
