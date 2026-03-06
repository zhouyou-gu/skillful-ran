#!/usr/bin/env python3
"""Validate marketplace config and skills against strict JSON Schemas."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS_DIR = ROOT / "schemas"
SKILLS_DIR = ROOT / "skills"
CONFIG_PATH = ROOT / "config" / "marketplace.json"
SKILL_FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*(?:\n|$)", re.DOTALL)
REQUIRED_SKILL_HEADINGS = [
    "## Trigger",
    "## Inputs",
    "## Workflow",
    "## Outputs",
    "## Failure / Escalation",
]
STANDARD_OUTPUT_FIELDS = ["passed", "summary", "warnings", "artifacts", "next_steps"]
ALLOWED_PREFIXES = ("ocudu-", "srsran-", "skillful-ran-")
MIN_EVAL_CASES = 8
MAX_EVAL_CASES = 12
MAX_SKILL_LINES = 140
MAX_README_NONEMPTY_LINES = 16
MAX_REFERENCE_LINES = 170


def count_nonempty_lines(text: str) -> int:
    return sum(1 for line in text.splitlines() if line.strip())


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def make_validator(schema_name: str) -> Draft202012Validator:
    schema = load_json(SCHEMAS_DIR / schema_name)
    return Draft202012Validator(schema, format_checker=FormatChecker())


def validate_codex_skill_file(path: Path, skill_id: str | None, errors: list[str]) -> None:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as exc:  # pragma: no cover - defensive parsing path
        errors.append(f"{path.relative_to(ROOT)}: unable to read file ({exc})")
        return

    match = SKILL_FRONTMATTER_RE.match(text)
    if match is None:
        errors.append(
            f"{path.relative_to(ROOT)}:<frontmatter>: missing YAML frontmatter delimited by '---'"
        )
        return

    try:
        frontmatter = yaml.safe_load(match.group(1))
    except Exception as exc:
        errors.append(f"{path.relative_to(ROOT)}:<frontmatter>: invalid YAML ({exc})")
        return

    if not isinstance(frontmatter, dict):
        errors.append(f"{path.relative_to(ROOT)}:<frontmatter>: expected mapping object")
        return

    allowed_keys = {"name", "description"}
    extra_keys = sorted(set(frontmatter.keys()) - allowed_keys)
    if extra_keys:
        errors.append(
            f"{path.relative_to(ROOT)}:<frontmatter>: unsupported field(s): {', '.join(extra_keys)}"
        )

    name = frontmatter.get("name")
    if not isinstance(name, str) or not name.strip():
        errors.append(f"{path.relative_to(ROOT)}:<frontmatter>.name: required non-empty string")
    elif skill_id is not None and name != skill_id:
        errors.append(
            f"{path.relative_to(ROOT)}:<frontmatter>.name: '{name}' must match skill id '{skill_id}'"
        )

    description = frontmatter.get("description")
    if not isinstance(description, str) or not description.strip():
        errors.append(
            f"{path.relative_to(ROOT)}:<frontmatter>.description: required non-empty string"
        )

    if len(text.splitlines()) > MAX_SKILL_LINES:
        errors.append(
            f"{path.relative_to(ROOT)}:<body>: exceeds compactness budget of {MAX_SKILL_LINES} lines"
        )

    body = text[match.end() :]
    missing_headings = [heading for heading in REQUIRED_SKILL_HEADINGS if heading not in body]
    if missing_headings:
        errors.append(
            f"{path.relative_to(ROOT)}:<body>: missing required section(s): {', '.join(missing_headings)}"
        )

    if "do not use" not in text.lower():
        errors.append(
            f"{path.relative_to(ROOT)}:<body>: must include explicit negative routing with 'Do not use'"
        )


def validate_readme_file(path: Path, errors: list[str]) -> None:
    if not path.exists():
        errors.append(f"{path.relative_to(ROOT)}: missing required file")
        return

    try:
        text = path.read_text(encoding="utf-8")
    except Exception as exc:
        errors.append(f"{path.relative_to(ROOT)}: unable to read file ({exc})")
        return

    if count_nonempty_lines(text) > MAX_README_NONEMPTY_LINES:
        errors.append(
            f"{path.relative_to(ROOT)}:<body>: exceeds compactness budget of {MAX_README_NONEMPTY_LINES} non-empty lines"
        )


def validate_reference_files(skill_dir: Path, errors: list[str]) -> None:
    references_dir = skill_dir / "references"
    if not references_dir.exists():
        return

    for ref_path in sorted(path for path in references_dir.rglob("*") if path.is_file()):
        try:
            text = ref_path.read_text(encoding="utf-8")
        except Exception as exc:
            errors.append(f"{ref_path.relative_to(ROOT)}: unable to read file ({exc})")
            continue

        if len(text.splitlines()) > MAX_REFERENCE_LINES:
            errors.append(
                f"{ref_path.relative_to(ROOT)}:<body>: exceeds compactness budget of {MAX_REFERENCE_LINES} lines"
            )


def validate_eval_cases(skill_dir: Path, errors: list[str]) -> None:
    eval_path = skill_dir / "evals" / "cases.jsonl"
    if not eval_path.exists():
        errors.append(f"{eval_path.relative_to(ROOT)}: missing required file")
        return

    try:
        lines = [line for line in eval_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    except Exception as exc:
        errors.append(f"{eval_path.relative_to(ROOT)}: unable to read file ({exc})")
        return

    if not (MIN_EVAL_CASES <= len(lines) <= MAX_EVAL_CASES):
        errors.append(
            f"{eval_path.relative_to(ROOT)}:<body>: expected {MIN_EVAL_CASES}-{MAX_EVAL_CASES} non-empty JSONL cases"
        )

    positive = 0
    negative = 0
    for index, line in enumerate(lines, start=1):
        label = f"{eval_path.relative_to(ROOT)}:{index}"
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"{label}: invalid JSON ({exc})")
            continue

        if not isinstance(payload, dict):
            errors.append(f"{label}: expected JSON object")
            continue

        name = payload.get("name")
        prompt = payload.get("prompt")
        should_trigger = payload.get("should_trigger")
        must_include = payload.get("must_include")

        if not isinstance(name, str) or not name.strip():
            errors.append(f"{label}.name: required non-empty string")
        if not isinstance(prompt, str) or not prompt.strip():
            errors.append(f"{label}.prompt: required non-empty string")
        if not isinstance(should_trigger, bool):
            errors.append(f"{label}.should_trigger: required boolean")
        elif should_trigger:
            positive += 1
        else:
            negative += 1

        if must_include is not None:
            if not isinstance(must_include, list) or not all(
                isinstance(item, str) and item.strip() for item in must_include
            ):
                errors.append(f"{label}.must_include: expected array of non-empty strings")

    if lines and positive == 0:
        errors.append(f"{eval_path.relative_to(ROOT)}:<body>: must include at least one positive case")
    if lines and negative == 0:
        errors.append(f"{eval_path.relative_to(ROOT)}:<body>: must include at least one negative case")


def validate_tool_conventions(
    tool_data: dict[str, Any], tool_rel: Path, skill_id: str | None, errors: list[str]
) -> None:
    output_schema = tool_data.get("outputSchema")
    if not isinstance(output_schema, dict):
        errors.append(f"{tool_rel}:outputSchema: required object for Skillful RAN skills")
        return

    properties = output_schema.get("properties")
    required = output_schema.get("required")
    if not isinstance(properties, dict):
        errors.append(f"{tool_rel}:outputSchema.properties: required object")
        return

    if not isinstance(required, list):
        errors.append(f"{tool_rel}:outputSchema.required: required array")
        return

    for field in STANDARD_OUTPUT_FIELDS:
        if field not in properties:
            errors.append(f"{tool_rel}:outputSchema.properties: missing standard field '{field}'")
        if field not in required:
            errors.append(f"{tool_rel}:outputSchema.required: missing '{field}'")

    input_schema = tool_data.get("inputSchema")
    if not isinstance(input_schema, dict):
        return

    input_props = input_schema.get("properties")
    if not isinstance(input_props, dict):
        return

    if "workspace" not in input_props:
        errors.append(f"{tool_rel}:inputSchema.properties: missing standard field 'workspace'")

    if skill_id == "skillful-ran-packaging":
        mode = input_props.get("mode", {})
        candidate_paths = input_props.get("candidate_paths")
        target_skill_id = input_props.get("target_skill_id")
        dry_run = input_props.get("dry_run")
        qa_report_path = input_props.get("qa_report_path")

        if not isinstance(mode, dict) or mode.get("enum") != ["review", "promote", "update"]:
            errors.append(f"{tool_rel}:inputSchema.properties.mode: expected enum review|promote|update")
        if not isinstance(candidate_paths, dict) or candidate_paths.get("type") != "array":
            errors.append(f"{tool_rel}:inputSchema.properties.candidate_paths: expected array")
        if not isinstance(target_skill_id, dict) or target_skill_id.get("type") != "string":
            errors.append(f"{tool_rel}:inputSchema.properties.target_skill_id: expected string")
        if not isinstance(dry_run, dict) or dry_run.get("type") != "boolean":
            errors.append(f"{tool_rel}:inputSchema.properties.dry_run: expected boolean")
        if not isinstance(qa_report_path, dict) or qa_report_path.get("type") != "string":
            errors.append(f"{tool_rel}:inputSchema.properties.qa_report_path: expected string")

        for field in ["decisions", "draft_path", "generated_files"]:
            if field not in properties:
                errors.append(f"{tool_rel}:outputSchema.properties: missing packaging field '{field}'")

    if skill_id == "skillful-ran-skill-test":
        if "qa_report_path" not in properties:
            errors.append(f"{tool_rel}:outputSchema.properties: missing skill-test field 'qa_report_path'")
        if "checks" not in properties:
            errors.append(f"{tool_rel}:outputSchema.properties: missing skill-test field 'checks'")


def collect_schema_errors(
    validator: Draft202012Validator,
    instance: Any,
    label: str,
    errors: list[str],
) -> None:
    for err in sorted(validator.iter_errors(instance), key=lambda item: list(item.absolute_path)):
        location = ".".join(str(part) for part in err.absolute_path) or "<root>"
        errors.append(f"{label}:{location}: {err.message}")


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    config_validator = make_validator("config.schema.json")
    skill_validator = make_validator("skill.schema.json")
    tool_validator = make_validator("tool.schema.json")

    if not CONFIG_PATH.exists():
        errors.append(f"missing file: {CONFIG_PATH}")
        config: dict[str, Any] = {}
    else:
        try:
            config = load_json(CONFIG_PATH)
        except Exception as exc:  # pragma: no cover - defensive parsing path
            errors.append(f"{CONFIG_PATH}: unable to parse JSON ({exc})")
            config = {}

    if config:
        collect_schema_errors(config_validator, config, str(CONFIG_PATH.relative_to(ROOT)), errors)

    allowed_categories = set(config.get("categories", []))

    if not SKILLS_DIR.exists():
        errors.append(f"missing directory: {SKILLS_DIR}")
        skill_dirs: list[Path] = []
    else:
        skill_dirs = sorted(path for path in SKILLS_DIR.iterdir() if path.is_dir())

    if not skill_dirs:
        warnings.append("No skills found under skills/. Add at least one skill folder.")

    seen_skill_ids: dict[str, Path] = {}
    tool_name_to_ids: dict[str, list[str]] = {}

    for skill_dir in skill_dirs:
        skill_yaml_path = skill_dir / "skill.yaml"
        readme_path = skill_dir / "README.md"
        skill_md_path = skill_dir / "SKILL.md"

        validate_readme_file(readme_path, errors)

        if not skill_md_path.exists():
            errors.append(f"{skill_md_path.relative_to(ROOT)}: missing required file")

        if not skill_yaml_path.exists():
            errors.append(f"{skill_yaml_path.relative_to(ROOT)}: missing required file")
            continue

        try:
            skill_data = load_yaml(skill_yaml_path)
        except Exception as exc:
            errors.append(f"{skill_yaml_path.relative_to(ROOT)}: unable to parse YAML ({exc})")
            continue

        if not isinstance(skill_data, dict):
            errors.append(f"{skill_yaml_path.relative_to(ROOT)}:<root>: expected mapping object")
            continue

        collect_schema_errors(skill_validator, skill_data, str(skill_yaml_path.relative_to(ROOT)), errors)

        skill_id = skill_data.get("id")
        if isinstance(skill_id, str):
            if not skill_id.startswith(ALLOWED_PREFIXES):
                errors.append(
                    f"{skill_yaml_path.relative_to(ROOT)}:id: '{skill_id}' must start with one of {ALLOWED_PREFIXES}"
                )
            if skill_id != skill_dir.name:
                errors.append(
                    f"{skill_yaml_path.relative_to(ROOT)}:id: '{skill_id}' must match folder '{skill_dir.name}'"
                )

            if skill_id in seen_skill_ids:
                original = seen_skill_ids[skill_id].relative_to(ROOT)
                errors.append(
                    f"{skill_yaml_path.relative_to(ROOT)}:id: duplicate skill id '{skill_id}' "
                    f"(already defined in {original})"
                )
            else:
                seen_skill_ids[skill_id] = skill_yaml_path

        if skill_md_path.exists():
            validate_codex_skill_file(
                skill_md_path,
                skill_id if isinstance(skill_id, str) else None,
                errors,
            )

        validate_reference_files(skill_dir, errors)
        validate_eval_cases(skill_dir, errors)

        category = skill_data.get("category")
        if isinstance(category, str) and allowed_categories and category not in allowed_categories:
            errors.append(
                f"{skill_yaml_path.relative_to(ROOT)}:category: '{category}' not in config categories "
                f"{sorted(allowed_categories)}"
            )

        agent = skill_data.get("agent", {})
        tool_schema_rel = None
        if isinstance(agent, dict):
            tool_schema_rel = agent.get("tool_schema")

        if not isinstance(tool_schema_rel, str):
            continue

        tool_path = (skill_dir / tool_schema_rel).resolve()
        try:
            tool_rel = tool_path.relative_to(ROOT)
        except ValueError:
            errors.append(
                f"{skill_yaml_path.relative_to(ROOT)}:agent.tool_schema: '{tool_schema_rel}' resolves outside repository"
            )
            continue

        if not tool_path.exists():
            errors.append(
                f"{skill_yaml_path.relative_to(ROOT)}:agent.tool_schema: referenced file missing ({tool_rel})"
            )
            continue

        try:
            tool_data = load_json(tool_path)
        except Exception as exc:
            errors.append(f"{tool_rel}: unable to parse JSON ({exc})")
            continue

        collect_schema_errors(tool_validator, tool_data, str(tool_rel), errors)
        validate_tool_conventions(
            tool_data,
            tool_rel,
            skill_id if isinstance(skill_id, str) else None,
            errors,
        )

        tool_name = tool_data.get("name")
        if isinstance(tool_name, str) and isinstance(skill_id, str):
            tool_name_to_ids.setdefault(tool_name, []).append(skill_id)

    for tool_name, skill_ids in sorted(tool_name_to_ids.items()):
        if len(skill_ids) > 1:
            warnings.append(
                f"tool name collision '{tool_name}' appears in skills: {', '.join(sorted(skill_ids))}"
            )

    for warning in warnings:
        print(f"WARNING: {warning}")

    if errors:
        print(f"Validation failed with {len(errors)} error(s):")
        for err in errors:
            print(f"  - {err}")
        return 1

    print(f"Validation passed: {len(skill_dirs)} skill(s) checked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
