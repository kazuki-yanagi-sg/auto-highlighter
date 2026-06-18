#!/bin/bash
input=$(cat)

MODEL=$(echo "$input" | jq -r '.model.display_name // "unknown"')
PERCENT=$(echo "$input" | jq -r '(.context_window.used_percentage // 0) | round')
ADDED=$(echo "$input" | jq -r '.cost.total_lines_added // 0')
REMOVED=$(echo "$input" | jq -r '.cost.total_lines_removed // 0')

printf '\033[36m%s\033[0m | Context: %s%% | +%s/-%s lines\n' "$MODEL" "$PERCENT" "$ADDED" "$REMOVED"
