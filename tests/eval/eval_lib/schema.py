"""Dependency-free validation for GraphRAG evaluation run documents."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

RUN_SCHEMA_VERSION = "2.0"


class RunSchemaError(ValueError):
    """Raised when a run document violates the release artifact contract."""


def _mapping(value: Any, path: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise RunSchemaError(f"{path}: expected object")
    return value


def _required(mapping: Mapping[str, Any], names: tuple[str, ...], path: str) -> None:
    missing = [name for name in names if name not in mapping]
    if missing:
        raise RunSchemaError(f"{path}: missing required keys {missing}")


def _nullable_number(value: Any, path: str) -> None:
    if value is not None and not isinstance(value, (int, float)):
        raise RunSchemaError(f"{path}: expected number or null")


def validate_run_document(document: Mapping[str, Any]) -> None:
    """Validate the parts of the v2 contract used by gates and reports.

    A JSON Schema companion is committed for external tooling.  This validator
    stays in stdlib so CI and the offline runner do not need ``jsonschema``.
    """

    root = _mapping(document, "run")
    _required(
        root,
        (
            "artifact_type",
            "schema_version",
            "run_id",
            "captured_at",
            "binding",
            "dataset",
            "summary",
            "results",
        ),
        "run",
    )
    if root["artifact_type"] != "eleutheria.graphrag.eval_run":
        raise RunSchemaError("run.artifact_type: unsupported value")
    if root["schema_version"] != RUN_SCHEMA_VERSION:
        raise RunSchemaError(
            f"run.schema_version: expected {RUN_SCHEMA_VERSION!r}, "
            f"got {root['schema_version']!r}"
        )

    binding = _mapping(root["binding"], "run.binding")
    _required(
        binding,
        (
            "runner_id",
            "release_id",
            "model_id",
            "config_id",
            "config_sha256",
            "generation_enabled",
            "code_revision",
            "code_sha256",
            "workspace_dirty",
            "python_version",
            "python_implementation",
            "snapshot_sha256",
            "snapshot_files",
            "snapshot_scope",
        ),
        "run.binding",
    )
    for name in (
        "runner_id",
        "release_id",
        "config_id",
        "config_sha256",
        "code_sha256",
        "python_version",
        "python_implementation",
        "snapshot_scope",
    ):
        if not isinstance(binding[name], str) or not binding[name].strip():
            raise RunSchemaError(f"run.binding.{name}: must be a non-empty string")
    if not isinstance(binding["generation_enabled"], bool):
        raise RunSchemaError("run.binding.generation_enabled: expected boolean")
    if binding["generation_enabled"] and not (
        isinstance(binding["model_id"], str) and binding["model_id"].strip()
    ):
        raise RunSchemaError(
            "run.binding.model_id: generation-enabled runs must bind a model"
        )
    if not binding["generation_enabled"] and binding["model_id"] is not None:
        raise RunSchemaError(
            "run.binding.model_id: retrieval-only runs must use explicit null"
        )
    if not isinstance(binding["snapshot_sha256"], str) or not binding[
        "snapshot_sha256"
    ].strip():
        raise RunSchemaError("run.binding.snapshot_sha256: required")
    snapshot_files = _mapping(
        binding["snapshot_files"], "run.binding.snapshot_files"
    )
    _required(
        snapshot_files,
        ("passages", "nodes", "edges", "citations", "manifest"),
        "run.binding.snapshot_files",
    )

    dataset = _mapping(root["dataset"], "run.dataset")
    _required(
        dataset,
        (
            "query_files",
            "query_sha256",
            "case_count",
            "case_ids",
            "gold_validation",
        ),
        "run.dataset",
    )
    gold_validation = _mapping(
        dataset["gold_validation"], "run.dataset.gold_validation"
    )
    _required(
        gold_validation,
        ("status", "invalid_gold_count", "invalid_queries", "invalid_gold"),
        "run.dataset.gold_validation",
    )
    results = root["results"]
    if not isinstance(results, list):
        raise RunSchemaError("run.results: expected array")
    if dataset["case_count"] != len(results):
        raise RunSchemaError("run.dataset.case_count does not match run.results")
    if dataset["case_ids"] != [row.get("id") for row in results if isinstance(row, Mapping)]:
        raise RunSchemaError("run.dataset.case_ids does not match result order")

    for index, raw_result in enumerate(results):
        path = f"run.results[{index}]"
        result = _mapping(raw_result, path)
        _required(
            result,
            (
                "id",
                "query",
                "query_type",
                "difficulty",
                "strata",
                "gold",
                "status",
                "retrieval",
                "generation",
                "operations",
                "gates",
                "gate_failures",
                "error",
                "raw_trace",
            ),
            path,
        )
        if result["status"] not in {"ok", "error"}:
            raise RunSchemaError(f"{path}.status: expected 'ok' or 'error'")
        if not isinstance(result["strata"], list) or not all(
            isinstance(value, str) and value for value in result["strata"]
        ):
            raise RunSchemaError(f"{path}.strata: expected non-empty string array")
        if not isinstance(result["gates"], list) or not isinstance(
            result["gate_failures"], list
        ):
            raise RunSchemaError(f"{path}.gates/gate_failures: expected arrays")

        retrieval = _mapping(result["retrieval"], f"{path}.retrieval")
        _required(retrieval, ("observed", "method", "returned", "scores"), f"{path}.retrieval")
        returned = _mapping(retrieval["returned"], f"{path}.retrieval.returned")
        _required(
            returned,
            ("entities", "works", "manifestations", "passages"),
            f"{path}.retrieval.returned",
        )
        for channel in ("entities", "works", "manifestations", "passages"):
            value = returned[channel]
            if value is not None and not (
                isinstance(value, list) and all(isinstance(item, str) for item in value)
            ):
                raise RunSchemaError(
                    f"{path}.retrieval.returned.{channel}: expected string array or null"
                )

        generation = _mapping(result["generation"], f"{path}.generation")
        _required(
            generation,
            ("observed", "answer", "cited_passages", "scores", "safety", "judge"),
            f"{path}.generation",
        )
        for safety_name in (
            "source_identity",
            "quote_fidelity",
            "publication",
            "forbidden_strings",
        ):
            safety = _mapping(
                _mapping(generation["safety"], f"{path}.generation.safety").get(safety_name),
                f"{path}.generation.safety.{safety_name}",
            )
            _required(safety, ("observed", "status", "failure_count", "details"), f"{path}.generation.safety.{safety_name}")

        operations = _mapping(result["operations"], f"{path}.operations")
        operation_fields = (
            "retrieval_latency_ms",
            "generation_latency_ms",
            "total_latency_ms",
            "input_tokens",
            "output_tokens",
            "total_tokens",
            "estimated_cost_usd",
            "cache_hit",
        )
        _required(operations, operation_fields, f"{path}.operations")
        for name in operation_fields[:-1]:
            _nullable_number(operations[name], f"{path}.operations.{name}")
        if operations["cache_hit"] is not None and not isinstance(
            operations["cache_hit"], bool
        ):
            raise RunSchemaError(f"{path}.operations.cache_hit: expected boolean or null")
        _mapping(result["raw_trace"], f"{path}.raw_trace")

    summary = _mapping(root["summary"], "run.summary")
    _required(
        summary,
        ("counts", "retrieval", "generation", "safety", "operations", "by_stratum"),
        "run.summary",
    )


__all__ = ["RUN_SCHEMA_VERSION", "RunSchemaError", "validate_run_document"]
