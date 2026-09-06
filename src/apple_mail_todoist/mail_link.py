"""Pure Apple Mail message deep-link construction."""

from __future__ import annotations

from urllib.parse import quote


def normalize_rfc_message_id(raw: str) -> str:
    """Return the bare RFC Message-ID or fail closed on unstable input."""

    has_control = isinstance(raw, str) and any(
        ord(character) < 32 or ord(character) == 127 for character in raw
    )
    if not isinstance(raw, str) or has_control:
        raise ValueError("RFC Message-ID contains invalid control characters")
    value = raw.strip()
    if value.startswith("<") and value.endswith(">"):
        value = value[1:-1]
    elif value.startswith("<") or value.endswith(">"):
        raise ValueError("RFC Message-ID has unmatched brackets")
    if (
        not value
        or value.count("@") != 1
        or any(character.isspace() for character in value)
        or "<" in value
        or ">" in value
    ):
        raise ValueError("RFC Message-ID is missing or malformed")
    return value


def mail_message_url(raw_message_id: str) -> str:
    """Build the macOS ``message://`` URL with exactly one encoded bracket pair."""

    normalized = normalize_rfc_message_id(raw_message_id)
    return "message://" + quote(f"<{normalized}>", safe="")
