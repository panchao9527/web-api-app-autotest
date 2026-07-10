from pathlib import Path


def test_default_pytest_entry_only_targets_framework_tests():
    config = Path("pytest.ini").read_text(encoding="utf-8")

    assert "testpaths = tests/framework" in config
    assert "--reruns" not in config
