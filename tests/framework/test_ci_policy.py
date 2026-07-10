from pathlib import Path


def test_dependency_files_are_split_by_test_type():
    for filename in [
        "requirements-api.txt",
        "requirements-web.txt",
        "requirements-app.txt",
        "requirements-infra.txt",
        "requirements-dev.txt",
    ]:
        assert Path(filename).is_file(), f"缺少依赖文件: {filename}"


def test_jenkins_parallel_jobs_use_separate_allure_directories():
    text = Path("Jenkinsfile").read_text(encoding="utf-8")

    assert "reports/allure-api" in text
    assert "reports/allure-web" in text


def test_github_workflow_has_framework_gate_and_pages_permission():
    text = Path(".github/workflows/automation-test.yml").read_text(encoding="utf-8")

    assert "framework-test:" in text
    assert "contents: write" in text
    assert "automation.py self-test" in text
    assert 'python-version: ["3.10", "3.11", "3.12"]' in text
