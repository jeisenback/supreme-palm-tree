from agents.pii_redactor import redact_text, redact_context


def test_redact_text_email_and_phone():
    s = "Contact: alice@example.org or +1 555-123-4567"
    r = redact_text(s)
    assert "[REDACTED_EMAIL]" in r
    assert "[REDACTED_PHONE]" in r


def test_redact_context_nested():
    ctx = {
        "title": "Hello bob@domain.com",
        "items": [
            {"note": "Call 555-321-9876"},
            "plain text with jane.doe@example.com"
        ]
    }
    out = redact_context(ctx)
    assert "[REDACTED_EMAIL]" in out["title"]
    assert "[REDACTED_PHONE]" in out["items"][0]["note"]
    assert "[REDACTED_EMAIL]" in out["items"][1]
