import json

import conftest


class FakePage:
    url = "https://example.test/result?token=query-secret"

    def screenshot(self):
        return b"web-png"

    def title(self):
        return "Result page"


class FakeDriver:
    current_package = "com.example.app"
    current_activity = ".ResultActivity"

    def get_screenshot_as_png(self):
        return b"app-png"


class FakeItem:
    funcargs = {"page": FakePage(), "app_driver": FakeDriver()}


def test_failure_evidence_contains_screenshots_and_safe_context(monkeypatch):
    attachments = []
    monkeypatch.setattr(
        "conftest.allure.attach",
        lambda body, name, attachment_type: attachments.append((body, name, attachment_type)),
    )

    conftest._attach_failure_evidence(FakeItem(), "teardown")

    names = [name for _, name, _ in attachments]
    assert "Web失败截图-teardown" in names
    assert "App失败截图-teardown" in names
    web_context = next(body for body, name, _ in attachments if name == "Web失败上下文-teardown")
    serialized = json.dumps(json.loads(web_context), ensure_ascii=False)
    assert "query-secret" not in serialized
    assert "***" in serialized
