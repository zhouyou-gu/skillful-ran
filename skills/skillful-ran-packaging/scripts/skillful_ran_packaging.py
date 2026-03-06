#!/usr/bin/env python3
"""Review and promote reusable artifacts into Skillful RAN skills."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from datetime import datetime, UTC
from pathlib import Path

import yaml

ALLOWED_PREFIXES = ("ocudu-", "srsran-", "skillful-ran-")
VALID_CATEGORIES = {"telco", "testing", "devtools", "automation"}
TEXT_SUFFIXES = {".md", ".txt", ".sh", ".py", ".json", ".yaml", ".yml"}
BINARY_SUFFIXES = {".png", ".jpg", ".jpeg", ".pcap", ".pcapng", ".bin", ".sqlite", ".zip"}
SECRET_PATTERNS = [r"BEGIN [A-Z ]+ PRIVATE KEY", r"\bghp_[A-Za-z0-9]+\b", r"AKIA[0-9A-Z]{16}"]
MAX_REFERENCE_LINES = 170


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def git_clean(root: Path) -> bool:
    proc = subprocess.run(
        ["git", "status", "--short"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    return proc.returncode == 0 and not proc.stdout.strip()


def normalize_lines(text: str) -> str:
    lines = [line.rstrip() for line in text.replace("\r\n", "\n").splitlines()]
    return "\n".join(lines).strip() + "\n"


def sanitize_name(name: str) -> str:
    lowered = re.sub(r"[^a-z0-9._-]+", "-", name.lower())
    lowered = re.sub(r"-{2,}", "-", lowered).strip("-")
    return lowered or "candidate"


def resolve_workspace(root: Path, workspace_arg: str) -> Path:
    workspace = Path(workspace_arg)
    return workspace if workspace.is_absolute() else (root / workspace).resolve()


def expand_candidates(workspace: Path, candidates: list[str]) -> list[Path]:
    resolved: list[Path] = []
    for candidate in candidates:
        path = Path(candidate)
        target = path if path.is_absolute() else (workspace / path).resolve()
        if target.is_dir():
            resolved.extend(sorted(item for item in target.rglob("*") if item.is_file()))
        else:
            resolved.append(target)
    return resolved


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def classify_candidate(path: Path, workspace: Path) -> dict[str, str]:
    rel = path
    try:
        rel = path.relative_to(workspace)
    except ValueError:
        pass

    result = {
        "path": str(rel),
        "decision": "drop",
        "reason": "candidate is missing",
        "target": "",
        "rewrite_notes": "",
    }

    if not path.exists() or not path.is_file():
        return result

    if path.suffix.lower() in BINARY_SUFFIXES:
        result["reason"] = "binary or capture artifacts are not promoted into tracked skills"
        return result

    raw = path.read_bytes()
    if b"\0" in raw:
        result["reason"] = "binary content is not promoted into tracked skills"
        return result

    text = raw.decode("utf-8", errors="replace")
    if any(re.search(pattern, text) for pattern in SECRET_PATTERNS):
        result["reason"] = "candidate appears to contain secrets or credentials"
        return result

    parts = set(path.parts)
    if {"logs", "captures", "tmp"} & parts:
        result["reason"] = "raw lab artifacts stay outside tracked skills"
        return result

    suffix = path.suffix.lower()
    name = sanitize_name(path.name)

    if suffix in {".sh", ".py"}:
        result["decision"] = "keep" if "promote" in parts else "rewrite"
        result["reason"] = "helper script can live under scripts/"
        result["target"] = f"scripts/{name}"
        result["rewrite_notes"] = "normalize name and whitespace only"
        return result

    if suffix in {".md", ".txt"}:
        line_count = len(text.splitlines())
        result["decision"] = "rewrite" if line_count > MAX_REFERENCE_LINES or {"src", "build"} & parts else "keep"
        result["reason"] = "text candidate can become a compact reference"
        result["target"] = f"references/{name if suffix == '.md' else name + '.md'}"
        result["rewrite_notes"] = "trim to a concise reference shape"
        return result

    if suffix in {".json", ".yaml", ".yml"}:
        result["decision"] = "rewrite"
        result["reason"] = "structured sample can become a tiny example"
        result["target"] = f"examples/{name}"
        result["rewrite_notes"] = "keep only sanitized compact sample content"
        return result

    if suffix in TEXT_SUFFIXES:
        result["decision"] = "rewrite"
        result["reason"] = "text candidate needs normalization before promotion"
        result["target"] = f"references/{name}.md"
        result["rewrite_notes"] = "convert to a concise markdown reference"
        return result

    result["reason"] = "candidate type has no compact tracked destination"
    return result


def rewrite_candidate(path: Path, decision: dict[str, str]) -> str:
    text = read_text(path)
    if decision["target"].startswith("references/"):
        lines = text.splitlines()[:MAX_REFERENCE_LINES]
        return normalize_lines("\n".join(lines))
    return normalize_lines(text)


def generic_description(skill_id: str, title: str) -> str:
    return (
        f"{title}. Use when this specific Skillful RAN workflow is needed. "
        "Do not use it for unrelated OCUDU tasks."
    )


def scaffold_skill_files(skill_id: str, title: str, category: str, tags: list[str]) -> dict[str, str]:
    tool_name = skill_id.replace("-", "_")
    description = generic_description(skill_id, title)
    tags_yaml = "\n".join(f"  - {tag}" for tag in tags)
    evals = [
        {"name": "positive basic", "prompt": f"Use {title} for this task.", "should_trigger": True, "must_include": ["workspace", "summary"]},
        {"name": "positive explicit", "prompt": f"Run the {skill_id} workflow in the local OCUDU workspace.", "should_trigger": True},
        {"name": "positive concise", "prompt": f"I need the {title} skill, not a general lab answer.", "should_trigger": True},
        {"name": "positive dry run", "prompt": f"Plan the {title} workflow before making changes.", "should_trigger": True, "must_include": ["dry_run"]},
        {"name": "negative host audit", "prompt": "Check host readiness and missing packages for OCUDU.", "should_trigger": False},
        {"name": "negative build install", "prompt": "Clone and build srsRAN Project in .local/ocudu.", "should_trigger": False},
        {"name": "negative smoke", "prompt": "Run local smoke tests against the build tree.", "should_trigger": False},
        {"name": "negative packaging", "prompt": "Promote scratch files into a tracked skill.", "should_trigger": False},
    ]

    eval_lines = "\n".join(json.dumps(item) for item in evals) + "\n"
    skill_md = f"""---
