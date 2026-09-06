## Outcome

Describe the bounded user-visible or repository outcome.

## Trust boundaries

- [ ] Apple Mail remains read-only.
- [ ] No live mail, credentials, logs, or runtime state are included.
- [ ] External writes are idempotent and failure-aware.
- [ ] Documentation claims match implemented behavior.

## Verification

- [ ] `make check`
- [ ] Focused tests for the changed behavior
- [ ] Live checks, if any, used synthetic or disposable data and left no tracked output

## Residual risk

State what remains uncertain after verification.
