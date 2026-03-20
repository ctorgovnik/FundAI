#!/usr/bin/env python3
"""
Agent reader for the shared_memory integration test.

Attaches to the POSIX shmem segment written by the fund binary, drains the
ring buffer, and exits with code 0 when all expected items have been consumed
or with code 1 on any error.

Usage: agent.py <shmem_name> [<expected_items>]
  shmem_name     POSIX shmem name (e.g. /fundai-test-1234)
  expected_items number of items to wait for before exiting (default: 10)
"""

import mmap
import os
import struct
import sys
import time

POLL_TIMEOUT_S = 10.0
POLL_INTERVAL_S = 0.005

# Ring buffer header layout (matches ipc/ring_buffer.h):
#   uint64_t write_seq
#   uint64_t read_seq
#   uint64_t capacity
HEADER_FMT = "@QQQ"
HEADER_SIZE = struct.calcsize(HEADER_FMT)  # 24 bytes

# FundData layout (matches tests/integration/shared_memory_test/fund.cc):
#   int instrument_id  (4 bytes, offset 0)
#   [4 bytes alignment padding]
#   double close_price (8 bytes, offset 8)
ITEM_FMT = "@id"
ITEM_SIZE = struct.calcsize(ITEM_FMT)  # 16 bytes


def _wait_for(condition_fn: callable, timeout_s: float, interval_s: float) -> bool:
    deadline = time.monotonic() + timeout_s
    while not condition_fn():
        if time.monotonic() >= deadline:
            return False
        time.sleep(interval_s)
    return True


def main() -> int:
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <shmem_name> [<expected_items>]", file=sys.stderr)
        return 1

    shmem_name: str = sys.argv[1]
    expected: int = int(sys.argv[2]) if len(sys.argv) > 2 else 10

    # On Linux, POSIX shm lives in /dev/shm/; strip the leading slash.
    shm_path = f"/dev/shm/{shmem_name.lstrip('/')}"

    print(f"Agent: waiting for {shm_path} ...")
    appeared = _wait_for(lambda: os.path.exists(shm_path), POLL_TIMEOUT_S, POLL_INTERVAL_S)
    if not appeared:
        print(f"FAIL: {shm_path} did not appear within {POLL_TIMEOUT_S}s", file=sys.stderr)
        return 1

    with open(shm_path, "r+b") as f:
        mm = mmap.mmap(f.fileno(), 0)

        items_read = 0

        def _header():
            return struct.unpack_from(HEADER_FMT, mm, 0)

        # Wait for the first item to be produced.
        ready = _wait_for(
            lambda: _header()[0] > _header()[1],  # write_seq > read_seq
            POLL_TIMEOUT_S,
            POLL_INTERVAL_S,
        )
        if not ready:
            print("FAIL: no items appeared within timeout", file=sys.stderr)
            mm.close()
            return 1

        # Drain items until we have read `expected` total.
        deadline = time.monotonic() + POLL_TIMEOUT_S
        while items_read < expected:
            write_seq, read_seq, capacity = _header()

            if read_seq >= write_seq:
                # Buffer empty — wait for more.
                if time.monotonic() >= deadline:
                    print(
                        f"FAIL: timeout after reading {items_read}/{expected} items",
                        file=sys.stderr,
                    )
                    mm.close()
                    return 1
                time.sleep(POLL_INTERVAL_S)
                continue

            slot = read_seq % capacity
            offset = HEADER_SIZE + slot * ITEM_SIZE
            instrument_id, close_price = struct.unpack_from(ITEM_FMT, mm, offset)
            print(f"Agent read: instrument_id={instrument_id} close_price={close_price:.1f}")

            # Advance read_seq (write_seq is at offset 0, read_seq at offset 8).
            struct.pack_into("@Q", mm, 8, read_seq + 1)
            items_read += 1

        print(f"Agent: consumed {items_read} items — OK")
        mm.close()

    return 0


class SimpleAgent:
    """Stub retained for import compatibility; real logic is in main()."""
    pass


if __name__ == "__main__":
    sys.exit(main())
