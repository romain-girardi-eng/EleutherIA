from __future__ import annotations

import copy
import json
import math
from pathlib import Path
from typing import Any

import httpx
import pytest

from tests.eval.eval_lib.gates import compare_with_gates
from tests.eval.eval_lib.schema import RunSchemaError, validate_run_document
from tests.eval.eval_lib.snapshot_runner import (
    SnapshotIndex,
    load_citability_policy,
    tokenize,
)
from tests.eval.run_eval import (
    LocalSnapshotCatalog,
    QueryCase,
    _abstention,
    _binding,
    _http_capture,
    _new_document,
    _operation_values,
    _scores,
    load_queries,
    summarize,
    validate_gold_against_snapshot,
)


def _tiny_snapshot(tmp_path: Path) -> SnapshotIndex:
    passages = tmp_path / "passages.jsonl"
    nodes = tmp_path / "nodes.jsonl"
    edges = tmp_path / "edges.jsonl"
    citations = tmp_path / "citations.jsonl"
    manifest = tmp_path / "manifest.jsonl"
    passages.write_text(
        json.dumps(
            {
                "passage_id": "p_fate",
                "cts_urn": "urn:test:1",
                "canonical_ref": "Test 1",
                "text_content": "fate responsibility assent",
                "work_canonical_id": "manifest_work",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    nodes.write_text(
        "\n".join(
            json.dumps(row)
            for row in (
                {
                    "id": "person_a",
                    "node_id": "person_a",
                    "type": "person",
                    "label": "Author Fate",
                    "description": "responsibility",
                },
                {
                    "id": "concept_b",
                    "node_id": "concept_b",
                    "type": "concept",
                    "label": "Assent",
                    "description": "fate and assent",
                },
            )
        )
        + "\n",
        encoding="utf-8",
    )
    edges.write_text(
        json.dumps(
            {
                "edge_id": "e1",
                "source": "person_a",
                "source_id": "person_a",
                "target": "concept_b",
                "target_id": "concept_b",
                "relation": "discusses",
                "weight": 1.0,
                "metadata": {},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    citations.write_text(
        json.dumps(
            {
                "kg_node_id": "concept_b",
                "passage_id": "p_fate",
                "citation_type": "source_for",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    manifest.write_text("{}\n", encoding="utf-8")
    return SnapshotIndex(
        passages_path=passages,
        nodes_path=nodes,
        edges_path=edges,
        citations_path=citations,
        manifest_path=manifest,
    )


def _policy_snapshot(tmp_path: Path) -> SnapshotIndex:
    passages = tmp_path / "policy-passages.jsonl"
    nodes = tmp_path / "policy-nodes.jsonl"
    edges = tmp_path / "policy-edges.jsonl"
    citations = tmp_path / "policy-citations.jsonl"
    manifest = tmp_path / "policy-manifest.jsonl"
    passage_rows = [
        {
            "passage_id": "p_citable_bobzien",
            "cts_urn": "urn:cts:greekLit:tlg0086.tlg010:3.5",
            "canonical_ref": "EN III.5, 1113b7-8 (English)",
            "text_content": "where acting and not acting are up to us",
            "work_canonical_id": "manifest_bobzien",
            "manifestation_id": "manifest_bobzien",
            "work_urn": "urn:cts:greekLit:tlg0086.tlg010",
            "language": "eng",
            "translator": "Susanne Bobzien",
            "translation_label": "translation (I)",
            "translation_source": "Found in Translation",
            "source_publication_id": "pub_bobzien",
            "source_doi": "10.1000/bobzien-test",
            "citability": "citable",
            "provenance": {
                "publication_node_id": "pub_bobzien",
                "registry_source_id": "src_bobzien",
            },
        },
        {
            "passage_id": "p_discovery",
            "cts_urn": "urn:test:discovery",
            "canonical_ref": "Discovery 1",
            "text_content": "Susanne Bobzien translation acting not acting",
            "work_canonical_id": "manifest_legacy",
            "citability": "discoverable_only",
        },
        {
            "passage_id": "p_machine",
            "cts_urn": "urn:test:machine",
            "canonical_ref": "Machine 1",
            "text_content": "Susanne Bobzien translation acting not acting",
            "work_canonical_id": "manifest_machine",
            "translation_type": "machine",
        },
        {
            "passage_id": "p_snapshot_machine",
            "cts_urn": "urn:test:snapshot-machine",
            "canonical_ref": "Snapshot machine 1",
            "text_content": "Susanne Bobzien translation acting not acting",
            "work_canonical_id": "manifest_snapshot_machine",
            "citability": "citable",
        },
        {
            "passage_id": "p_manifest_metadata",
            "cts_urn": "urn:test:manifest-metadata",
            "canonical_ref": "Metadata 1",
            "text_content": "unrelated base vocabulary",
            "work_canonical_id": "manifest_rare",
            "citability": "citable",
        },
    ]
    passages.write_text(
        "\n".join(json.dumps(row) for row in passage_rows) + "\n",
        encoding="utf-8",
    )
    node_rows = [
        {
            "id": f"node_{row['passage_id']}",
            "node_id": f"node_{row['passage_id']}",
            "type": "passage",
            "label": row["canonical_ref"],
            "description": row["text_content"],
            "metadata": {
                "citability": "citable",
                **(
                    {"translation_type": "machine"}
                    if row["passage_id"] == "p_snapshot_machine"
                    else {}
                ),
            },
        }
        for row in passage_rows
    ]
    node_rows.append(
        {
            "id": "concept_discovery",
            "node_id": "concept_discovery",
            "type": "concept",
            "label": "Aurelia Quinctia discovery record",
            "description": "must not enter the entity evidence channel",
            "metadata": {"citability": "discoverable_only"},
        }
    )
    nodes.write_text(
        "\n".join(json.dumps(row) for row in node_rows) + "\n",
        encoding="utf-8",
    )
    edges.write_text("\n", encoding="utf-8")
    citations.write_text(
        "\n".join(
            json.dumps(
                {
                    "kg_node_id": f"node_{row['passage_id']}",
                    "passage_id": row["passage_id"],
                    "citation_type": "snapshot_passage_node",
                }
            )
            for row in passage_rows
        )
        + "\n",
        encoding="utf-8",
    )
    manifest.write_text(
        "\n".join(
            json.dumps(row)
            for row in (
                {
                    "canonical_id": "manifest_bobzien",
                    "title": "Found in Translation",
                    "author": "Aristotle",
                    "translator": "Susanne Bobzien",
                    "translation_label": "translation (I)",
                    "doi": "10.1000/bobzien-test",
                },
                {
                    "canonical_id": "manifest_rare",
                    "title": "Hidden Treatise on Agency",
                    "author": "Aurelia Quinctia",
                },
            )
        )
        + "\n",
        encoding="utf-8",
    )
    return SnapshotIndex(
        passages_path=passages,
        nodes_path=nodes,
        edges_path=edges,
        citations_path=citations,
        manifest_path=manifest,
    )


def _brute_force_bm25(index, query: str, *, k: int) -> list[tuple[str, float]]:
    """The pre-postings document scan, retained as an equivalence oracle."""

    terms = list(dict.fromkeys(tokenize(query)))
    count = len(index.passages)
    scored: list[tuple[str, float]] = []
    for position, passage in enumerate(index.passages):
        frequencies = index._term_frequencies[position]
        length = index._lengths[position]
        normalization = index.k1 * (
            1 - index.b + index.b * length / (index._average_length or 1.0)
        )
        score = 0.0
        for term in terms:
            frequency = frequencies.get(term, 0)
            if not frequency:
                continue
            document_frequency = index._document_frequencies.get(term, 0)
            inverse_frequency = math.log(
                1 + (count - document_frequency + 0.5) / (document_frequency + 0.5)
            )
            score += (
                inverse_frequency
                * frequency
                * (index.k1 + 1)
                / (frequency + normalization)
            )
        if score > 0:
            scored.append((passage.passage_id, score))
    return sorted(scored, key=lambda value: (-value[1], value[0]))[:k]


def test_snapshot_lexical_and_ppr_are_key_free_and_traceable(tmp_path: Path) -> None:
    index = _tiny_snapshot(tmp_path)
    lexical = index.retrieve(
        "fate responsibility", strategy="snapshot-lexical", passage_k=1, node_k=2
    )
    ppr = index.retrieve(
        "author fate",
        strategy="snapshot-ppr-bidirectional",
        passage_k=1,
        node_k=2,
        seed_k=1,
    )
    assert lexical.passage_ids == ["p_fate"]
    assert "person_a" in ppr.entity_ids
    assert ppr.trace["config"]["adjacency_mode"] == "asserted_bidirectional"
    assert ppr.trace["config"]["asserted_edge_count"] == 1
    assert index.excluded_inferred_edge_count == 0


@pytest.mark.parametrize(
    "query",
    (
        "Susanne Bobzien translation acting",
        "Aurelia Quinctia Hidden Treatise",
        "translation translation machine",
        "absent vocabulary",
    ),
)
def test_inverted_bm25_is_exactly_equivalent_to_document_scan(
    tmp_path: Path, query: str
) -> None:
    snapshot = _policy_snapshot(tmp_path)
    for index in (snapshot.passage_index, snapshot.excluded_passage_index):
        expected = _brute_force_bm25(index, query, k=10)
        actual = [
            (hit.passage.passage_id, hit.score) for hit in index.search(query, k=10)
        ]
        assert actual == expected


def test_snapshot_passage_evidence_uses_true_central_policy_fail_closed(
    tmp_path: Path,
) -> None:
    index = _policy_snapshot(tmp_path)
    CitabilityTier, evidence_policy, _stricter = load_citability_policy()
    assert evidence_policy({"citability": "citable"}).tier is CitabilityTier.CITABLE
    assert (
        evidence_policy({"citability": "discoverable_only"}).tier
        is CitabilityTier.DISCOVERABLE_ONLY
    )
    assert (
        evidence_policy({"translation_type": "machine"}).tier is CitabilityTier.BLOCKED
    )

    result = index.retrieve(
        "Susanne Bobzien translation I acting",
        strategy="snapshot-lexical",
        passage_k=10,
        node_k=10,
    )
    assert "p_citable_bobzien" in result.passage_ids
    assert "manifest_bobzien" in result.manifestation_ids
    assert not {
        "p_discovery",
        "p_machine",
        "p_snapshot_machine",
    } & set(result.passage_ids)

    policy_trace = result.trace["evidence_policy"]
    assert policy_trace["excluded_passage_count"] == 3
    exclusions = {
        row["passage_id"]: row for row in policy_trace["query_excluded_passages"]
    }
    assert set(policy_trace["query_excluded_passage_ids"]) == set(exclusions)
    assert exclusions["p_discovery"]["tier"] == "discoverable_only"
    assert exclusions["p_discovery"]["marker"] == "citability=discoverable_only"
    assert exclusions["p_machine"]["tier"] == "blocked"
    assert exclusions["p_machine"]["marker"] == "translation_type=machine"
    assert exclusions["p_snapshot_machine"]["tier"] == "blocked"
    assert any(
        check.get("scope") == "snapshot_node"
        and check.get("marker") == "translation_type=machine"
        for check in exclusions["p_snapshot_machine"]["checks"]
    )
    assert policy_trace["non_citable_node_count"] == 1
    assert policy_trace["non_citable_nodes"][0]["node_id"] == "concept_discovery"
    assert policy_trace["policy_sha256"] == index.citability_policy_sha256


def test_snapshot_indexes_generic_passage_and_manifest_identity_metadata(
    tmp_path: Path,
) -> None:
    index = _policy_snapshot(tmp_path)
    bobzien = index.passages["p_citable_bobzien"]
    searchable = bobzien.search_text.lower()
    for value in (
        "manifest_bobzien",
        "1113b7-8",
        "urn:cts:greeklit:tlg0086.tlg010:3.5",
        "eng",
        "susanne bobzien",
        "translation (i)",
        "found in translation",
        "pub_bobzien",
        "10.1000/bobzien-test",
        "aristotle",
    ):
        assert value in searchable

    metadata_result = index.retrieve(
        "Aurelia Quinctia Hidden Treatise",
        strategy="snapshot-lexical",
        passage_k=2,
        node_k=2,
    )
    assert metadata_result.passage_ids[0] == "p_manifest_metadata"
    assert metadata_result.manifestation_ids[0] == "manifest_rare"
    identity = metadata_result.trace["fused_passages"][0]["identity"]
    assert identity["manifestation_id"] == "manifest_rare"


def test_current_aristotle_repair_case_returns_only_citable_exact_evidence() -> None:
    cases = load_queries(Path(__file__).parent / "repair_wave_2026_08_24.yaml")
    case = next(
        row for row in cases if row.id == "repair_aristotle_en_1113b_manifest_split"
    )
    result = SnapshotIndex().retrieve(
        case.query,
        strategy="snapshot-lexical",
        passage_k=12,
        node_k=30,
        seed_k=5,
    )
    assert set(case.expected_passages).issubset(result.passage_ids)
    assert set(case.expected_manifestations).issubset(result.manifestation_ids)
    assert not set(case.forbidden_passages) & set(result.passage_ids)
    policy_trace = result.trace["evidence_policy"]
    assert set(case.forbidden_passages).issubset(
        policy_trace["query_excluded_passage_ids"]
    )
    traced = {row["passage_id"]: row for row in policy_trace["query_excluded_passages"]}
    assert all(
        traced[passage_id]["tier"] in {"discoverable_only", "blocked"}
        and traced[passage_id]["reason"]
        and traced[passage_id]["marker"]
        for passage_id in case.forbidden_passages
    )


def test_current_alexander_repair_case_keeps_named_work_identity_separate() -> None:
    cases = load_queries(Path(__file__).parent / "repair_wave_2026_08_24.yaml")
    case = next(row for row in cases if row.id == "repair_alexander_df12_df20")
    result = SnapshotIndex().retrieve(
        case.query,
        strategy="snapshot-lexical",
        passage_k=12,
        node_k=30,
        seed_k=5,
    )
    assert set(case.expected_works).issubset(result.work_ids)
    work_trace_ids = {row["node_id"] for row in result.trace["lexical_work_identities"]}
    assert set(case.expected_works).issubset(work_trace_ids)


def test_ppr_does_not_synthesize_inverse_edges(tmp_path: Path) -> None:
    index = _tiny_snapshot(tmp_path)
    forward = index.personalized_pagerank(
        ["person_a"], adjacency_mode="asserted_directed"
    )
    reverse = index.personalized_pagerank(
        ["concept_b"], adjacency_mode="asserted_directed"
    )
    assert forward.get("concept_b", 0) > 0
    assert reverse.get("person_a", 0) == 0


def test_bidirectional_ppr_reuses_asserted_row_without_inverse_relation(
    tmp_path: Path,
) -> None:
    index = _tiny_snapshot(tmp_path)
    reverse = index.personalized_pagerank(
        ["concept_b"], adjacency_mode="asserted_bidirectional"
    )
    assert reverse.get("person_a", 0) > 0
    assert index.asserted_edge_count == 1


def test_generation_and_citation_stay_null_without_model() -> None:
    case = QueryCase(
        id="q",
        query="fate",
        query_type="fact",
        difficulty="easy",
        expected_passages=["p1"],
    )
    _retrieval, generation = _scores(
        case,
        entities=[],
        works=[],
        manifestations=[],
        passages=[],
        citations=None,
        abstained=None,
        abstention_source=None,
    )
    assert generation["citation"]["scored"] is False
    assert generation["citation"]["recall"] is None
    assert generation["abstention"]["accuracy"] is None


def test_ood_requires_structured_abstention_signal() -> None:
    assert _abstention({"answer": "No result was found."}) == (None, None)
    assert _abstention({"insufficient_evidence": True}) == (
        True,
        "payload.insufficient_evidence",
    )


def test_http_error_preserves_status_body_and_elapsed() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            500,
            json={"detail": "broken retrieval"},
            headers={"x-request-id": "req-1"},
        )
    )
    case = QueryCase("q", "test question", "fact", "easy")
    with httpx.Client(transport=transport) as client:
        payload, elapsed, trace, error = _http_capture(
            client, "https://example.test", case, mode="fast"
        )
    assert payload == {"detail": "broken retrieval"}
    assert elapsed >= 0
    assert error and error.startswith("HTTP 500")
    assert trace["response"]["status_code"] == 500
    assert "broken retrieval" in trace["response"]["body"]
    assert trace["response"]["headers"]["x-request-id"] == "req-1"


def test_sse_capture_collects_stage_cost_and_complete_payload() -> None:
    seen_request: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen_request["method"] = request.method
        seen_request["url"] = str(request.url)
        body = "\n".join(
            [
                'data: {"type":"stage_complete","stage":"classify","duration_ms":100}',
                'data: {"type":"stage_complete","stage":"synthesis","duration_ms":400}',
                'data: {"type":"cost_summary","data":{"total_tokens":125,"total_cost_usd":0.02}}',
                'data: {"type":"complete","data":{"answer":"ok","metadata":{"publication_gate":{"publishable":true,"status":"passed","reasons":[]}}}}',
                "",
            ]
        )
        return httpx.Response(
            200,
            text=body,
            headers={"content-type": "text/event-stream"},
        )

    case = QueryCase("q", "test question", "fact", "easy")
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        payload, _elapsed, trace, error = _http_capture(
            client,
            "https://example.test",
            case,
            mode="deep",
            model="gpt-5.6-sol",
        )

    assert error is None
    assert payload is not None
    assert seen_request["method"] == "GET"
    assert "force_refresh=true" in seen_request["url"]
    assert "model=gpt-5.6-sol" in seen_request["url"]
    assert trace["request"]["params"]["model"] == "gpt-5.6-sol"
    assert payload["metadata"]["stage_metrics"] == [
        {"stage": "classify", "ms": 100},
        {"stage": "synthesis", "ms": 400},
    ]
    assert payload["metadata"]["total_tokens"] == 125
    assert payload["metadata"]["total_cost_usd"] == 0.02
    assert trace["kind"] == "live-http-sse"

    operations = _operation_values(payload, 600, mode="deep")
    assert operations["mode"] == "deep"
    assert operations["retained"] is True
    assert operations["estimated_cost_usd"] == 0.02


def test_repair_wave_gold_is_exact_in_current_snapshot() -> None:
    path = Path(__file__).parent / "repair_wave_2026_08_24.yaml"
    cases = load_queries(path)
    assert len(cases) == 7
    assert all(case.expected_passage_identities for case in cases)
    report = validate_gold_against_snapshot(cases, LocalSnapshotCatalog())
    assert report["status"] == "valid"
    assert report["strict_case_count"] == 7


def test_strict_gold_rejects_missing_entity_and_manifestation() -> None:
    catalog = LocalSnapshotCatalog()
    broken = QueryCase(
        id="strict",
        query="strict gold",
        query_type="fact",
        difficulty="easy",
        expected_entities=["missing_person"],
        expected_manifestations=["missing_manifestation"],
        provenance={"proof_test": "tests/proof.py"},
    )
    with pytest.raises(ValueError, match="strict gold/snapshot validation"):
        validate_gold_against_snapshot([broken], catalog)


def test_legacy_invalid_gold_is_not_scored_as_a_miss() -> None:
    catalog = LocalSnapshotCatalog()
    legacy = QueryCase(
        id="legacy",
        query="legacy gold",
        query_type="fact",
        difficulty="easy",
        expected_entities=["missing_person"],
    )
    validation = validate_gold_against_snapshot([legacy], catalog)
    assert validation["status"] == "legacy_invalid_gold"
    retrieval, _generation = _scores(
        legacy,
        entities=[],
        works=[],
        manifestations=[],
        passages=[],
        citations=None,
        abstained=None,
        abstention_source=None,
        gold_validation=validation["by_case"][legacy.id],
    )
    assert retrieval["entity"]["status"] == "not_scored_invalid_gold"
    assert retrieval["entity"]["recall"] is None
    assert retrieval["entity"]["invalid_gold_ids"] == ["missing_person"]


def _valid_run() -> dict:
    case = QueryCase(
        id="q",
        query="fate",
        query_type="fact",
        difficulty="easy",
        expected_entities=["person_a"],
    )
    retrieval, generation = _scores(
        case,
        entities=["person_a"],
        works=[],
        manifestations=[],
        passages=[],
        citations=None,
        abstained=None,
        abstention_source=None,
    )
    safety = {
        name: {
            "observed": False,
            "status": "not_run",
            "failure_count": None,
            "details": [],
        }
        for name in (
            "source_identity",
            "quote_fidelity",
            "publication",
            "forbidden_strings",
        )
    }
    result = {
        "id": "q",
        "query": "fate",
        "query_type": "fact",
        "difficulty": "easy",
        "strata": ["query_type:fact", "difficulty:easy"],
        "gold": {
            "answerable": True,
            "expected_entities": ["person_a"],
            "expected_entity_keywords": [],
            "expected_works": [],
            "expected_manifestations": [],
            "expected_passages": [],
            "complete_evidence_sets": [],
            "expected_passage_identities": {},
            "forbidden_passages": [],
            "gold_claims": [],
            "provenance": {},
        },
        "status": "ok",
        "retrieval": {
            "observed": True,
            "method": "fixture",
            "returned": {
                "entities": ["person_a"],
                "works": [],
                "manifestations": [],
                "passages": [],
            },
            "scores": retrieval,
            "trace_provenance": ["fixture"],
        },
        "generation": {
            "observed": False,
            "answer": None,
            "cited_passages": None,
            "scores": generation,
            "safety": safety,
            "judge": None,
        },
        "operations": {
            "retrieval_latency_ms": 1.0,
            "generation_latency_ms": None,
            "total_latency_ms": 1.0,
            "input_tokens": None,
            "output_tokens": None,
            "total_tokens": None,
            "estimated_cost_usd": None,
            "cache_hit": None,
        },
        "gates": [],
        "gate_failures": [],
        "error": None,
        "raw_trace": {"fixture": True},
    }
    binding = _binding(
        runner_id="fixture",
        release_id="snapshot:fixture",
        model_id=None,
        config_id="fixture-v1",
        config={"fixture": True},
        generation_enabled=False,
        snapshot_sha256="abc",
        snapshot_files={
            "passages": "abc",
            "nodes": "abc",
            "edges": "abc",
            "citations": "abc",
            "manifest": "abc",
        },
        snapshot_scope="fixture",
    )
    return _new_document(
        binding=binding,
        dataset={
            "query_files": ["fixture.yaml"],
            "query_sha256": "gold-hash",
            "case_count": 1,
            "case_ids": ["q"],
            "gold_validation": {
                "status": "valid",
                "invalid_gold_count": 0,
                "invalid_queries": [],
                "invalid_gold": [],
                "strict_case_count": 0,
            },
            "gold_counts": {},
        },
        results=[result],
    )


def test_schema_and_identical_comparison_pass() -> None:
    run = _valid_run()
    validate_run_document(run)
    report = compare_with_gates(run, copy.deepcopy(run))
    assert report["comparable"] is True
    assert report["release_gate"] == "pass"


def test_comparison_rejects_different_gold_hash() -> None:
    baseline = _valid_run()
    candidate = copy.deepcopy(baseline)
    candidate["dataset"]["query_sha256"] = "different"
    report = compare_with_gates(baseline, candidate)
    assert report["comparable"] is False
    assert "query_sha256 differs" in report["reasons"]


def test_comparison_rejects_invalid_gold_even_with_same_query_hash() -> None:
    baseline = _valid_run()
    candidate = copy.deepcopy(baseline)
    for document in (baseline, candidate):
        document["dataset"]["gold_validation"] = {
            "status": "legacy_invalid_gold",
            "invalid_gold_count": 1,
            "invalid_queries": ["q"],
            "invalid_gold": [
                {
                    "query_id": "q",
                    "channel": "entity",
                    "id": "stale",
                    "reason": "missing",
                    "strict": False,
                }
            ],
        }
    report = compare_with_gates(baseline, candidate)
    assert report["comparable"] is False
    assert report["release_gate"] == "fail"
    assert any("invalid gold" in reason for reason in report["reasons"])


def test_schema_requires_nullable_operational_fields() -> None:
    run = _valid_run()
    del run["results"][0]["operations"]["estimated_cost_usd"]
    with pytest.raises(RunSchemaError, match="estimated_cost_usd"):
        validate_run_document(run)


def test_live_metric_aggregation_reports_retention_stages_and_cost() -> None:
    first = copy.deepcopy(_valid_run()["results"][0])
    first["operations"].update(
        {
            "mode": "fast",
            "retained": True,
            "withholding_reasons": [],
            "stage_metrics": [{"stage": "synthesis", "ms": 100}],
            "estimated_cost_usd": 0.02,
        }
    )
    second = copy.deepcopy(first)
    second["id"] = "q-2"
    second["operations"].update(
        {
            "mode": "deep",
            "retained": False,
            "withholding_reasons": ["citation_audit_not_passed"],
            "stage_metrics": [{"stage": "synthesis", "ms": 300}],
            "estimated_cost_usd": 0.04,
        }
    )

    summary = summarize([first, second])

    assert summary["retention"]["retention_rate"] == 0.5
    assert summary["retention"]["withheld_rate"] == 0.5
    assert summary["retention"]["by_mode"]["fast"]["retention_rate"] == 1.0
    assert summary["retention"]["by_mode"]["deep"]["withholding_reasons"] == {
        "citation_audit_not_passed": 1
    }
    assert summary["operations"]["stage_latency"]["synthesis"] == {
        "observed_queries": 2,
        "p50_ms": 100.0,
        "p95_ms": 300.0,
        "max_ms": 300.0,
    }
    assert summary["operations"]["estimated_cost_usd"] == {
        "observed_queries": 2,
        "sum": 0.06,
        "p50": 0.02,
        "mean": 0.03,
        "max": 0.04,
    }


def test_public_citation_shape_resolves_only_declared_exact_corpus_twins():
    from types import SimpleNamespace
    from tests.eval.run_eval import extract_predicted_passages

    catalog = SimpleNamespace(exact_node_passages={"kg_locus": ["uuid_locus"]})
    payload = {
        "citations": {"ancient_sources": []},
        "passage_citations": [
            {"id": "kg_locus", "type": "passage"},
            {"id": "unknown_locus", "type": "passage"},
            {"id": "scholar_position", "type": "node"},
        ],
    }
    assert extract_predicted_passages(payload, catalog) == [
        "uuid_locus",
        "unknown_locus",
    ]


def test_required_evidence_cannot_pass_when_retrieval_is_unobserved_or_citation_is_absent():
    from tests.eval.run_eval import _query_gates
    from tests.eval.eval_lib.scoring import complete_evidence_set_recall

    case = QueryCase("q", "question", "fact", "easy", expected_passages=["p1"])
    retrieval, _ = _scores(
        case,
        entities=[],
        works=[],
        manifestations=[],
        passages=None,
        citations=[],
        abstained=None,
        abstention_source=None,
    )
    gates = _query_gates(retrieval, {}, complete_evidence_set_recall([], [["p1"]]))
    failed = {g["name"] for g in gates if g["status"] == "failed"}
    assert {"complete_evidence_set", "published_complete_evidence_set"} <= failed
