import pytest

from utils.retry import retry


def test_retry_preserves_function_metadata():
    @retry(times=1, delay=0)
    def operation():
        """operation docs"""
        return "ok"

    assert operation.__name__ == "operation"
    assert operation.__doc__ == "operation docs"


def test_retry_rejects_zero_attempts():
    with pytest.raises(ValueError, match="times"):
        retry(times=0)


def test_retry_does_not_sleep_after_final_failure(monkeypatch):
    sleeps = []
    monkeypatch.setattr("utils.retry.time.sleep", lambda delay: sleeps.append(delay))

    @retry(times=2, delay=1)
    def always_fails():
        raise RuntimeError("failed")

    with pytest.raises(RuntimeError, match="failed"):
        always_fails()

    assert sleeps == [1]
