# Public Launch Readiness

![Apple Mail to Todoist social preview](../assets/social-preview.png)

## Current release

| Item | Status | Evidence |
|---|---|---|
| Repository | Public | `https://github.com/viggomeesters/apple-mail-todoist` |
| Foundation release | `v0.1.0` | GitHub release and `CHANGELOG.md` |
| Product runtime | Not shipped in `v0.1.0` | Open tasks in `.go/tasks/` |
| Local quality gate | Required | `make check` |
| GitHub Actions | Intentionally unused | Local-gate policy in `AGENTS.md` |
| Privacy posture | Public-safe source, synthetic tests | `SECURITY.md` and validation report |
| Visual identity | Hero and social preview | `assets/hero.png`, `assets/social-preview.png` |

## Metadata

- Description: Create actionable Todoist tasks from selected Apple Mail messages on macOS.
- Topics: `macos`, `apple-mail`, `todoist`, `raycast`, `automation`, `python`
- Homepage: repository URL; the project is a local CLI integration rather than a hosted web product.
- License: MIT

## Visual verification

The hero and 1280×640 social-preview crop were rendered and inspected at release time. The exact headline is readable at repository width; the email card, command symbol, flow, and task card remain inside safe margins; foreground and background contrast is strong; no elements overlap the headline; and the images contain no clipping, personal data, watermark, or draft copy.

## Publication proof

The release gate requires schema-valid design and Go contracts, passing tests and lint, current-file and history privacy scans, no large unreviewed binaries, readback of public visibility/default branch/description/topics, a clean working tree, and a pushed release tag.
