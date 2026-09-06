# Security Policy

## Supported versions

Security fixes target the latest published release. Version `0.1.0` contains repository contracts and development tooling only; it does not ship a live Apple Mail or Todoist integration.

## Reporting a vulnerability

Please use GitHub's **Report a vulnerability** flow under the repository Security tab. Do not open a public issue for credential exposure, unintended mail mutation, private-data leakage, request replay, or duplicate-task creation.

Include the affected version, impact, reproduction conditions using synthetic data, and any mitigation you have already applied. Do not attach real email, access tokens, Keychain exports, live Message-IDs, or reconciliation databases.

## Security boundaries

- Todoist credentials must be stored in macOS Keychain and retrieved only at the request boundary.
- Apple Mail is a read-only source. The product must not request or perform archive, move, flag, delete, or send operations.
- Mail fields are untrusted text and cannot control commands, file paths, API endpoints, labels, or projects.
- Todoist creation uses stable request identity and reconciliation before replay.
- Logs contain outcome codes and synthetic identifiers, never message bodies, tokens, email addresses, or raw API payloads.
- Tests and documentation use reserved `example.invalid` identities.

## Disclosure

After a report is acknowledged, remediation and disclosure timing will be coordinated privately. A public advisory and patched release will follow when the issue affects published code.
