import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from cli.audit_queue import audit_queue_app
from scripts.audit_queue.build_queue import (
    build_queue,
    read_jsonl,
    stable_id,
)
from scripts.audit_queue.generate_flag_sql import generate_sql

runner = CliRunner()


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
        encoding="utf-8",
    )


@pytest.fixture
def audit_dir(tmp_path: Path) -> Path:
    """Synthetic audit dir mimicking the real data/audit schemas (ASCII only)."""
    d = tmp_path / "audit"
    d.mkdir()
    _write_jsonl(
        d / "greek_insertions_deferred.jsonl",
        [
            {
                "node_id": "work_alpha",
                "severity": "critical",
                "issue": "Quoted run presented as verbatim is attested by no edition.",
                "current": "old text",
                "proposed": "replacement text",
                "sources": ["edition X"],
                "rationale": "fabricated run",
                "_defer": "inserts sourced Greek - verify vs edition before applying",
            }
        ],
    )
    _write_jsonl(
        d / "greek_unmatched.jsonl",
        [
            {
                "node_id": "concept_beta",
                "type": "concept",
                "label": "Beta concept",
                "period": None,
                "n_runs": 2,
                "n_unmatched": 2,
                "unmatched_runs": ["run-one", "run-two"],
            }
        ],
    )
    _write_jsonl(
        d / "cite_fix_deferred.jsonl",
        [
            {
                "node_id": "argument_gamma",
                "action": "repoint",
                "bad_passage_id": "bad-uuid",
                "new_passage_id": "good-uuid",
                "confidence": 0.7,
                "severity": "high",
                "rationale": "wrong book cited",
                "_defer": "confidence 0.7 < 0.8",
            }
        ],
    )
    _write_jsonl(
        d / "wave1_deferred.jsonl",
        [
            {
                "node_id": "scholar_delta",
                "dimension": "J1_false_fact",
                "verdict": "confirmed",
                "severity": "high",
                "fix_class": "scholarly",
                "field": "description",
                "issue": "False co-editorship claim.",
                "evidence": "quoted sentence",
                "current": "old desc",
                "proposed": "new desc",
                "rationale": "sources disagree",
                "sources": ["catalogue"],
                "final_confidence": 0.95,
                "_defer": "non-surgical description change - manual review",
            },
            {
                "node_id": "concept_epsilon",
                "dimension": "J2_greek",
                "verdict": "confirmed",
                "severity": "medium",
                "fix_class": "scholarly",
                "field": "description",
                "issue": "Non-verbatim quotation presented as transmitted text.",
                "evidence": "quoted string",
                "current": "old",
                "proposed": "new",
                "rationale": "edition differs",
                "sources": ["Bekker"],
                "final_confidence": 0.9,
                "_defer": "manual review",
            },
        ],
    )
    _write_jsonl(
        d / "mechanical_findings.jsonl",
        [
            {
                "dim": "duplicate_node_candidate",
                "severity": "medium",
                "fix_class": "scholarly",
                "ref_kind": "node",
                "ref": "argument_zeta_v0",
                "issue": "2 argument nodes share normalized label",
                "evidence": "argument_zeta_v0,argument_zeta_v1",
                "proposed": "confirm_merge",
            }
        ],
    )
    (d / "wave2_anach_deferred.jsonl").write_text("", encoding="utf-8")
    return d


@pytest.fixture
def queue_path(audit_dir: Path, tmp_path: Path) -> Path:
    out = tmp_path / "review_queue.jsonl"
    build_queue(audit_dir, out)
    return out


def test_stable_id_is_content_derived_and_prefixed():
    rec = {"node_id": "work_alpha", "issue": "x"}
    a = stable_id("wave1_deferred.jsonl", rec)
    assert a == stable_id("wave1_deferred.jsonl", rec)
    assert a != stable_id("wave1_deferred.jsonl", {"node_id": "work_alpha", "issue": "y"})
    assert a != stable_id("wave3_deferred.jsonl", rec)
    # Byte-identical duplicates in the same file are disambiguated.
    assert a != stable_id("wave1_deferred.jsonl", rec, occurrence=1)
    # Key order must not matter (canonical JSON).
    assert a == stable_id("wave1_deferred.jsonl", {"issue": "x", "node_id": "work_alpha"})
    assert a.startswith("rq_") and len(a) == 15


def test_build_queue_normalizes_all_sources(queue_path: Path):
    entries = read_jsonl(queue_path)
    assert len(entries) == 6
    by_cat = {e["category"] for e in entries}
    assert by_cat == {
        "greek_fabrication",
        "greek_unverified",
        "citation_fix",
        "false_fact",
        "mechanical",
    }
    ids = [e["id"] for e in entries]
    assert len(set(ids)) == len(ids)
    for e in entries:
        assert e["status"] == "pending"
        assert e["adjudicated_by"] is None
        assert e["adjudicated_at"] is None
        assert e["resolution"] is None
        assert e["id"].startswith("rq_") and len(e["id"]) == 15


