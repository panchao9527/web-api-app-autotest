from pathlib import Path


def test_project_uses_one_dependency_file():
    assert Path("requirements.txt").is_file()
    split_files = list(Path().glob("requirements-*.txt"))
    assert split_files == [], f"应只保留 requirements.txt，发现: {split_files}"

    for filename in [
        ".github/workflows/automation-test.yml",
        ".gitlab-ci.yml",
        "Jenkinsfile",
    ]:
        text = Path(filename).read_text(encoding="utf-8")
        assert "requirements.txt" in text
        assert "requirements-api.txt" not in text
        assert "requirements-web.txt" not in text
        assert "requirements-dev.txt" not in text


def test_project_uses_one_operation_manual():
    manuals = list(Path("docs").rglob("*.md"))
    assert manuals == [Path("docs/自动化测试框架操作手册.md")]

    readme = Path("README.md").read_text(encoding="utf-8")
    assert "docs/自动化测试框架操作手册.md" in readme


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
