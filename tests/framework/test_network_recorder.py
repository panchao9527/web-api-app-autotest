from core.network_recorder import NetworkRecorder


class FakePage:
    def on(self, event, callback):
        self.event = event
        self.callback = callback


class FakeRequest:
    method = "POST"
    url = "https://example.test/api/login?token=query-secret"
    post_data = '{"username":"tester","password":"plain-password"}'


class FakeResponse:
    request = FakeRequest()
    status = 200

    def text(self):
        return '{"token":"response-secret","name":"tester"}'


def test_network_recorder_redacts_url_and_bodies():
    recorder = NetworkRecorder(FakePage(), capture_body=True)

    recorder._on_response(FakeResponse())

    serialized = str(recorder.calls)
    assert "query-secret" not in serialized
    assert "plain-password" not in serialized
    assert "response-secret" not in serialized
    assert "***" in serialized