def test_dimension_mapping_routes_j2_greek_to_greek_fabrication(queue_path: Path):
    entries = read_jsonl(queue_path)
    epsilon = next(e for e in entries if e["node_id"] == "concept_epsilon")
    assert epsilon["category"] == "greek_fabrication"
    assert epsilon["evidence"]["verdict"] == "confirmed"


def test_greek_insertions_carry_confirmed_verdict(queue_path: Path):
    entries = read_jsonl(queue_path)
    alpha = next(e for e in entries if e["node_id"] == "work_alpha")
    assert alpha["category"] == "greek_fabrication"
    assert alpha["evidence"]["verdict"] == "confirmed"


def test_cite_fix_captures_passage_id(queue_path: Path):
    entries = read_jsonl(queue_path)
    gamma = next(e for e in entries if e["node_id"] == "argument_gamma")
    assert gamma["category"] == "citation_fix"
    assert gamma["passage_id"] == "bad-uuid"
    assert "repoint" in gamma["proposed_action"]


def test_rebuild_is_idempotent_and_preserves_originals(
    audit_dir: Path, queue_path: Path
):
    before_queue = queue_path.read_bytes()
    before_sources = {p.name: p.read_bytes() for p in audit_dir.iterdir()}
    build_queue(audit_dir, queue_path)
    assert queue_path.read_bytes() == before_queue
    assert {p.name: p.read_bytes() for p in audit_dir.iterdir()} == before_sources


def test_rebuild_preserves_adjudications(audit_dir: Path, queue_path: Path):
    entries = read_jsonl(queue_path)
    target = entries[0]
    target["status"] = "adjudicated"
    target["resolution"] = "rejected"
    target["note"] = "false positive"
    target["adjudicated_by"] = "romain"
    target["adjudicated_at"] = "2026-06-10T12:00:00+00:00"
    _write_jsonl(queue_path, entries)

    build_queue(audit_dir, queue_path)
    rebuilt = {e["id"]: e for e in read_jsonl(queue_path)}
    kept = rebuilt[target["id"]]
    assert kept["status"] == "adjudicated"
    assert kept["resolution"] == "rejected"
    assert kept["note"] == "false positive"
    assert kept["adjudicated_by"] == "romain"
    others = [e for e in rebuilt.values() if e["id"] != target["id"]]
    assert all(e["status"] == "pending" for e in others)


def test_adjudication_does_not_migrate_when_source_file_shrinks(
    audit_dir: Path, queue_path: Path
):
    """Deleting an earlier source line must not re-attach an adjudication.

    Regression: line-number-derived ids made every later record inherit the
    id of the finding that previously sat on its line, silently migrating
    human adjudications to the WRONG finding (and suppressing integrity
    flags downstream).
    """
    entries = read_jsonl(queue_path)
    epsilon = next(e for e in entries if e["node_id"] == "concept_epsilon")
    assert epsilon["source_line"] == 2
    epsilon["status"] = "adjudicated"
    epsilon["resolution"] = "rejected"
    epsilon["note"] = "verified against edition"
    epsilon["adjudicated_by"] = "romain"
    epsilon["adjudicated_at"] = "2026-06-10T12:00:00+00:00"
    _write_jsonl(queue_path, entries)

    # The earlier finding (scholar_delta, line 1) gets fixed and removed:
    # concept_epsilon now sits on the line scholar_delta used to occupy.
    wave1 = audit_dir / "wave1_deferred.jsonl"
    rows = [json.loads(line) for line in wave1.read_text().splitlines() if line.strip()]
    _write_jsonl(wave1, [r for r in rows if r["node_id"] != "scholar_delta"])

    build_queue(audit_dir, queue_path)
    rebuilt = read_jsonl(queue_path)
    epsilon_after = next(e for e in rebuilt if e["node_id"] == "concept_epsilon")
    assert epsilon_after["id"] == epsilon["id"]
    assert epsilon_after["source_line"] == 1
    assert epsilon_after["status"] == "adjudicated"
    assert epsilon_after["resolution"] == "rejected"
    others = [e for e in rebuilt if e["node_id"] != "concept_epsilon"]
    assert all(e["status"] == "pending" and e["resolution"] is None for e in others)


def test_duplicate_source_records_get_distinct_ids(audit_dir: Path, tmp_path: Path):
    wave1 = audit_dir / "wave1_deferred.jsonl"
    rows = [json.loads(line) for line in wave1.read_text().splitlines() if line.strip()]
    _write_jsonl(wave1, rows + [rows[0]])

    out = tmp_path / "dup_queue.jsonl"
    entries = build_queue(audit_dir, out)
    ids = [e["id"] for e in entries]
    assert len(set(ids)) == len(ids)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _env(queue_path: Path) -> dict[str, str]:
    return {"ELEUTHERIA_REVIEW_QUEUE": str(queue_path), "ELEUTHERIA_REVIEWER": "romain"}


