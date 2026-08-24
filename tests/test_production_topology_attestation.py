import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ATTESTATION = ROOT / "data/audit/2026-08-24_production_single_api_topology.json"


def test_single_api_topology_attestation_is_fail_closed_and_reopenable() -> None:
    payload = json.loads(ATTESTATION.read_text(encoding="utf-8"))
    runtime = payload["public_api_runtime"]

    assert payload["capture_mode"] == "read_only_ssh_docker_metadata"
    assert runtime["running_container_count"] == 1
    assert runtime["effective_worker_default"] == 1
    assert payload["attestation"]["multi_replica_capability_claimed"] is False
    assert payload["attestation"]["secrets_captured"] is False
    assert len(payload["reopen_triggers"]) >= 5
    assert any("second API upstream" in item for item in payload["reopen_triggers"])

    assert re.fullmatch(r"[0-9a-f]{40}", payload["repository"]["head_sha"])
    for compose_file in payload["compose"]["files"]:
        assert re.fullmatch(r"[0-9a-f]{64}", compose_file["sha256"])
