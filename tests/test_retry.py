import pytest

from apg_automation.retry import retry


def test_retry_returns_result_after_transient_failures():
    attempts = {"count": 0}

    def flaky_operation():
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise RuntimeError("temporary")
        return "ok"

    assert retry(flaky_operation, attempts=3, delay_seconds=0) == "ok"
    assert attempts["count"] == 3


def test_retry_raises_last_error_after_attempts_are_exhausted():
    attempts = {"count": 0}

    def failing_operation():
        attempts["count"] += 1
        raise RuntimeError(f"failure {attempts['count']}")

    with pytest.raises(RuntimeError, match="failure 2"):
        retry(failing_operation, attempts=2, delay_seconds=0)
