"""Dead Letter Queue unit test — Phase 6-07."""

import os
import sys
import tempfile

# Ensure we can import from edge/agent
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from buffer import DuckDBBuffer


def test_dead_letter_queue():
    """Test dead letter flow: write → reject 3x → skip → no unsynced remain."""
    tmp = tempfile.mktemp(suffix=".duckdb")
    try:
        buffer = DuckDBBuffer(tmp)

        # Write 5 test measurements
        for i in range(5):
            buffer.write([{
                "timestamp": f"2026-07-01T00:00:0{i}Z",
                "signal_id": f"TEST.DEAD.{i}",
                "value": float(i),
                "quality": "GOOD",
                "source": "test",
            }])

        assert buffer.count_unsynced() == 5, "Expected 5 unsynced after write"

        # Simulate 3 rejections (increment retry_count for all 5 rows)
        for iteration in range(3):
            buffer.increment_retry_count(5)
            unsynced = buffer.get_unsynced(100, max_retries=3)
            expected_remaining = 5  # Still all rows have rc < 3 after 2 increments
            if iteration == 2:
                expected_remaining = 0  # After 3 increments, rc=3 >= max_retries=3
            print(f"  Iteration {iteration+1}: increment_retry_count(5) → "
                  f"unsynced={len(unsynced)} (expected {expected_remaining})")

        # Verify get_unsynced with max_retries=3 excludes dead letters
        remaining = buffer.get_unsynced(100, max_retries=3)
        assert len(remaining) == 0, (
            f"Expected 0 unsynced after 3 retries, got {len(remaining)}"
        )

        # Now skip dead letters
        skipped = buffer.skip_dead_letters(3)
        print(f"  skip_dead_letters: {skipped} rows skipped (expected 5)")
        assert skipped == 5, f"Expected 5 skipped, got {skipped}"

        # Verify no unsynced remain
        final_unsynced = buffer.count_unsynced()
        assert final_unsynced == 0, (
            f"Expected 0 unsynced after dead letter skip, got {final_unsynced}"
        )

        print("✅ test_dead_letter_queue PASSED")

    finally:
        buffer.close()
        os.remove(tmp)


def test_migration_no_data_loss():
    """Test that ALTER TABLE ADD COLUMN works on existing DB without data loss."""
    tmp = tempfile.mktemp(suffix=".duckdb")
    try:
        # Create old schema (without retry_count)
        import duckdb
        conn = duckdb.connect(tmp)
        conn.execute("""
            CREATE TABLE measurements (
                ts          TIMESTAMPTZ NOT NULL,
                signal_id   VARCHAR NOT NULL,
                value       DOUBLE,
                quality     VARCHAR,
                source      VARCHAR,
                synced      BOOLEAN DEFAULT FALSE
            )
        """)
        conn.execute("""
            INSERT INTO measurements (ts, signal_id, value, quality, source, synced)
            VALUES ('2026-07-01T00:00:00Z', 'TEST.1', 42.0, 'GOOD', 'test', FALSE)
        """)
        conn.close()

        # Open with new code — should migrate
        buffer = DuckDBBuffer(tmp)
        assert buffer.count_unsynced() == 1, "Expected 1 unsynced after migration"
        unsynced = buffer.get_unsynced(10)
        assert len(unsynced) == 1, "Expected 1 unsynced row"
        assert unsynced[0]["retry_count"] == 0, "Expected retry_count=0"
        assert unsynced[0]["value"] == 42.0, "Expected value=42.0"

        # Test dead letter still works after migration
        buffer.increment_retry_count(1)
        assert buffer.skip_dead_letters(3) == 0  # rc=1 < 3, not yet dead
        buffer.increment_retry_count(1)
        buffer.increment_retry_count(1)
        assert buffer.skip_dead_letters(3) == 1  # rc=3 >= 3, now dead
        assert buffer.count_unsynced() == 0

        print("✅ test_migration_no_data_loss PASSED")

    finally:
        buffer.close()
        os.remove(tmp)


if __name__ == "__main__":
    test_dead_letter_queue()
    test_migration_no_data_loss()
    print("\n🎉 All dead letter tests passed!")
