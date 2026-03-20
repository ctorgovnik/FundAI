#!/usr/bin/env bash
# Integration test: shared_memory_test
#
# Starts the fund binary (producer) and agent.py (consumer) concurrently,
# waits for both to finish, and exits non-zero if either crashed.
#
# Usage: run.sh [<build_dir>]
#   build_dir  path to the CMake build output directory (default: build)

set -euo pipefail

BUILD_DIR="${1:-build}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SHMEM_NAME="/fundai-shmem-$$"

cleanup() {
    # Best-effort removal of lingering shmem segment.
    rm -f "/dev/shm/${SHMEM_NAME#/}" 2>/dev/null || true
}
trap cleanup EXIT

echo "==> shared_memory_test"
echo "    build : $BUILD_DIR"
echo "    shmem : $SHMEM_NAME"

FUND_BIN="$BUILD_DIR/bin/fund"
if [[ ! -x "$FUND_BIN" ]]; then
    echo "FAIL: fund binary not found at $FUND_BIN" >&2
    exit 1
fi

# Start producer and consumer concurrently.
"$FUND_BIN" "$SHMEM_NAME" &
FUND_PID=$!

python3 "$SCRIPT_DIR/agent.py" "$SHMEM_NAME" 10 &
AGENT_PID=$!

# Collect exit codes — `wait` returns the process's exit status.
FUND_EXIT=0
AGENT_EXIT=0

wait "$FUND_PID"  || FUND_EXIT=$?
wait "$AGENT_PID" || AGENT_EXIT=$?

if [[ $FUND_EXIT -ne 0 ]]; then
    echo "FAIL: fund binary exited with code $FUND_EXIT" >&2
    exit 1
fi

if [[ $AGENT_EXIT -ne 0 ]]; then
    echo "FAIL: agent.py exited with code $AGENT_EXIT" >&2
    exit 1
fi

echo "PASS: shared_memory_test"
