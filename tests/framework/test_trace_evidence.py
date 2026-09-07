import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import conftest

pytest_plugins = ["pytester"]


def test_teardown_failure_trace_is_attached_to_allure(pytester, monkeypatch):
    monkeypatch.setenv("PYTHONUTF8", "1")
    monkeypatch.delenv("PYTEST_ADDOPTS", raising=False)
    root = Path(__file__).resolve().parents[2]
    pytester.makeconftest(
        "import sys\nsys.path.insert(0, "
        + repr(str(root))
        + ")\n"
        + (root / "conftest.py").read_text(encoding="utf-8")
        + """
@pytest.fixture
def recorded(output_path):
    yield
    path = Path(output_path)
    path.mkdir(parents=True, exist_ok=True)
    (path / "trace.zip").write_bytes(b"offline-export")

@pytest.fixture
def broken_cleanup(recorded):
    yield
    raise RuntimeError("cleanup failed")
"""
    )
    pytester.makepyfile("""
def test_pass(recorded):
    pass

def test_cleanup(broken_cleanup):
    pass
""")
    result = pytester.runpytest_subprocess(
        "--tracing=retain-on-failure", "--alluredir=allure-results", "--output=evidence"
    )
    result.assert_outcomes(passed=2, errors=1)
    results = [
        json.loads(p.read_text(encoding="utf-8"))
        for p in (pytester.path / "allure-results").glob("*-result.json")
    ]
    failed = next(r for r in results if r["name"] == "test_cleanup")
    assert any(a["name"] == "Playwright trace.zip" for a in failed.get("attachments", []))
    assert len(list((pytester.path / "evidence").rglob("trace.zip"))) == 1


@pytest.mark.parametrize(
    "mode,failed,keep",
    [
        ("retain-on-failure", False, False),
        ("retain-on-failure", True, True),
        ("on", False, True),
    ],
)
def test_trace_retention_and_multiple_context_attachments(
    tmp_path, monkeypatch, mode, failed, keep
):
    traces = [tmp_path / "trace-1.zip", tmp_path / "trace-2.zip"]
    for trace in traces:
        trace.write_bytes(b"trace")
    attached = []
    monkeypatch.setattr(conftest.allure.attach, "file", lambda path, **kw: attached.append(path))
    item = SimpleNamespace(
        _web_output=tmp_path, _web_failed=failed, config=SimpleNamespace(_trace_retention=mode)
    )
    conftest._finish_web_traces(item)
    assert all(trace.exists() == keep for trace in traces)
    assert len(attached) == (2 if keep else 0)


def test_attachment_failure_preserves_original_trace(tmp_path, monkeypatch):
    trace = tmp_path / "trace.zip"
    trace.write_bytes(b"trace")

    def fail(*args, **kwargs):
        raise OSError("attachment failed")

    monkeypatch.setattr(conftest.allure.attach, "file", fail)
    item = SimpleNamespace(
        _web_output=tmp_path,
        _web_failed=True,
        config=SimpleNamespace(_trace_retention="retain-on-failure"),
    )
    conftest._finish_web_traces(item)
    assert trace.exists()
