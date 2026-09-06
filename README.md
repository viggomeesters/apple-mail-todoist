# Apple Mail to Todoist

![Apple Mail to Todoist hero](assets/hero.png)

[![License: MIT](https://img.shields.io/badge/License-MIT-22c55e.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-38bdf8.svg)](pyproject.toml)
[![Go workflow](https://img.shields.io/badge/workflow-repo--local_.go-f97316.svg)](.go/project.json)

Create one traceable Todoist task from the message selected in Apple Mail, confirm it with a lightweight Raycast HUD, and keep working without leaving Mail. The project is a narrow, local-first macOS integration with explicit privacy and retry guarantees.

## Project status

Version `0.1.0` is the public repository-foundation release. It establishes the product contract, architecture, safety boundaries, local validation, and dependency-ordered Go backlog. The executable mail-to-task command is not part of this release; implementation begins with the first open task in `.go/tasks/`.

## Product contract

The accepted interaction is deliberately small:

1. Select one message in Apple Mail on macOS.
2. Invoke **Create Todoist Task from Mail** in Raycast.
3. Create exactly one task directly through the Todoist API.
4. Show `Todoist task created` in a non-blocking Raycast HUD.
5. Leave the selected email unchanged.

The task defaults to Todoist Inbox, carries the `mail` label, has no inferred due date, and includes sender, received time, and a `message://` link back to the selected message. An optional command may expose project, date, priority, and title controls without slowing the default path.

## Purpose

Apple Mail and Todoist are excellent at different jobs, but turning correspondence into a commitment still creates friction. This project removes that friction while preserving three trust properties:

- **Mail stays read-only.** Task creation never archives, moves, flags, or deletes a message.
- **Private data stays local.** The Todoist token belongs in macOS Keychain; live mail and runtime state never belong in Git.
- **Retries stay safe.** Stable request identity and local reconciliation prevent uncertain network responses from producing duplicate tasks.

## Architecture at a glance

```text
Raycast command
    │
    ▼
local Python CLI ──read-only──▶ Apple Mail selection (JXA)
    │                              │
    │                              └── RFC Message-ID → message:// link
    ▼
task composer ◀────────────── macOS Keychain token
    │
    ├── idempotent request ──────▶ Todoist API
    ├── minimal reconciliation ──▶ local app state
    └── outcome ─────────────────▶ Raycast HUD
```

See [Architecture](docs/architecture.md) for trust boundaries, data flow, failure states, and extension points.

## Installation

The `0.1.0` release installs the development package and validation tooling. It does not install a live Raycast command.

```bash
git clone https://github.com/viggomeesters/apple-mail-todoist.git
cd apple-mail-todoist
uv sync --frozen --group dev
```

## Usage

Use the foundation release to inspect the accepted product contract and continue the ordered work:

```bash
make check
./go status . --json
./go next .
```

The first claimable Go task defines the typed core using synthetic data. Live Apple Mail and Todoist access stay outside normal validation.

## Development

Requirements:

- macOS for live Apple Mail and Keychain integration work
- Python 3.11 or newer
- [`uv`](https://docs.astral.sh/uv/)
- Git

Validate a prepared clone:

```bash
make check
```

`make check` is the repository's authoritative local gate. It validates the Python package, tests, formatting/lint rules, machine-readable vision contract, `.go` workflow, documentation links, and public-data boundaries. This repository intentionally uses local gates instead of GitHub Actions.

## Repository map

| Path | Purpose |
|---|---|
| [`.go/`](.go/) | Canonical product vision, principles, hierarchy, tasks, and evidence |
| [`docs/vision.json`](docs/vision.json) | Machine-readable repository design and acceptance contract |
| [`docs/architecture.md`](docs/architecture.md) | Components, data flow, side effects, and failure model |
| [`docs/onboarding.md`](docs/onboarding.md) | Dependency-ordered orientation for developers and agents |
| [`docs/product-plan.md`](docs/product-plan.md) | Ordered implementation plan mirrored by open Go tasks |
| [`scripts/validate_repository.py`](scripts/validate_repository.py) | One-command local repository gate |
| [`schemas/`](schemas/) | Committed schemas for machine-readable contracts |
| [`src/apple_mail_todoist/`](src/apple_mail_todoist/) | Python package boundary; runtime modules arrive through Go tasks |

## Continue the work

The repo-local workflow is pinned to an immutable Go Workflow Stack release. Inspect the project and the first claimable task with:

```bash
./go status . --json
./go next .
```

Agents must read [`AGENTS.md`](AGENTS.md), [the design contract](docs/vision.json), and [the product plan](docs/product-plan.md) before claiming work. The normal continuation command is simply `Go`.

## Privacy and security

Never commit Todoist credentials, exported mail, message bodies, real addresses, live Message-IDs, reconciliation databases, logs, or Keychain exports. Tests use synthetic `example.invalid` identities. Report vulnerabilities through the private process in [`SECURITY.md`](SECURITY.md).

## Releases

Release history is recorded in [`CHANGELOG.md`](CHANGELOG.md). Version `0.1.0` publishes the professional foundation and validated implementation contract; later releases must not claim working product behavior without its corresponding verification evidence.

## License

Copyright © 2026 Viggo Meesters. Released under the [MIT License](LICENSE).
