from scripts.automation import (
    build_pytest_command,
    create_parser,
    main,
    normalize_pytest_exit_code,
    playwright_browser_installed,
    run_app_smoke,
)


def test_build_web_command_preserves_cli_options():
    command, env = build_pytest_command(
        test_type="web",
        environment="uat",
        marker="smoke",
        headed=True,
        browser="firefox",
        slowmo=500,
        tracing="retain-on-failure",
        allow_prod=False,
    )

    assert command[:3] == ["-m", "pytest", "testcases/web"]
    assert command[command.index("-m", 2) + 1] == "web and smoke"
    assert "--headed" in command
    assert command[-2:] == ["--tracing", "retain-on-failure"]
    assert env["ENV"] == "uat"
    assert env["PYTHONUTF8"] == "1"


def test_build_api_command_keeps_marker_optional():
    command, _ = build_pytest_command(
        test_type="api",
        environment="sit",
        marker=None,
        headed=False,
        browser=None,
        slowmo=0,
        tracing=None,
        allow_prod=False,
    )

    assert command[:3] == ["-m", "pytest", "testcases/api"]
    assert command[command.index("-m", 2) + 1] == "api"
    assert "--headed" not in command


def test_no_business_tests_fail_by_default_and_can_be_explicitly_allowed():
    assert normalize_pytest_exit_code(5) == 5
    assert normalize_pytest_exit_code(5, allow_empty=True) == 0
    assert normalize_pytest_exit_code(1) == 1


def test_playwright_browser_check_uses_cache_without_starting_driver(tmp_path):
    (tmp_path / "chromium-1234").mkdir()

    assert playwright_browser_installed([tmp_path], "chromium") is True
    assert playwright_browser_installed([tmp_path], "firefox") is False


def test_prod_blocking_returns_clear_cli_error(monkeypatch, capsys):
    monkeypatch.delenv("ALLOW_PROD_TESTS", raising=False)

    exit_code = main(["test", "--type", "api", "--env", "prod"])

    assert exit_code == 2
    assert "[失败]" in capsys.readouterr().out


def test_parser_supports_app_specific_doctor_and_smoke():
    parser = create_parser()

    doctor_args = parser.parse_args(["doctor", "--env", "uat", "--type", "app"])
    smoke_args = parser.parse_args(["app-smoke", "--env", "sit"])

    assert doctor_args.type == "app"
    assert smoke_args.command == "app-smoke"
    assert smoke_args.env == "sit"


def test_app_smoke_is_blocked_in_prod_by_default(monkeypatch, capsys):
    monkeypatch.delenv("ALLOW_PROD_TESTS", raising=False)

    assert run_app_smoke("prod") == 2
    assert "[失败]" in capsys.readouterr().out
