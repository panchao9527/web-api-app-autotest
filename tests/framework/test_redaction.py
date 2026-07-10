from utils.redaction import redact, redact_text, redact_url


def test_redact_masks_nested_sensitive_values_without_mutating_input():
    value = {
        "username": "tester",
        "password": "plain-password",
        "nested": {"access_token": "secret-token"},
        "items": [{"phone": "13800138000"}],
    }

    result = redact(value)

    assert result["username"] == "tester"
    assert result["password"] == "***"
    assert result["nested"]["access_token"] == "***"
    assert result["items"][0]["phone"] == "***"
    assert value["password"] == "plain-password"


def test_redact_matches_sensitive_keys_case_insensitively():
    assert redact({"Authorization": "Bearer abc"}) == {"Authorization": "***"}


def test_redact_url_masks_sensitive_query_parameters():
    result = redact_url("https://example.test/login?token=abc&page=1")

    assert "token=%2A%2A%2A" in result
    assert "page=1" in result
    assert "abc" not in result


def test_redact_text_masks_common_key_value_formats():
    text = 'password=plain token: "secret-token" username=tester'

    result = redact_text(text)

    assert "plain" not in result
    assert "secret-token" not in result
    assert "username=tester" in result