def test_cli_list_filters_by_category_and_status(queue_path: Path):
    result = runner.invoke(
        audit_queue_app,
        ["list", "--category", "greek_fabrication"],
        env=_env(queue_path),
    )
    assert result.exit_code == 0
    assert "2 match" in result.output

    result = runner.invoke(
        audit_queue_app,
        ["list", "--status", "adjudicated"],
        env=_env(queue_path),
    )
    assert result.exit_code == 0
    assert "0 match" in result.output


def test_cli_show_displays_entry(queue_path: Path):
    entry_id = read_jsonl(queue_path)[0]["id"]
    result = runner.invoke(audit_queue_app, ["show", entry_id], env=_env(queue_path))
    assert result.exit_code == 0
    assert entry_id in result.output

    result = runner.invoke(audit_queue_app, ["show", "rq_nope"], env=_env(queue_path))
    assert result.exit_code == 1


def test_cli_adjudicate_updates_only_target_entry(queue_path: Path):
    before = read_jsonl(queue_path)
    entry_id = before[1]["id"]
    result = runner.invoke(
        audit_queue_app,
        ["adjudicate", entry_id, "--resolution", "accepted", "--note", "verified"],
        env=_env(queue_path),
    )
    assert result.exit_code == 0

    after = {e["id"]: e for e in read_jsonl(queue_path)}
    target = after[entry_id]
    assert target["status"] == "adjudicated"
    assert target["resolution"] == "accepted"
    assert target["note"] == "verified"
    assert target["adjudicated_by"] == "romain"
    assert target["adjudicated_at"] is not None

    for e in before:
        if e["id"] != entry_id:
            assert after[e["id"]] == e


def test_cli_adjudicate_rejects_invalid_resolution(queue_path: Path):
    entry_id = read_jsonl(queue_path)[0]["id"]
    before = queue_path.read_bytes()
    result = runner.invoke(
        audit_queue_app,
        ["adjudicate", entry_id, "--resolution", "apply-all", "--note", "x"],
        env=_env(queue_path),
    )
    assert result.exit_code == 1
    assert queue_path.read_bytes() == before


def test_cli_has_no_bulk_command(queue_path: Path):
    for forbidden in ("apply-all", "adjudicate-all", "bulk"):
        result = runner.invoke(audit_queue_app, [forbidden], env=_env(queue_path))
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# Flagging SQL generator
# ---------------------------------------------------------------------------


def test_generate_sql_statuses_and_format(queue_path: Path):
    entries = read_jsonl(queue_path)
    by_node = {e["node_id"]: e for e in entries}
    # Reject the wave J2_greek finding: its node must drop out of the SQL.
    by_node["concept_epsilon"]["status"] = "adjudicated"
    by_node["concept_epsilon"]["resolution"] = "rejected"

    sql = generate_sql(list(by_node.values()))
    updates = [line for line in sql.splitlines() if line.startswith("UPDATE ")]
    assert len(updates) == 2  # work_alpha (confirmed) + concept_beta (unverified)

    alpha_line = next(line for line in updates if "'work_alpha'" in line)
    assert '"fabrication_confirmed_pending_fix"' in alpha_line
    assert f"queue_id={by_node['work_alpha']['id']}" in alpha_line
    assert alpha_line.endswith(
        f"-- queue_id={by_node['work_alpha']['id']} "
        f"source={by_node['work_alpha']['source_file']}:"
        f"{by_node['work_alpha']['source_line']}"
    )

    beta_line = next(line for line in updates if "'concept_beta'" in line)
    assert '"greek_unverified"' in beta_line

    # Non-greek categories never emit statements.
    assert "argument_gamma" not in sql
    assert "scholar_delta" not in sql
    assert "argument_zeta_v0" not in sql


def test_generate_sql_accepted_unverified_becomes_confirmed(queue_path: Path):
    entries = read_jsonl(queue_path)
    beta = next(e for e in entries if e["node_id"] == "concept_beta")
    beta["status"] = "adjudicated"
    beta["resolution"] = "accepted"
    sql = generate_sql(entries)
    beta_line = next(
        line
        for line in sql.splitlines()
        if line.startswith("UPDATE ") and "'concept_beta'" in line
    )
    assert '"fabrication_confirmed_pending_fix"' in beta_line


def test_generate_sql_fixed_resolution_skips_node(queue_path: Path):
    entries = read_jsonl(queue_path)
    for e in entries:
        if e["category"] in ("greek_fabrication", "greek_unverified"):
            e["status"] = "adjudicated"
            e["resolution"] = "fixed"
    sql = generate_sql(entries)
    assert not [line for line in sql.splitlines() if line.startswith("UPDATE ")]
