from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]


def load_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_design_vision_validates_against_committed_schema() -> None:
    schema = load_json("schemas/repo-vision-contract.schema.json")
    vision = load_json("docs/vision.json")
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(vision)


def test_design_contract_has_stable_required_principles() -> None:
    vision = load_json("docs/vision.json")
    principle_ids = [item["id"] for item in vision["principles"]]
    assert len(principle_ids) == len(set(principle_ids))
    assert {
        "one-keystroke",
        "mail-read-only",
        "keychain-only",
        "idempotent-effect",
        "json-first",
        "public-safe",
        "fail-closed",
    } <= set(principle_ids)


def test_go_and_design_visions_share_the_product_north_star() -> None:
    go_vision = load_json(".go/vision.json")
    design_vision = load_json("docs/vision.json")
    combined = " ".join(
        [
            go_vision["north_star"],
            go_vision["core_promise"],
            design_vision["vision"]["north_star"],
            design_vision["vision"]["promise"],
        ]
    ).lower()
    for phrase in ("selected", "mail", "todoist", "one"):
        assert phrase in combined


def test_public_safety_contract_names_private_artifacts() -> None:
    safety = load_json("docs/vision.json")["public_safety"]
    contract = " ".join(safety["forbidden"] + safety["required_boundaries"]).lower()
    for phrase in ("token", "keychain", "message", "runtime", "synthetic"):
        assert phrase in contract


def test_architecture_records_external_effect_guards() -> None:
    architecture = (ROOT / "docs/architecture.md").read_text(encoding="utf-8").lower()
    for phrase in ("message://", "official todoist cli", "macos keychain", "read-only"):
        assert phrase in architecture


def test_product_plan_references_every_open_go_task() -> None:
    plan = (ROOT / "docs/product-plan.md").read_text(encoding="utf-8")
    task_paths = sorted((ROOT / ".go/tasks").rglob("*.json"))
    assert task_paths
    for task_path in task_paths:
        task = json.loads(task_path.read_text(encoding="utf-8"))
        if task["status"] == "open":
            assert f"`{task['id']}`" in plan


def test_readme_renders_the_public_hero_near_the_top() -> None:
    lines = (ROOT / "README.md").read_text(encoding="utf-8").splitlines()
    assert "assets/hero.png" in "\n".join(lines[:10])
    assert (ROOT / "assets/hero.png").stat().st_size > 100_000
