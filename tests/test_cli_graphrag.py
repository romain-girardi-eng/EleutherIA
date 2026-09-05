"""Headless CLI contracts: real HTTPX streaming, no provider or database calls."""

from __future__ import annotations

import json
import sys

import httpx
import pytest
from typer.testing import CliRunner

from cli import graphrag_client as client_module
from cli.graphrag_client import auth_headers, capture_query, sse_events
from cli.main import app

DRAFT = "PRIVATE_PROVISIONAL_DRAFT"
CITATION = {
    "id": "source-1",
    "ref": "P1",
    "type": "passage",
    "layer": "primary",
    "label": "A checked source",
}
GATE = {"publishable": True, "status": "passed", "reasons": []}
LEDGER = [
    {"claim": "Checked claim", "evidence_ids": ["source-1"], "status": "supported"}
]
VERDICT = {
    "answer": "Checked claim [P1].",
    "withheld": False,
    "citations": [CITATION],
    "claim_ledger": LEDGER,
    "publication_gate": GATE,
    "quality_badge": "High",
}


def event(kind, data):
    return "data: " + json.dumps({"type": kind, "data": data}) + "\n\n"


@pytest.fixture(autouse=True)
def isolated_session(monkeypatch, tmp_path):
    monkeypatch.delenv("ELEUTHERIA_API_TOKEN", raising=False)
    monkeypatch.delenv("ELEUTHERIA_TOKEN_FILE", raising=False)
    monkeypatch.setattr(client_module, "SESSION_PATH", tmp_path / "session.json")


def client_for(content, *, status=200, handler=None):
    return httpx.Client(
        transport=httpx.MockTransport(
            handler or (lambda _: httpx.Response(status, text=content))
        )
    )


def test_sse_accepts_comments_multiline_crlf_and_final_buffer():
    lines = [
        ": heartbeat\r",
        "",
        "event: message",
        'data:{"type":',
        'data: "complete", "data": {"answer": "é"}}',
        "\r",
    ]
    assert list(sse_events(lines))[0]["data"]["answer"] == "é"
    assert list(sse_events(['data: {"type":"status"}'])) == [{"type": "status"}]


@pytest.mark.parametrize(
    "terminal",
    [
        None,
        {"trace_id": "trace-1"},
        {"trace_id": "trace-1", "passage_citations": [], "claim_ledger": []},
    ],
)
def test_full_verdict_survives_eof_and_terminal_enrichment(terminal):
    wire = event("answer_provisional", DRAFT) + event("answer_final", VERDICT)
    if terminal is not None:
        wire += event("complete", terminal)
    with client_for(wire) as client:
        payload, code = capture_query(
            "q", base_url="https://free-will.app", client=client
        )
    assert code == 0
    assert payload["answer"] == VERDICT["answer"]
    assert payload["passage_citations"] == [CITATION]
    assert payload["claim_ledger"] == LEDGER
    assert payload["metadata"]["publication_gate"] == GATE
    assert DRAFT not in json.dumps(payload)


class Interrupted(httpx.SyncByteStream):
    def __iter__(self):
        yield event("answer_final", VERDICT).encode()
        raise httpx.ReadError("PRIVATE_CONNECTION_DETAIL")


def test_read_failure_preserves_verdict_but_fails_the_run():
    with client_for(
        "", handler=lambda _: httpx.Response(200, stream=Interrupted())
    ) as client:
        payload, code = capture_query(
            "q", base_url="https://free-will.app", client=client
        )
    assert code == 3
    assert payload["answer"] == VERDICT["answer"]
    assert payload["passage_citations"] == [CITATION]
    assert payload["_cli"]["error"] == "Stream interrupted (ReadError)."
    assert "PRIVATE_CONNECTION_DETAIL" not in json.dumps(payload)


def test_withheld_verdict_cannot_be_overridden_by_later_prose():
    withheld = {**VERDICT, "withheld": True}
    terminal = {
        "answer": DRAFT,
        "metadata": {"publication_gate": GATE, "debug_trace": {"raw_excerpt": DRAFT}},
    }
    with client_for(
        event("answer_final", withheld) + event("complete", terminal)
    ) as client:
        payload, code = capture_query(
            "q", base_url="https://free-will.app", client=client
        )
    assert code == 2
    assert DRAFT not in json.dumps(payload)
    assert payload["answer"] == ""
    assert payload["passage_citations"] == []
    assert payload["metadata"]["publication_gate"]["publishable"] is False