name: {skill_id}
description: {description}
---

# {title}

## Trigger

- Use when the user explicitly needs the {title} workflow.
- Do not use it for broad OCUDU tasks that belong to a different Skillful RAN skill.

## Inputs

- `workspace`: root lab path, defaulting to `.local/ocudu/`
- `dry_run`: plan before changing files or the system
- Add task-specific inputs to `tool.json`

## Workflow

1. Read [`tool.json`](tool.json).
2. Refine the task-specific logic from the generated draft.
3. Keep detailed material in `references/` or `scripts/`, not in this skill body.
4. Update the eval pack before promoting the draft.

## Outputs

- Standard envelope: `passed`, `summary`, `warnings`, `artifacts`, `next_steps`
- Add task-specific fields only when they help downstream automation

## Failure / Escalation

- If the task is not clearly this workflow, route to a more specific Skillful RAN skill.
- If the generated draft is still too broad, split it before promotion.
"""
    return {
        "SKILL.md": skill_md,
        "README.md": f"# {title}\n\nGenerated by skillful-ran-packaging as a compact draft.\nRefine the workflow, tool contract, and evals before relying on it.\n",
        "skill.yaml": (
            f"id: {skill_id}\n"
            f"name: {title}\n"
            f"description: {title} for Skillful RAN\n"
            f"category: {category}\n"
            f"tags:\n{tags_yaml}\n"
            f"difficulty: intermediate\n"
            f"repo: https://github.com/zhouyou-gu/skillful-ran\n"
            f"install:\n"
            f"  pip: pyyaml\n"
            f"agent:\n"
            f"  protocol: mcp\n"
            f"  tool_schema: tool.json\n"
        ),
        "tool.json": json.dumps(
            {
                "name": tool_name,
                "title": title,
                "description": f"{title} for Skillful RAN.",
                "inputSchema": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "workspace": {"type": "string", "default": ".local/ocudu"},
                        "dry_run": {"type": "boolean", "default": True},
                        "task": {"type": "string"},
                    },
                    "required": ["workspace"],
                },
                "outputSchema": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "passed": {"type": "boolean"},
                        "summary": {"type": "string"},
                        "warnings": {"type": "array", "items": {"type": "string"}},
                        "artifacts": {"type": "array", "items": {"type": "string"}},
                        "next_steps": {"type": "array", "items": {"type": "string"}},
                        "details": {"type": "object"},
                    },
                    "required": ["passed", "summary", "warnings", "artifacts", "next_steps", "details"],
                },
            },
            indent=2,
        )
        + "\n",
        "evals/cases.jsonl": eval_lines,
    }


def write_tree(base: Path, files: dict[str, str]) -> list[str]:
    if base.exists():
        shutil.rmtree(base)
    base.mkdir(parents=True, exist_ok=True)

    written: list[str] = []
    for rel_path, content in files.items():
        target = base / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        written.append(rel_path)
    return sorted(written)


def validate_promotion_inputs(skill_id: str, title: str | None, category: str | None, tags: list[str]) -> list[str]:
    warnings: list[str] = []
    if not skill_id.startswith(ALLOWED_PREFIXES):
        raise ValueError(f"skill id must start with one of {ALLOWED_PREFIXES}")
    if title is None or not title.strip():
        raise ValueError("title is required for new skill promotion")
    if category not in VALID_CATEGORIES:
        raise ValueError(f"category must be one of {sorted(VALID_CATEGORIES)}")
    if not tags:
        raise ValueError("at least one tag is required")
    return warnings


def run_validator(root: Path) -> tuple[bool, str]:
    proc = subprocess.run(
        ["python3", "scripts/validate_skills.py"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    message = (proc.stdout + proc.stderr).strip()
    return proc.returncode == 0, message


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["review", "promote", "update"], required=True)
    parser.add_argument("--candidate-path", action="append", dest="candidate_paths", required=True)
    parser.add_argument("--target-skill-id", required=True)
    parser.add_argument("--workspace", default=".local/ocudu")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--title")
    parser.add_argument("--category")
    parser.add_argument("--tag", action="append", dest="tags", default=[])
    args = parser.parse_args()

    root = repo_root()
    workspace = resolve_workspace(root, args.workspace)
    draft_dir = workspace / "promote" / args.target_skill_id
    backup_dir: Path | None = None
    promoted_path: Path | None = None
    warnings: list[str] = []
    next_steps: list[str] = []

    if args.mode in {"promote", "update"} and not args.dry_run and not git_clean(root):
        payload = {
            "passed": False,
            "summary": "Promotion is blocked because the git worktree is not clean.",
            "warnings": warnings,
            "artifacts": [str(draft_dir)],
            "next_steps": ["Commit or stash current tracked changes before promoting or updating a skill."],
            "decisions": [],
            "draft_path": str(draft_dir),
            "generated_files": [],
            "promoted_path": None,
            "backup_path": None,
        }
        print(json.dumps(payload, indent=2))
        return 1

    skill_dir = root / "skills" / args.target_skill_id
    is_update = args.mode == "update"
    if args.mode == "promote" and skill_dir.exists():
        raise SystemExit("target skill already exists; use --mode update instead")
    if is_update and not skill_dir.exists():
        raise SystemExit("target skill does not exist; use --mode promote instead")

    title = args.title
    category = args.category
    tags = sorted(set(args.tags))

    if skill_dir.exists():
        current = load_yaml(skill_dir / "skill.yaml")
        title = title or current.get("name")
        category = category or current.get("category")
        tags = tags or list(current.get("tags", []))

    if args.mode == "promote":
        warnings.extend(validate_promotion_inputs(args.target_skill_id, title, category, tags))
    elif args.mode == "update" and (not title or not category or not tags):
        raise SystemExit("existing skill metadata could not be resolved for update")

    candidates = expand_candidates(workspace, args.candidate_paths)
    decisions = [classify_candidate(path, workspace) for path in candidates]

    scaffold = scaffold_skill_files(args.target_skill_id, title or args.target_skill_id, category or "devtools", tags or ["ocudu"])
    generated_support: dict[str, str] = {}
    for source_path, decision in zip(candidates, decisions):
        if decision["decision"] == "drop" or not decision["target"]:
            continue
        generated_support[decision["target"]] = rewrite_candidate(source_path, decision)

    all_files = {**scaffold, **generated_support}
    generated_files = write_tree(draft_dir, all_files)
    artifacts = [str(draft_dir)]

    if args.mode == "review" or args.dry_run:
        next_steps.append("Inspect the draft under .local/ocudu/promote/ before any tracked promotion.")
        payload = {
            "passed": True,
            "summary": "Draft review completed without touching tracked skill folders.",
            "warnings": warnings,
            "artifacts": artifacts,
            "next_steps": next_steps,
            "decisions": decisions,
            "draft_path": str(draft_dir),
            "generated_files": generated_files,
            "promoted_path": None,
            "backup_path": None,
        }
        print(json.dumps(payload, indent=2))
        return 0

    if is_update:
        backup_dir = workspace / "promote" / "backups" / f"{args.target_skill_id}-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"
        backup_dir.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(skill_dir, backup_dir)
        shutil.rmtree(skill_dir)
        shutil.copytree(draft_dir, skill_dir)
        promoted_path = skill_dir
    else:
        shutil.copytree(draft_dir, skill_dir)
        promoted_path = skill_dir

    ok, validator_output = run_validator(root)
    if not ok:
        warnings.append("repo validation failed after promotion; draft was kept for review")
        if is_update and backup_dir is not None:
            if skill_dir.exists():
                shutil.rmtree(skill_dir)
            shutil.copytree(backup_dir, skill_dir)
        elif promoted_path and promoted_path.exists():
            shutil.rmtree(promoted_path)
        payload = {
            "passed": False,
            "summary": "Promotion failed validation and was rolled back.",
            "warnings": warnings + [validator_output],
            "artifacts": artifacts,
            "next_steps": ["Fix the draft and rerun the packaging workflow."],
            "decisions": decisions,
            "draft_path": str(draft_dir),
            "generated_files": generated_files,
            "promoted_path": None,
            "backup_path": str(backup_dir) if backup_dir else None,
        }
        print(json.dumps(payload, indent=2))
        return 1

    next_steps.append("Run verify_install_targets and registry builds before committing the promoted skill.")
    payload = {
        "passed": True,
        "summary": "Skill draft passed packaging checks and was promoted into tracked paths.",
        "warnings": warnings,
        "artifacts": artifacts + [str(promoted_path)] if promoted_path else artifacts,
        "next_steps": next_steps,
        "decisions": decisions,
        "draft_path": str(draft_dir),
        "generated_files": generated_files,
        "promoted_path": str(promoted_path) if promoted_path else None,
        "backup_path": str(backup_dir) if backup_dir else None,
    }
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
