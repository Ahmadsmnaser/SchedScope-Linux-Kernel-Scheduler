#!/bin/sh

TRACE_DIR="/sys/kernel/debug/tracing"
TRACE_OUT="/tmp/trace_pipe.log"

mount -t debugfs none /sys/kernel/debug

if [ ! -d "$TRACE_DIR" ]; then
	echo "[TRACE] tracing directory not available"
	exit 1
fi

echo > "$TRACE_DIR/trace"

cat "$TRACE_DIR/trace_pipe" > "$TRACE_OUT" &
TRACE_PID=$!

/workloads/run_mixed_workload.sh

sleep 1
kill "$TRACE_PID" 2>/dev/null
wait "$TRACE_PID" 2>/dev/null

echo "[TRACE] raw trace stream saved to $TRACE_OUT"
grep '\[SCHED_TRACE\]' "$TRACE_OUT"
