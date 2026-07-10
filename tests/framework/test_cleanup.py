import pytest

from fixtures.api_fixtures import CleanupError, CleanupRegistry


def raise_cleanup_error():
    raise RuntimeError("cleanup failed")


def test_cleanup_runs_in_reverse_and_reports_failures():
    calls = []
    registry = CleanupRegistry()
    registry.add_callback(lambda: calls.append("first"))
    registry.add_callback(raise_cleanup_error)
    registry.add_callback(lambda: calls.append("last"))

    with pytest.raises(CleanupError, match="cleanup failed") as exc_info:
        registry.run()

    assert calls == ["last", "first"]
    assert len(exc_info.value.errors) == 1
