"""
Tests for TOCTOU race condition fix in job claiming.

Verifies that the atomic UPDATE...RETURNING prevents race conditions (CWE-367).
"""

import pytest
from casare_rpa.infrastructure.queue.pgqueuer_consumer import PgQueuerConsumer


class TestAtomicJobClaiming:
    """Test that job claiming is atomic and prevents TOCTOU race conditions."""

    def test_claim_job_query_is_atomic(self):
        """
        Test that the SQL_CLAIM_JOB_ATOMIC query uses UPDATE...RETURNING.

        This is a static analysis test - verifies the SQL structure prevents
        the race condition by combining SELECT and UPDATE in one operation.
        """
        query = PgQueuerConsumer.SQL_CLAIM_JOB_ATOMIC

        # Verify it's a single UPDATE statement (not SELECT then UPDATE)
        assert query.strip().upper().startswith("UPDATE")

        # Verify it uses RETURNING clause
        assert "RETURNING" in query.upper()

        # Verify it uses FOR UPDATE SKIP LOCKED in subquery
        assert "FOR UPDATE SKIP LOCKED" in query.upper()

        # Verify the WHERE id IN (SELECT...) pattern (atomic)
        assert "WHERE ID IN" in query.upper()

        # Verify no separate SELECT statement (would indicate TOCTOU)
        query_lines = query.strip().split("\n")
        update_count = sum(
            1 for line in query_lines if line.strip().upper().startswith("UPDATE")
        )
        assert (
            update_count == 1
        ), "Should have exactly one UPDATE statement (atomic operation)"

    def test_no_separate_select_for_update_query(self):
        """
        Verify there's no vulnerable SELECT...FOR UPDATE + UPDATE pattern.

        The OLD (vulnerable) pattern was:
        1. SELECT ... FOR UPDATE SKIP LOCKED (get job IDs)
        2. UPDATE ... WHERE id IN (...) (claim jobs)

        Between step 1 and 2, another transaction could interfere (TOCTOU).

        The NEW (secure) pattern is:
        UPDATE ... WHERE id IN (SELECT ... FOR UPDATE SKIP LOCKED) RETURNING ...

        This is a single atomic operation.
        """
        # Ensure the class doesn't have a separate SELECT query constant
        assert not hasattr(
            PgQueuerConsumer, "SQL_CLAIM_JOB_SELECT"
        ), "Should not have separate SELECT query"
        assert not hasattr(
            PgQueuerConsumer, "SQL_CLAIM_JOB_UPDATE"
        ), "Should not have separate UPDATE query"

        # Ensure we only have the atomic version
        assert hasattr(PgQueuerConsumer, "SQL_CLAIM_JOB_ATOMIC")

    def test_atomic_query_parameters_are_secure(self):
        """
        Verify that all dynamic values in the atomic query use parameters.

        This ensures no SQL injection vulnerabilities in the claiming logic.
        """
        query = PgQueuerConsumer.SQL_CLAIM_JOB_ATOMIC

        # Count parameter placeholders ($1, $2, $3, $4)
        assert "$1" in query  # robot_id
        assert "$2" in query  # visibility_timeout_seconds
        assert "$3" in query  # environment
        assert "$4" in query  # batch_size

        # Ensure no string concatenation or format placeholders
        assert "{" not in query, "Should not use .format() for SQL"
        assert "%" not in query or "%" in "SKIP LOCKED", "Should not use % formatting"

    def test_query_updates_all_required_fields_atomically(self):
        """
        Verify the atomic query sets all required fields in one operation.

        This ensures consistency - either ALL fields are updated or NONE.
        """
        query = PgQueuerConsumer.SQL_CLAIM_JOB_ATOMIC

        # Verify all critical fields are set in the UPDATE
        required_sets = [
            "status = 'running'",
            "robot_id = $1",
            "started_at = NOW()",
            "visible_after = NOW()",
        ]

        for field_set in required_sets:
            assert (
                field_set in query
            ), f"Atomic query must set {field_set} to prevent partial updates"

    def test_other_queries_use_parameters(self):
        """
        Verify that all other job management queries use parameterized queries.

        This prevents SQL injection across all operations.
        """
        queries_to_check = [
            ("SQL_EXTEND_LEASE", 3),  # $1, $2, $3
            ("SQL_COMPLETE_JOB", 3),  # $1, $2, $3
            ("SQL_FAIL_JOB", 3),  # $1, $2, $3
            ("SQL_RELEASE_JOB", 2),  # $1, $2
            ("SQL_REQUEUE_TIMED_OUT", 1),  # $1
            ("SQL_UPDATE_PROGRESS", 4),  # $1, $2, $3, $4
            ("SQL_GET_JOB_STATUS", 1),  # $1
        ]

        for query_name, expected_params in queries_to_check:
            assert hasattr(PgQueuerConsumer, query_name), f"Missing query: {query_name}"

            query = getattr(PgQueuerConsumer, query_name)

            # Verify all expected parameters are present
            for i in range(1, expected_params + 1):
                assert f"${i}" in query, f"{query_name} should use parameter ${i}"

            # Verify no string formatting
            assert "{" not in query, f"{query_name} should not use .format()"


class TestConsumerConfigValidation:
    """Test that ConsumerConfig validates robot_id on construction."""

    def test_robot_id_validated_on_init(self):
        """Test that invalid robot_id is rejected during config construction."""
        from casare_rpa.infrastructure.queue.pgqueuer_consumer import ConsumerConfig

        # Valid robot_id should work
        valid_config = ConsumerConfig(
            postgres_url="postgresql://localhost/test", robot_id="robot-001"
        )
        assert valid_config.robot_id == "robot-001"

        # Invalid robot_id with SQL injection should fail
        with pytest.raises(ValueError, match="Invalid robot_id"):
            ConsumerConfig(
                postgres_url="postgresql://localhost/test",
                robot_id="'; DROP TABLE robots; --",
            )

    def test_config_to_dict_masks_credentials(self):
        """Test that to_dict() masks sensitive credentials (Fix #5)."""
        from casare_rpa.infrastructure.queue.pgqueuer_consumer import ConsumerConfig

        config = ConsumerConfig(
            postgres_url="postgresql://user:password@localhost/db", robot_id="robot-001"
        )

        safe_dict = config.to_dict()

        # Credentials should be masked
        assert safe_dict["postgres_url"] == "***"

        # Non-sensitive fields should be present
        assert safe_dict["robot_id"] == "robot-001"
        assert safe_dict["environment"] == "default"


@pytest.mark.asyncio
async def test_claim_batch_validates_job_ids():
    """
    Integration test: Verify that job IDs returned from claim_batch are validated.

    This is a smoke test - actual database testing would require test DB setup.
    """
    from casare_rpa.infrastructure.security import validate_job_id

    # Simulate job IDs that would come from database
    valid_job_ids = [
        "12345678-1234-1234-1234-123456789012",
        "abcdef01-2345-6789-abcd-ef0123456789",
    ]

    # All should pass validation
    for job_id in valid_job_ids:
        assert validate_job_id(job_id) == job_id

    # Malformed job IDs should fail
    invalid_job_ids = [
        "not-a-uuid",
        "'; DROP TABLE jobs; --",
        "",
    ]

    for job_id in invalid_job_ids:
        with pytest.raises(ValueError):
            validate_job_id(job_id)
