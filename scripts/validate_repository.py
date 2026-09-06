#!/usr/bin/env python3
"""Run the authoritative local repository-foundation gate."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = (
    "README.md",
    "LICENSE",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "CHANGELOG.md",
    "AGENTS.md",
    "docs/vision.json",
    "docs/architecture.md",
    "docs/onboarding.md",
    "docs/product-plan.md",
    "schemas/repo-vision-contract.schema.json",
    "assets/hero.png",
    "assets/social-preview.png",
    ".go/project.json",
    ".go/vision.json",
    ".go/architecture-principles.json",
)
FORBIDDEN_FILENAMES = re.compile(
    r"(^|/)(\.env($|\.)|id_(rsa|ed25519)|.*\.(eml|mbox|p12|pem|key|sqlite3?|db|log)$)",
    re.IGNORECASE,
)
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"(?i)(?:todoist[_ -]?(?:api[_ -]?)?token)\s*[:=]\s*['\"]?[A-Za-z0-9_-]{20,}"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
)
TEXT_SUFFIXES = {
    ".md",
    ".py",
    ".toml",
    ".json",
    ".jsonl",
    ".sh",
    ".yml",
    ".yaml",
    ".txt",
}


def run(label: str, command: list[str]) -> None:
    print(f"==> {label}")
    completed = subprocess.run(command, cwd=ROOT, check=False)
    if completed.returncode:
        raise SystemExit(completed.returncode)


def public_data_check() -> None:
    missing = [path for path in REQUIRED_FILES if not (ROOT / path).is_file()]
    if missing:
        raise SystemExit(f"Missing required files: {', '.join(missing)}")

    failures: list[str] = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or ".git" in path.parts or ".venv" in path.parts:
            continue
        relative = path.relative_to(ROOT).as_posix()
        if FORBIDDEN_FILENAMES.search(relative):
            failures.append(f"private/generated filename: {relative}")
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in {"Makefile", "go"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                failures.append(f"secret-like content: {relative}")
                break
    if failures:
        raise SystemExit("Public-data boundary failed:\n- " + "\n- ".join(failures))
    print("Public-data boundary: OK")


def main() -> int:
    public_data_check()
    run("Ruff", [sys.executable, "-m", "ruff", "check", "."])
    run("Pytest", [sys.executable, "-m", "pytest", "-q"])
    run("Go workflow", [str(ROOT / "go"), "validate", "."])
    print("Repository validation: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
