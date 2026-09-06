import pytest

from apple_mail_todoist.mail_link import mail_message_url, normalize_rfc_message_id


@pytest.mark.parametrize(
    ("raw", "normalized"),
    [
        ("synthetic-123@example.invalid", "synthetic-123@example.invalid"),
        (" <synthetic-123@example.invalid> ", "synthetic-123@example.invalid"),
    ],
)
def test_mail_message_url_normalizes_and_encodes_one_bracket_pair(
    raw: str, normalized: str
) -> None:
    assert normalize_rfc_message_id(raw) == normalized
    assert mail_message_url(raw) == (
        "message://%3Csynthetic-123%40example.invalid%3E"
    )


@pytest.mark.parametrize(
    "raw",
    ["", "   ", "missing-at", "<missing-end", "missing-start>", "a@example.invalid\n"],
)
def test_mail_message_url_rejects_missing_or_malformed_identity(raw: str) -> None:
    with pytest.raises(ValueError, match="RFC Message-ID"):
        mail_message_url(raw)