@pytest.mark.parametrize(
    "wire",
    [
        event("answer_provisional", DRAFT),
        event("citations_preview", {"answer": DRAFT}),
        event("answer_chunk", DRAFT),
        event("complete", {"answer": DRAFT}),
    ],
)
def test_ungated_prose_is_never_an_answer(wire):
    with client_for(wire) as client:
        payload, code = capture_query(
            "q", base_url="https://free-will.app", client=client
        )
    assert code == 2
    assert payload["answer"] == ""
    assert DRAFT not in json.dumps(payload)


@pytest.mark.parametrize(
    ("http_status", "expected_code"), [(401, 4), (403, 4), (429, 3), (502, 3)]
)
def test_http_failures_are_machine_readable_and_do_not_expose_response_bodies(
    http_status, expected_code
):
    with client_for("PRIVATE_ERROR_DETAIL", status=http_status) as client:
        payload, code = capture_query(
            "q", base_url="https://free-will.app", client=client
        )
    assert code == expected_code
    assert payload["_cli"]["http_status"] == http_status
    assert "PRIVATE_ERROR_DETAIL" not in json.dumps(payload)


def test_authentication_mode_model_and_refresh_reach_the_streaming_endpoint(
    monkeypatch,
):
    monkeypatch.setenv("ELEUTHERIA_API_TOKEN", "secret-token")

    def handler(request):
        assert request.url.path == "/api/graphrag/query/stream"
        assert request.headers["Authorization"] == "Bearer secret-token"
        assert request.url.params["mode"] == "deep"
        assert request.url.params["model"] == "chosen-model"
        assert request.url.params["force_refresh"] == "true"
        assert "secret-token" not in str(request.url)
        return httpx.Response(200, text=event("answer_final", VERDICT))

    with client_for("", handler=handler) as client:
        payload, code = capture_query(
            "question",
            base_url="https://free-will.app/api/",
            mode="deep",
            model="chosen-model",
            fresh=True,
            client=client,
        )
    assert code == 0
    assert "secret-token" not in json.dumps(payload)


def test_cli_json_and_file_preserve_provenance_and_return_partial_exit_code(
    monkeypatch, tmp_path
):
    wire = event(
        "answer_final", {**VERDICT, "publication_gate": {**GATE, "status": "partial"}}
    )
    real_capture = capture_query
    with client_for(wire) as client:
        monkeypatch.setattr(
            client_module,
            "capture_query",
            lambda question, **kw: real_capture(question, client=client, **kw),
        )
        output = tmp_path / "answer.json"
        result = CliRunner().invoke(
            app,
            [
                "ask",
                "q",
                "--base-url",
                "https://free-will.app",
                "--json",
                "--output",
                str(output),
            ],
        )
    assert result.exit_code == 2
    payload = json.loads(result.stdout)
    assert payload == json.loads(output.read_text())
    assert payload["claim_ledger"] == LEDGER
    assert output.stat().st_mode & 0o777 == 0o600


def test_noninteractive_login_is_private_and_scoped_to_api(monkeypatch, tmp_path):
    actual_client = httpx.Client
    calls = []

    def handler(request):
        calls.append(request.url.path)
        assert json.loads(request.content) == {
            "email": "test@example.com",
            "code": "123456",
        }
        return httpx.Response(200, json={"access_token": "private-session-token"})

    monkeypatch.setattr(
        httpx,
        "Client",
        lambda **kw: actual_client(transport=httpx.MockTransport(handler), **kw),
    )
    code_file = tmp_path / "otp.txt"
    code_file.write_text("123456\n")
    result = CliRunner().invoke(
        app,
        [
            "login",
            "--email",
            "test@example.com",
            "--base-url",
            "https://free-will.app",
            "--code-file",
            str(code_file),
        ],
    )
    assert result.exit_code == 0, result.output
    assert calls == ["/api/auth/verify-code"]
    assert "private-session-token" not in result.output
    assert client_module.SESSION_PATH.stat().st_mode & 0o777 == 0o600
    assert (
        auth_headers("https://free-will.app")["Authorization"]
        == "Bearer private-session-token"
    )
    assert auth_headers("https://another.example") == {}


