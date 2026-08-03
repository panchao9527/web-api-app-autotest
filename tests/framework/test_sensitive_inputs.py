from pages.base_page import BasePage
from screens.base_screen import BaseScreen


class FakeElement:
    def clear(self):
        pass

    def send_keys(self, text):
        self.text = text


class FakeWebPage:
    def __init__(self):
        self.calls = []

    def fill(self, selector, text):
        self.calls.append((selector, text))


def test_web_password_input_is_not_written_to_log(monkeypatch):
    messages = []
    page = FakeWebPage()
    monkeypatch.setattr("pages.base_page.log.info", messages.append)

    BasePage(page).fill("[data-testid='password']", "plain-password")

    assert page.calls == [("[data-testid='password']", "plain-password")]
    assert all("plain-password" not in message for message in messages)
    assert any("***" in message for message in messages)


def test_app_sensitive_input_is_not_written_to_log(monkeypatch):
    messages = []
    screen = BaseScreen(object())
    element = FakeElement()
    monkeypatch.setattr(screen, "find", lambda *_: element)
    monkeypatch.setattr("screens.base_screen.log.info", messages.append)

    screen.input("id", "password_input", "plain-password")

    assert element.text == "plain-password"
    assert all("plain-password" not in message for message in messages)
    assert any("***" in message for message in messages)
