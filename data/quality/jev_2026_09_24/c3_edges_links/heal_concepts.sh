#!/bin/bash
# Self-healing driver for run_concepts.py: reruns until candidates == results, or
# gives up after MAX_ROUNDS with no progress.
set -u
cd "$(dirname "$0")"
PY=/Users/romaingirardi/Projects/EleutherIA/.venv/bin/python3
TOTAL=$(wc -l < candidates_B.jsonl)
MAX_ROUNDS=20
round=0
last_done=-1
while [ "$round" -lt "$MAX_ROUNDS" ]; do
  done_n=$(wc -l < results_B.jsonl 2>/dev/null || echo 0)
  if [ "$done_n" -ge "$TOTAL" ]; then
    echo "healed: $done_n/$TOTAL"
    break
  fi
  if [ "$done_n" -eq "$last_done" ]; then
    echo "no progress this round, backing off 20s"
    sleep 20
  fi
  last_done=$done_n
  round=$((round + 1))
  echo "=== heal round $round, done $done_n/$TOTAL ==="
  "$PY" run_concepts.py
done
echo "heal_concepts.sh finished, rounds=$round, results=$(wc -l < results_B.jsonl)/$TOTAL"
