# Developer and Agent Onboarding

This guide provides the shortest evidence-backed route from a fresh clone to useful work.

## 1. Understand the product

Read in this order:

1. [`README.md`](../README.md) for the user promise and current release status.
2. [`.go/vision.json`](../.go/vision.json) for the canonical product north star and non-goals.
3. [`docs/vision.json`](vision.json) for design, engineering, and public-safety acceptance rules.
4. [`docs/architecture.md`](architecture.md) for components, data flow, and side effects.
5. [`docs/product-plan.md`](product-plan.md) for ordered implementation work.

## 2. Prepare the clone

```bash
uv sync --frozen --group dev
make check
```

The `./go` launcher reads the immutable stack reference from `.go/project.json` and bootstraps that exact release into a local cache. Override it only with a checkout whose HEAD exactly matches the pinned tag.

## 3. Inspect workflow state

```bash
./go doctor . --platform auto --agent codex --json
./go status . --json
./go next .
```

`.go` is the source of truth for product tasks. Do not reproduce its state in a vault, issue list, or narrative checklist.

## 4. Find the relevant boundary

| Role | Start with | Primary risk | Proof |
|---|---|---|---|
| Product builder | `docs/product-plan.md` and the next Go task | Expanding beyond the one-keystroke wedge | Task acceptance plus focused tests |
| Mail adapter builder | Apple Mail port in `docs/architecture.md` | Accidentally introducing Mail mutation | Static script contract and fake-adapter tests |
| Todoist adapter builder | API and reconciliation sections | Duplicate tasks after uncertain delivery | Replay, timeout, and reconciliation tests |
| Raycast UX builder | HUD outcomes and task flow | Interrupting the Mail workflow | Script tests plus explicit manual UX evidence |
| Reviewer | `docs/vision.json` scorecard | Passing narrow tests while violating trust boundaries | `make check` and scorecard review |

## 5. Work through Go

Claim only a task whose stated prerequisites are complete. Keep edits inside its scope and record concrete evidence for every acceptance item. Normal continuation is:

```text
Go
```

Before shipping, run `make check`, review staged files for private data, verify the branch and remote, and ensure documentation describes only observed behavior.

## Current extension points

- `src/apple_mail_todoist/` is the package boundary.
- Platform adapters belong behind narrow protocols rather than in the CLI entry point.
- `tests/` must remain runnable without Mail, Keychain, Raycast, or Todoist access.
- `scripts/validate_repository.py` is the local release gate and may be extended when new canonical contracts are added.
