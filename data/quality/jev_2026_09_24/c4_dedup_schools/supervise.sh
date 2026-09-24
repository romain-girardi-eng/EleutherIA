#!/bin/zsh
# Relaunch each resumable runner until a pass reports nothing left to do.
set -a; . ~/.config/vercel-ai-gateway/env; set +a
PY=../../../../.venv/bin/python
run_until_done() {
  local script=$1 conc=$2 log=$3
  while true; do
    while pgrep -f "$script" >/dev/null; do sleep 30; done
    $PY $script $conc > $log 2>&1
    grep -q "todo=0" $log && break
    sleep 20
  done
}
run_until_done run_school_propose_pw.py 6 sup_school_pw.log &
run_until_done run_dedup.py 8 sup_dedup.log &
wait
run_until_done run_school_propose.py 6 sup_school.log
echo SUPERVISOR-DONE