def test_quality_commands_use_the_cli_interpreter_and_frontend_never_watches(
    monkeypatch,
):
    from cli import main

    calls = []
    monkeypatch.setattr(main, "run_command", lambda cmd, **kw: calls.append(cmd) or 0)
    assert CliRunner().invoke(app, ["test", "graphrag"]).exit_code == 0
    assert calls[-1][:3] == [sys.executable, "-m", "pytest"]
    assert CliRunner().invoke(app, ["test", "frontend"]).exit_code == 0
    assert calls[-1] == ["npm", "test", "--", "--run"]
    assert (
        CliRunner()
        .invoke(
            app, ["test", "answers", "--runner", "snapshot-lexical", "--limit", "1"]
        )
        .exit_code
        == 0
    )
    assert calls[-1][0] == sys.executable
    assert "--limit" in calls[-1]


@pytest.mark.parametrize(
    "terminal",
    [
        {"answer": "", "metadata": {"publication_gate": GATE}},
        {"answer": DRAFT, "metadata": "broken"},
    ],
)
def test_empty_or_malformed_terminal_cannot_be_a_success(terminal):
    with client_for(event("complete", terminal)) as client:
        payload, code = capture_query(
            "q", base_url="https://free-will.app", client=client
        )
    assert code == 2
    assert payload["answer"] == ""


def test_strict_live_evaluation_refuses_bad_gold_before_constructing_http_client(
    monkeypatch,
):
    from types import SimpleNamespace

    from tests.eval import run_eval

    monkeypatch.setattr(run_eval, "LocalSnapshotCatalog", lambda: object())
    monkeypatch.setattr(
        run_eval, "validate_gold_against_snapshot", lambda *a: {"invalid_gold_count": 1}
    )

    def unexpected_client(**kwargs):
        pytest.fail("Live HTTP must not start with invalid gold")

    monkeypatch.setattr(run_eval, "httpx", SimpleNamespace(Client=unexpected_client))
    with pytest.raises(ValueError, match="No live query was sent"):
        run_eval.run(
            "https://free-will.app",
            [],
            release_id="release",
            model_id="model",
            config_id="config",
            strict=True,
        )


def test_saved_login_selects_the_default_api_but_never_overrides_environment(
    monkeypatch,
):
    monkeypatch.delenv("ELEUTHERIA_API_URL", raising=False)
    client_module.write_json(
        client_module.SESSION_PATH,
        {"api_root": "https://free-will.app/api", "access_token": "private-token"},
    )
    assert client_module.default_api_url() == "https://free-will.app"
    monkeypatch.setenv("ELEUTHERIA_API_URL", "http://localhost:8000")
    assert client_module.default_api_url() == "http://localhost:8000"


def test_quality_wrapper_preserves_equals_syntax_base_url(monkeypatch):
    from cli import main

    calls = []
    monkeypatch.setattr(main, "run_command", lambda cmd, **kw: calls.append(cmd) or 0)
    result = CliRunner().invoke(
        app,
        [
            "test",
            "answers",
            "--base-url=https://free-will.app",
            "--runner",
            "snapshot-lexical",
        ],
    )
    assert result.exit_code == 0
    assert "--base-url" not in calls[0]
    assert "--base-url=https://free-will.app" in calls[0]
    assert "--strict" in calls[0]


class UserCancelled(httpx.SyncByteStream):
    def __iter__(self):
        yield event("answer_final", VERDICT).encode()
        raise KeyboardInterrupt


def test_interrupt_keeps_an_already_received_verdict_with_cancel_exit_code():
    with client_for(
        "", handler=lambda _: httpx.Response(200, stream=UserCancelled())
    ) as client:
        payload, code = capture_query(
            "q", base_url="https://free-will.app", client=client
        )
    assert code == 130
    assert payload["passage_citations"] == [CITATION]
    assert payload["answer"] == VERDICT["answer"]
