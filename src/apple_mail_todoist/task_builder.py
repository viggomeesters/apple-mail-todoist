"""Deterministic conversion from selected mail metadata to a Todoist task."""

from __future__ import annotations

import unicodedata

from apple_mail_todoist.domain import SelectedMail, TaskDraft
from apple_mail_todoist.mail_link import mail_message_url

MONTHS = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)


def _single_line(value: str) -> str:
    without_controls = "".join(
        " " if unicodedata.category(character).startswith("C") else character
        for character in value
    )
    return " ".join(without_controls.split())


def build_task(selected: SelectedMail) -> TaskDraft:
    local_date = selected.received_at.astimezone().date()
    received = f"{local_date.day} {MONTHS[local_date.month - 1]} {local_date.year}"
    return TaskDraft(
        content=f"Reply to: {_single_line(selected.subject)}",
        description=(
            f"From: {_single_line(selected.sender_display)}\n"
            f"Received: {received}\n"
            f"[Open in Apple Mail]({mail_message_url(selected.rfc_message_id)})"
        ),
        labels=("mail",),
    )
