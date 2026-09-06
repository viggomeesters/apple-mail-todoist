# Dependency-Ordered Product Plan

The foundation release is complete. Product behavior is intentionally represented as small open tasks in `.go/tasks/`; each task is claimable after the listed prerequisites have shipped. Task IDs, scope, acceptance, and verification in `.go` are canonical.

## Delivery sequence

| Order | Task | Outcome | Prerequisites |
|---:|---|---|---|
| 1 | `T001-contracts` | Typed domain contracts and synthetic fixtures define the safe core | None |
| 2 | `T002-mail-link` | A pure, tested RFC Message-ID to `message://` builder | `T001-contracts` |
| 3 | `T003-mail-selection` | Read exactly one selected Apple Mail message through a read-only JXA adapter | `T001-contracts`, `T002-mail-link` |
| 4 | `T004-keychain` | Configure and retrieve a Todoist token through macOS Keychain without disclosure | `T001-contracts` |
| 5 | `T005-todoist-api` | Create a typed Todoist task with stable request identity | `T001-contracts`, `T004-keychain` |
| 6 | `T006-reconciliation` | Persist minimal idempotency state and reconcile uncertain delivery | `T001-contracts`, `T005-todoist-api` |
| 7 | `T007-capture-service` | Compose defaults and orchestrate one safe end-to-end capture through fake ports | `T003-mail-selection`, `T005-todoist-api`, `T006-reconciliation` |
| 8 | `T008-raycast-ux` | Ship the Raycast command and non-blocking success/error HUD | `T007-capture-service` |
| 9 | `T009-live-proof` | Verify the complete local workflow with disposable Todoist data and redacted evidence | `T008-raycast-ux` |

## Scope boundaries

The sequence delivers one selected message, direct Todoist Inbox creation, fixed `mail` label, deterministic title/description, a deep link, duplicate protection, and a Raycast HUD.

It excludes mail archiving, vault ingestion, body or attachment processing, AI enrichment, inferred scheduling, cross-platform clients, background monitoring, and multi-message batches.

## Shared verification

Every task runs its focused tests and the full local gate:

```bash
make check
```

Live Mail, Keychain, link, or Todoist access is allowed only in `T009-live-proof` or a separately accepted task that names those side effects. Evidence committed to Git must remain synthetic or structurally redacted.
