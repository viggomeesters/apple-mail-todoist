# Redacted Live Verification

The release candidate was exercised locally on 6 September 2026 with one deliberately selected disposable message and one disposable Todoist task. No subject, sender, Message-ID, task ID, credential, response body, or screenshot containing correspondence was retained.

## Environment

- macOS 26.6.2 (25G83)
- Apple Mail 16.0
- Raycast 1.104.28
- Python 3.12.13
- official Todoist CLI 5.2.1, browser OAuth, read-write scope, secure OS credential store

## Proven behavior

| Check | Result |
|---|---|
| Exactly one selected Mail message accepted | Pass |
| Raycast command returned immediately with `Creating Todoist task` | Pass |
| Official CLI returned a confirmed task ID | Pass |
| Remote content and description matched the deterministic draft exactly | Pass |
| Description contained the exact encoded `message://` link | Pass |
| `mail` label was present | Pass |
| Due date and deadline were absent | Pass |
| A second capture returned the existing task without another mutation | Pass |
| Opening the deep link resolved to the exact selected Mail message | Pass |
| Read, flagged, mailbox, and selection identity were unchanged | Pass |
| Disposable remote task and local reconciliation files were removed | Pass |

The first confirmed CLI capture completed in 1.37 seconds. The Raycast wrapper itself returned immediately and continued the bounded capture independently. Automated verification uses only synthetic `example.invalid` fixtures and does not require Mail, Raycast, `td`, or Todoist.

## Residual risk

macOS Automation permissions, Notification Center policy, Apple Mail URL handling, Raycast process behavior, and Todoist CLI output may change after release. Ambiguous CLI delivery remains fail-closed: local state becomes `uncertain` and automatic replay is blocked until reconciled.

## Conversation-selection regression

On 6 September 2026, a real grouped Mail conversation that the scripting API expanded to three underlying messages reproduced the former `multiple_selection` failure. After the fix, the same Raycast command selected the newest same-subject message, removed its reply prefix for the task title, created one confirmed Todoist task, and returned the existing task on replay. Remote fields matched the deterministic draft, no due date was added, and a before/after Mail-state digest remained equal. No correspondence or identifiers were retained.

Mail exposes no conversation identifier through its scripting dictionary, so grouping uses a conservative normalized-subject check. A manual multiselect of distinct messages with the same normalized subject can therefore be interpreted as one conversation; different subjects continue to fail closed.
