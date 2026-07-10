from core.web_driver import (
    configured_browsers,
    configured_tracing,
    merge_launch_args,
)


def test_cli_launch_options_override_yaml_options():
    yaml_args = {"headless": True, "slow_mo": 0}
    cli_args = {"headless": False, "slow_mo": 800}

    assert merge_launch_args(yaml_args, cli_args) == cli_args


def test_yaml_browser_is_used_when_cli_browser_is_missing():
    assert configured_browsers([], "firefox") == ["firefox"]


def test_cli_browsers_override_yaml_browser():
    assert configured_browsers(["webkit"], "firefox") == ["webkit"]


def test_yaml_trace_is_used_only_without_explicit_cli_option():
    assert configured_tracing("off", [], trace_enabled=True) == "retain-on-failure"
    assert configured_tracing("off", ["pytest", "--tracing=off"], trace_enabled=True) == "off"
