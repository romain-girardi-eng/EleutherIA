#!/usr/bin/env python3
"""Repair 29 reviewed gold references; never drop a passage or dilute a claim."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import uuid
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.data_2026_09_05_eval_gold_repair import (  # noqa: E402
    CLAIM_CORRECTIONS,
    ORIGEN_QUERY,
    REPAIRS,
)
from tests.eval.run_eval import (  # noqa: E402
    LocalSnapshotCatalog,
    load_query_files,
    validate_gold_against_snapshot,
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    path = ROOT / "tests/eval/queries.yaml"
    before = path.read_bytes()
    data = yaml.safe_load(before)
    by_id = {q["id"]: q for q in data["queries"]}
    nodes = {n["id"]: n for n in map(json.loads, (ROOT / "data/kg/nodes.jsonl").open())}
    fields = {"entity": "expected_entities", "work": "expected_works"}
    report = []
    for qid, old_channel, old_id, new_channel, new_id in REPAIRS:
        node = nodes[new_id]
        assert (node["type"] == "work") == (new_channel == "work"), (
            qid,
            new_id,
            node["type"],
        )
        q = by_id[qid]
        old_field = fields[old_channel]
        new_field = fields[new_channel]
        old = q.get(old_field, [])
        if old_id in old:
            if old_field == new_field:
                q[old_field] = [new_id if x == old_id else x for x in old]
            else:
                q[old_field] = [x for x in old if x != old_id]
                if new_id not in q.setdefault(new_field, []):
                    q[new_field].append(new_id)
        else:
            assert new_id in q.get(new_field, []), (
                f"Unexpected gold precondition: {qid}/{old_id}"
            )
        report.append(
            {
                "query_id": qid,
                "old_channel": old_channel,
                "old_id": old_id,
                "new_channel": new_channel,
                "new_id": new_id,
                "target_type": node["type"],
                "target_label": node["label"],
                "target_sha256": hashlib.sha256(
                    json.dumps(node, sort_keys=True, ensure_ascii=False).encode()
                ).hexdigest(),
            }
        )
    q = by_id["r002"]
    if q["query"] != ORIGEN_QUERY:
        q["previous_query"] = q["query"]
        q["query"] = ORIGEN_QUERY
    for field, value in [
        (
            "expected_entities",
            "argument_origens_de_principiis_argument_for_free_will_93d043fc",
        ),
        ("expected_works", "work_origen_commentary_genesis"),
        ("expected_works", "work_origen_philocalia"),
    ]:
        if value not in q.setdefault(field, []):
            q[field].append(value)
    q["gold_claims"] = [
        CLAIM_CORRECTIONS.get(claim, claim) for claim in q.get("gold_claims", [])
    ]
    q["provenance"] = {
        "gold_revision": "2026-09-05",
        "reason": "Separate De Principiis III.1 from the Comm. Gen. III / Philocalia 23 dossier; retain all three passage requirements; correct the catena label and the reversed agency claim against passage 481e3e44-0c73-54f3-9190-73f09e332def.",
    }
    q = by_id["r014"]
    pid = str(
        uuid.uuid5(uuid.NAMESPACE_URL, "urn:cts:greekLit:tlg0031.tlg006.perseus-grc2:9")
    )
    q["expected_entities"] = ["person_paul_apostle"]
    q["expected_passages"] = [pid]
    q["complete_evidence_sets"] = [[pid]]
    q["expected_manifestations"] = ["romans_westcott_hort_perseus_grc2"]
    q["expected_passage_identities"] = {
        pid: {
            "work_canonical_id": "romans_westcott_hort_perseus_grc2",
            "canonical_ref": "Romans 9",
            "cts_urn": "urn:cts:greekLit:tlg0031.tlg006.perseus-grc2:9",
            "language": "grc",
        }
    }
    # Every existing passage expectation and claim remains required, byte-for-byte.
    old_queries = {q["id"]: q for q in yaml.safe_load(before)["queries"]}
    for q in data["queries"]:
        old = old_queries[q["id"]]
        assert set(old.get("expected_passages", [])) <= set(
            q.get("expected_passages", [])
        )
        expected_claims = (
            [
                CLAIM_CORRECTIONS.get(claim, claim)
                for claim in old.get("gold_claims", [])
            ]
            if q["id"] == "r002"
            else old.get("gold_claims", [])
        )
        assert expected_claims == q.get("gold_claims", [])
    text = yaml.safe_dump(data, allow_unicode=True, sort_keys=False)
    candidate = Path("/tmp/eleutheria-gold-candidate.yaml")
    candidate.write_text(text)
    files = [
        candidate,
        ROOT / "tests/eval/ood_queries.yaml",
        ROOT / "tests/eval/repair_wave_2026_08_24.yaml",
    ]
    validation = validate_gold_against_snapshot(
        load_query_files(files), LocalSnapshotCatalog()
    )
    assert validation["invalid_gold_count"] == 0, validation
    artifact = {
        "status": "resolved",
        "repaired_reference_count": len(report),
        "invalid_gold_count": 0,
        "before_sha256": hashlib.sha256(before).hexdigest(),
        "after_sha256": hashlib.sha256(text.encode()).hexdigest(),
        "repairs": report,
        "claim_corrections": CLAIM_CORRECTIONS,
        "validation": {k: v for k, v in validation.items() if k != "by_case"},
    }
    if args.apply and not args.dry_run:
        artifact_path = ROOT / "data/audit/2026-09-05_eval_gold_repair.json"
        if artifact_path.exists():
            previous = json.loads(artifact_path.read_text())
            artifact["before_sha256"] = previous["before_sha256"]
        path.write_text(text)
        (ROOT / "data/audit/2026-09-05_eval_gold_repair.json").write_text(
            json.dumps(artifact, indent=2, ensure_ascii=False) + "\n"
        )
        queue = ROOT / "tests/eval/legacy_gold_migration_queue.yaml"
        old = yaml.safe_load(queue.read_text())
        old.update(
            status="resolved_2026_09_05",
            invalid_gold_count=0,
            invalid_query_count=0,
            resolution_report="data/audit/2026-09-05_eval_gold_repair.json",
        )
        for entry in old["queue"]:
            item = next(
                r
                for r in report
                if r["query_id"] == entry["query_id"]
                and r["old_id"] == entry["stale_id"]
            )
            entry.update(
                status="resolved",
                replacement=item["new_id"],
                replacement_channel=item["new_channel"],
            )
        queue.write_text(yaml.safe_dump(old, allow_unicode=True, sort_keys=False))
    print(
        json.dumps(
            {
                "status": "applied" if args.apply and not args.dry_run else "dry_run",
                "repaired": len(report),
                "invalid_gold_count": validation["invalid_gold_count"],
            }
        )
    )


if __name__ == "__main__":
    main()
