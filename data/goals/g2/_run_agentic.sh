#!/usr/bin/env bash
# Run the agentic GraphRAG eval against the warmed prod backend (via SSH tunnel
# on :18000), with the faithfulness judge fetching passage text from the BM25
# baseline service (:8011, same data/corpus snapshot the gold was annotated on),
# because the prod /api/passages endpoint requires auth (401).
#
# Prereqs (already running):
#   - SSH tunnel localhost:18000 -> host:8015 (agentic API)
#   - BM25 baseline service on :8011 (serves passage text for the judge)
#   - cache warmed on the host so uncached ReAct latency doesn't blow the timeout
set -euo pipefail
cd "$(dirname "$0")/../../.."

set -a; . ./.env; set +a
export PYTHONPATH="graphrag/src:knowledge graph/src:database/src:."
export ELEUTHERIA_EVAL_JUDGE=1
export ELEUTHERIA_EVAL_PASSAGE_URL="http://localhost:8011"
export ELEUTHERIA_EVAL_TIMEOUT="${ELEUTHERIA_EVAL_TIMEOUT:-800}"

.venv/bin/python tests/eval/run_eval.py \
    --base-url http://localhost:18000 \
    --queries tests/eval/queries.yaml \
    --output data/goals/g2/run_graphrag.json
