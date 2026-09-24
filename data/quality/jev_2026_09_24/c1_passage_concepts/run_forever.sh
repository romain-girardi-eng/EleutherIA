#!/bin/bash
# Self-healing wrapper: restarts run_c1.py until its todo count hits 0.
# Each run_c1.py invocation already catches per-request exceptions and never
# aborts on a single bad response; this loop only guards against the whole
# process dying (OOM, network stack fault, killed signal, unhandled exception).
#
# Env vars: C1_MODE (all|chunked|passage_only|concepts_only, default all),
#           C1_CONCURRENCY (default 8), C1_IDS_FILE (optional, for concepts_only).
cd "$(dirname "$0")"
set -a; . ~/.config/vercel-ai-gateway/env; set +a
PY=/Users/romaingirardi/Projects/EleutherIA/.venv/bin/python
MODE="${C1_MODE:-all}"
CONC="${C1_CONCURRENCY:-8}"
IDS_ARGS=()
if [ -n "$C1_IDS_FILE" ]; then
  IDS_ARGS=(--ids-file "$C1_IDS_FILE")
fi

while true; do
  echo "$(date '+%F %T') launching run_c1.py --mode $MODE --concurrency $CONC ${IDS_ARGS[*]}" >> run_c1.log
  $PY run_c1.py --mode "$MODE" --concurrency "$CONC" "${IDS_ARGS[@]}" >> run_c1.log 2>&1
  code=$?
  remaining=$($PY - "$MODE" "$C1_IDS_FILE" <<'PY'
import json, sys
mode = sys.argv[1]
ids_file = sys.argv[2] if len(sys.argv) > 2 else ""

chunks_seen = {}
for line in open("results.jsonl", encoding="utf-8"):
    if not line.strip():
        continue
    r = json.loads(line)
    chunks_seen.setdefault(r["id"], set()).add(r["chunk"])

cands = [json.loads(l)["id"] for l in open("candidates.jsonl", encoding="utf-8") if l.strip()]
if ids_file:
    order = [x.strip() for x in open(ids_file, encoding="utf-8") if x.strip()]
    wanted = set(order)
    cands = [pid for pid in cands if pid in wanted]

if mode == "passage_only":
    covered = lambda s: "all" in s or "passage_level" in s or 0 in s
elif mode == "concepts_only":
    covered = lambda s: "all" in s or "concepts_only" in s or all(ci in s for ci in range(4))
elif mode == "chunked":
    covered = lambda s: all(ci in s for ci in range(4))
else:
    covered = lambda s: "all" in s or all(ci in s for ci in range(4))

todo = sum(1 for pid in cands if not covered(chunks_seen.get(pid, set())))
print(todo)
PY
)
  echo "$(date '+%F %T') run_c1.py exited code=$code, remaining=$remaining" >> run_c1.log
  if [ "$remaining" -eq 0 ]; then
    echo "$(date '+%F %T') STAGE DONE (mode=$MODE)" >> run_c1.log
    break
  fi
  sleep 5
done
