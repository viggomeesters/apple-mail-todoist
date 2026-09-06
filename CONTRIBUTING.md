# Contributing

Thank you for helping make Apple Mail to Todoist safer and more useful.

## Before you start

Read [`AGENTS.md`](AGENTS.md), [`docs/vision.json`](docs/vision.json), and [`docs/architecture.md`](docs/architecture.md). Product work is managed through the repo-local `.go` contract; inspect the next eligible task with `./go next .`.

## Development setup

```bash
git clone https://github.com/viggomeesters/apple-mail-todoist.git
cd apple-mail-todoist
uv sync --frozen --group dev
make check
```

## Contribution rules

- Keep changes bounded to one product outcome.
- Use synthetic messages and `example.invalid` addresses in tests.
- Never include credentials, live correspondence, personal identifiers, exported mail, Keychain material, logs, or runtime databases.
- Preserve the read-only Apple Mail boundary.
- Add tests for success, failure, timeout, and replay behavior when external effects change.
- Update machine-readable contracts and human documentation together when architecture or product behavior changes.
- Run `make check` before submitting a pull request.

## Commit and pull request quality

Use a concise imperative commit subject. In the pull request, explain the user-visible outcome, affected trust boundaries, verification commands, and residual risk. Reviewers should be able to reproduce the proof without private data or a live account.

## Live integration checks

Normal tests must not access Apple Mail, Keychain, or Todoist. A live check requires an explicitly scoped task, a test account or disposable task target, and a documented cleanup/reconciliation step. Never put live output in Git.
