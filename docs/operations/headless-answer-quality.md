# Headless answer-quality testing

Use the repository's Python 3.14 environment. No browser, browser automation, or
LLM provider key is needed on the client: it calls the authenticated SSE endpoint
used by free-will.app.

## Connect once

```bash
export ELEUTHERIA_API_URL=https://free-will.app
.venv/bin/eleutheria login --email YOUR_EMAIL --request-code
```

Enter the emailed OTP into a private temporary file, then exchange it without
putting the code in process arguments:

```bash
.venv/bin/eleutheria login --email YOUR_EMAIL --code-file /path/to/private-otp.txt
```

Remove that temporary file afterwards. An interactive terminal can instead use
`eleutheria login --email YOUR_EMAIL` and enter the code at the hidden prompt.
The saved session is mode 0600 at `~/.config/eleutheria/session.json`, scoped to the
API origin. Subsequent CLI commands reuse that origin unless `ELEUTHERIA_API_URL` or `--base-url` overrides it. The token is never forwarded to a different API. For CI, inject
`ELEUTHERIA_API_TOKEN` or use `ELEUTHERIA_TOKEN_FILE` / `--token-file`; do not put
the bearer token in a shell command or commit it.

## Capture an answer and its evidence

```bash
.venv/bin/eleutheria ask \
  'Dans Cicéron, De fato 41, quelle distinction de causes est attribuée à Chrysippe ? Réponds en 200 mots au plus, avec la référence exacte et les limites du témoignage.' \
  --base-url https://free-will.app \
  --fresh --json --output /tmp/cicero-answer.json
```

- `--fresh` bypasses the answer cache for an actual test.
- `--model` selects the same model key as the website; default `auto`.
- `--mode deep` / legacy `--thinking` selects the real deep mode.
- `--timeout` sets the network timeout, default 1200 seconds rather than the old
  CLI's 30 seconds. Cancellation through Ctrl+C closes the HTTP stream.
- JSON stdout contains only the result, never a spinner or Rich formatting.
- The output includes published prose, citations, claim ledger, publication gate,
  trace ID and `_cli` transport/timing fields. It excludes provisional prose and
  private draft diagnostics. Output files are atomic writes with mode 0600.
- EOF or a broken connection after `answer_final` preserves the received verdict
  and evidence. A transport failure still returns a failing exit code.

| Exit | Meaning |
|---:|---|
| 0 | A complete published answer was received; this is not a claim of infallibility |
| 2 | Answer withheld or partial; also used by argument validation |
| 3 | HTTP, transport, parsing or artifact I/O failure |
| 4 | Authentication failed or expired |
| 130 | Cancelled with Ctrl+C; an already received verdict is retained |

Always inspect `metadata.publication_gate` and the actual sources. A partial
answer can be useful for investigation while still failing a quality test.
Do not retry blindly: fix or narrow the evidence problem recorded in the report.

## Run the evaluation harness

```bash
.venv/bin/eleutheria test answers \
  --runner snapshot-lexical --include-ood --include-repair-wave \
  --output /tmp/retrieval-eval.json

.venv/bin/eleutheria test answers --validate /tmp/retrieval-eval.json
.venv/bin/eleutheria test answers --help
```

The CLI test wrapper enables `--strict`: invalid gold, individual query/gate
failures, or missing required safety coverage cause a nonzero exit. Schema
validation is a separate operation; a structurally valid report can describe
poor results. The underlying Python harness still supports non-strict diagnostic
capture when explicitly invoked directly.

For live evaluation, select reviewed gold cases and record the exact deployment,
model and configuration:

```bash
.venv/bin/eleutheria test answers \
  --runner live-http --queries /path/to/reviewed-cases.yaml \
  --base-url https://free-will.app \
  --release-id EXACT_RELEASE --model-id EXACT_MODEL --config-id EXACT_CONFIG \
  --output /tmp/live-eval.json
```

Live evaluation shares the CLI authentication. Invalid gold is rejected before
sending any live query. The full default gold set currently contains unresolved
identifiers, so it must not be advertised as a clean release benchmark. See the
[runbook](graphrag-eval-runbook.md) for case binding and channel definitions.

The evaluation harness retains internal raw traces for investigation; unlike
`ask --json`, those are diagnostic artifacts and can include provisional output.
Keep them private. No request authorization headers are written to artifacts.

## Ordinary regression tests

`eleutheria test frontend` now passes `--run` and exits rather than watching.
Python test and quality commands use the CLI's own interpreter rather than an
unrelated `pytest`, `ruff` or `mypy` executable from PATH.
