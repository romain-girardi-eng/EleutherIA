"""Load a local knowledge graph snapshot when PostgreSQL is unavailable.

Also provides a best-effort write-through to Supabase Storage so the
canonical snapshot files (`nodes.jsonl`, `edges.jsonl`, `stats.json`,
`_snapshot.json`) are mirrored to a `kg-snapshots` bucket on
EleutherIA's own Supabase. The disk write is always authoritative;
the upload is fire-and-forget and failures only emit a warning.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

SNAPSHOT_ENV_VAR = "ELEUTHERIA_KG_SNAPSHOT_DIR"
SUPABASE_URL_ENV_VAR = "ELEUTHERIA_SUPABASE_STORAGE_URL"
SUPABASE_KEY_ENV_VAR = "ELEUTHERIA_SUPABASE_STORAGE_KEY"
SUPABASE_BUCKET_ENV_VAR = "KG_SNAPSHOT_BUCKET"
DEFAULT_BUCKET = "kg-snapshots"


def _repo_root() -> Path:
    # services/snapshot.py -> eleutheria_kg -> src -> knowledge graph -> repo
    return Path(__file__).resolve().parents[4]


def resolve_snapshot_dir(snapshot_dir: str | os.PathLike[str] | None = None) -> Path:
    """Resolve the KG snapshot directory.

    Precedence:
    1. explicit argument
    2. ELEUTHERIA_KG_SNAPSHOT_DIR
    3. ./data/kg from the current working directory
    4. repo-root/data/kg
    """
    candidates: list[Path] = []
    if snapshot_dir:
        candidates.append(Path(snapshot_dir))

    env_dir = os.getenv(SNAPSHOT_ENV_VAR)
    if env_dir:
        candidates.append(Path(env_dir))

    candidates.append(Path.cwd() / "data" / "kg")
    candidates.append(_repo_root() / "data" / "kg")

    for candidate in candidates:
        expanded = candidate.expanduser()
        if expanded.exists():
            return expanded

    return candidates[0].expanduser() if candidates else _repo_root() / "data" / "kg"


def snapshot_available(snapshot_dir: str | os.PathLike[str] | None = None) -> bool:
    """Return whether a local KG snapshot is present."""
    directory = resolve_snapshot_dir(snapshot_dir)
    return (directory / "nodes.jsonl").exists() and (directory / "edges.jsonl").exists()


def load_kg_snapshot(
    snapshot_dir: str | os.PathLike[str] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """Load nodes and edges from deterministic JSONL snapshot files."""
    directory = resolve_snapshot_dir(snapshot_dir)
    nodes_path = directory / "nodes.jsonl"
    edges_path = directory / "edges.jsonl"

    if not nodes_path.exists() or not edges_path.exists():
        raise FileNotFoundError(
            f"KG snapshot missing: expected {nodes_path} and {edges_path}"
        )

    nodes = [_normalize_node(row) for row in _read_jsonl(nodes_path)]
    edges = [_normalize_edge(row) for row in _read_jsonl(edges_path)]

    nodes = [node for node in nodes if node.get("id")]
    node_ids = {str(node["id"]) for node in nodes}
    edges = [
        edge
        for edge in edges
        if edge.get("source") in node_ids and edge.get("target") in node_ids
    ]

    logger.info(
        "Loaded KG snapshot",
        extra={
            "snapshot_dir": str(directory),
            "nodes": len(nodes),
            "edges": len(edges),
        },
    )
    return {"nodes": nodes, "edges": edges}


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                row = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON in {path}:{line_no}: {exc}") from exc
            if isinstance(row, dict):
                rows.append(row)
    return rows


def _normalize_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if not value:
        return {}
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def _normalize_node(row: dict[str, Any]) -> dict[str, Any]:
    metadata = _normalize_mapping(row.get("metadata"))
    node_id = str(row.get("id") or row.get("node_id") or "")
    node = {
        **row,
        "id": node_id,
        "metadata": metadata,
    }

    for key in (
        "school",
        "role",
        "date",
        "birth",
        "death",
        "floruit",
        "approximate_dates",
        "scholarly_role",
    ):
        if node.get(key) is None and metadata.get(key) is not None:
            node[key] = metadata[key]

    if node.get("school") is None:
        node["school"] = metadata.get("school_affiliation")
    if node.get("role") is None:
        node["role"] = metadata.get("scholarly_role")

    return node


def _normalize_edge(row: dict[str, Any]) -> dict[str, Any]:
    metadata = _normalize_mapping(row.get("metadata"))
    source = str(row.get("source") or row.get("source_id") or "")
    target = str(row.get("target") or row.get("target_id") or "")
    weight = row.get("weight", metadata.get("weight", 1.0))
    try:
        normalized_weight = float(weight)
    except TypeError, ValueError:
        normalized_weight = 1.0

    return {
        **row,
        "source": source,
        "target": target,
        "relation": row.get("relation") or row.get("edge_type") or "",
        "description": row.get("description") or metadata.get("description"),
        "weight": normalized_weight,
        "metadata": metadata,
    }


# ---------------------------------------------------------------------------
# Supabase Storage write-through (Phase C)
# ---------------------------------------------------------------------------


def _storage_config() -> tuple[str, str, str] | None:
    """Return (url, key, bucket) for Supabase Storage, or None if unconfigured.

    Falls back to SUPABASE_URL / SUPABASE_SERVICE_KEY when the dedicated
    storage env vars are absent — they point at the same project in
    most setups.
    """
    url = os.getenv(SUPABASE_URL_ENV_VAR) or os.getenv("SUPABASE_URL")
    key = (
        os.getenv(SUPABASE_KEY_ENV_VAR)
        or os.getenv("SUPABASE_SERVICE_KEY")
        or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    )
    bucket = os.getenv(SUPABASE_BUCKET_ENV_VAR, DEFAULT_BUCKET)
    if not url or not key:
        return None
    return url.rstrip("/"), key, bucket


def _content_type_for(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".jsonl":
        return "application/x-ndjson"
    if suffix == ".json":
        return "application/json"
    return "application/octet-stream"


def upload_snapshot_file(
    local_path: str | os.PathLike[str],
    *,
    object_path: str | None = None,
    bucket: str | None = None,
) -> bool:
    """Upload a single snapshot file to Supabase Storage (best-effort).

    Returns True on a 2xx response, False if uploading failed or storage
    is unconfigured. The disk file is the source of truth — callers must
    never depend on the upload succeeding.

    `object_path` defaults to the basename of `local_path`. The bucket
    is created if missing? No — bucket creation is a one-time setup
    step done by the operator. This function only PUTs the object.
    """
    path = Path(local_path)
    if not path.is_file():
        logger.warning("Snapshot upload skipped: %s does not exist", path)
        return False

    config = _storage_config()
    if config is None:
        logger.debug("Snapshot upload skipped: Supabase Storage env vars unset")
        return False
    url, key, default_bucket = config
    target_bucket = bucket or default_bucket
    target_object = object_path or path.name

    try:
        import httpx  # local import keeps the loader path import-light
    except ImportError:  # pragma: no cover - httpx is a backend baseline dep
        logger.warning("httpx not installed; snapshot upload skipped")
        return False

    endpoint = f"{url}/storage/v1/object/{target_bucket}/{target_object}"
    headers = {
        "Authorization": f"Bearer {key}",
        "apikey": key,
        "Content-Type": _content_type_for(path),
        "x-upsert": "true",
    }

    try:
        with path.open("rb") as handle:
            data = handle.read()
        response = httpx.put(endpoint, content=data, headers=headers, timeout=30.0)
        if response.status_code >= 400:
            logger.warning(
                "Snapshot upload failed: %s %s -> %s",
                response.status_code,
                target_object,
                response.text[:200],
            )
            return False
        logger.info(
            "Snapshot uploaded",
            extra={"bucket": target_bucket, "object": target_object},
        )
        return True
    except Exception:
        logger.exception("Snapshot upload raised for %s", target_object)
        return False


def upload_snapshot_dir(
    snapshot_dir: str | os.PathLike[str],
    *,
    bucket: str | None = None,
    prefix: str = "",
) -> dict[str, bool]:
    """Upload every regular file under `snapshot_dir` to Supabase Storage.

    Returns a {object_path: success?} mapping. Failures are logged but
    never raised — uploading is always best-effort.
    """
    directory = Path(snapshot_dir)
    if not directory.is_dir():
        logger.warning("Snapshot dir not found: %s", directory)
        return {}

    results: dict[str, bool] = {}
    for file_path in sorted(directory.iterdir()):
        if not file_path.is_file():
            continue
        object_path = f"{prefix}{file_path.name}" if prefix else file_path.name
        results[object_path] = upload_snapshot_file(
            file_path, object_path=object_path, bucket=bucket
        )
    return results


def snapshot_public_url(object_path: str, *, bucket: str | None = None) -> str | None:
    """Return the public URL for a snapshot file, or None if unconfigured."""
    config = _storage_config()
    if config is None:
        return None
    url, _, default_bucket = config
    target_bucket = bucket or default_bucket
    return f"{url}/storage/v1/object/public/{target_bucket}/{object_path}"
