import pytest

from scripts.notify_from_junit import collect


def test_collect_counts_testcases_without_double_counting_nested_suites(tmp_path):
    report = tmp_path / "junit.xml"
    report.write_text(
        """<?xml version="1.0" encoding="utf-8"?>
<testsuite name="root" tests="3" failures="1" skipped="1" time="0.6">
  <testsuite name="child" tests="3" failures="1" skipped="1" time="0.6">
    <testcase name="passed" time="0.1" />
    <testcase name="failed" time="0.2"><failure message="boom" /></testcase>
    <testcase name="skipped" time="0.3"><skipped /></testcase>
  </testsuite>
</testsuite>
""",
        encoding="utf-8",
    )

    total, passed, failed, duration = collect(str(tmp_path))

    assert (total, passed, failed) == (3, 1, 1)
    assert duration == pytest.approx(0.6)
