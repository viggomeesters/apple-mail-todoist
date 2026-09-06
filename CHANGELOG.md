# Changelog

All notable changes to this project are documented in this file. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Fixed

- Accept one grouped Apple Mail conversation by selecting its newest message, while still rejecting unrelated multiselects.

## [0.2.0] - 2026-09-06

### Added

- One-action Apple Mail selection capture with deterministic Todoist task fields and exact `message://` deep links.
- Official Todoist CLI browser OAuth integration with credentials owned by the macOS secure store.
- Local reconciliation that prevents duplicate creation and blocks ambiguous replay.
- Immediate Raycast HUD feedback followed by a bounded macOS result notification.

### Changed

- Replaced manual API-token handling and direct HTTP delivery with the official `td` CLI.

### Security

- The application no longer retrieves or accepts Todoist credentials; live evidence is structurally redacted and disposable artifacts are removed.

## [0.1.0] - 2026-09-06

### Added

- Public repository identity, MIT license, security policy, contribution guide, and onboarding documentation.
- Repo-local `.go` product vision, architecture principles, hierarchy, and dependency-ordered implementation tasks.
- Machine-readable repository design contract with committed JSON Schema and semantic tests.
- Local validation gate covering tests, lint, workflow state, documentation, and public-data safety.
- Original hero and social-preview artwork with verified safe margins and readable contrast.

### Security

- Established read-only Apple Mail, macOS Keychain, synthetic-fixture, idempotency, and private-runtime-state boundaries before product implementation.

[0.2.0]: https://github.com/viggomeesters/apple-mail-todoist/releases/tag/v0.2.0
[0.1.0]: https://github.com/viggomeesters/apple-mail-todoist/releases/tag/v0.1.0
