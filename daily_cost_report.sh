#!/bin/bash
# Daily cost report — standalone, zero LLM tokens
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
NOTIFY_SCRIPT="${NOTIFY_SCRIPT:-/home/jd/src/calendar-agent/notify.sh}"

cd "$SCRIPT_DIR"
OUTPUT=$(python3 daily_cost_report.py 2>&1)
"$NOTIFY_SCRIPT" "$OUTPUT"
