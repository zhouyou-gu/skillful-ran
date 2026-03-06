#!/usr/bin/env python3
"""Run the Skillful RAN QA gate for a tracked skill."""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=False)


def stage_dir(workspace: Path) -> Path:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    path = workspace / "stages" / "skillful-ran-skill-test" / stamp
    path.mkdir(parents=True, exist_ok=True)
    return path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", default=".local/ocudu")
    parser.add_argument("--target-skill-id", required=True)
    parser.add_argument("--dry-run", action=argparse.BooleanOptionalAction, default=True)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[3]
    workspace = Path(args.workspace)
    out_dir = stage_dir(workspace)
    skill_dir = root / "skills" / args.target_skill_id
    checks: list[dict[str, str]] = []
    warnings: list[str] = []

    validator = run(["python3", "scripts/validate_skills.py"], root)
    checks.append({"name": "validate_skills", "status": "pass" if validator.returncode == 0 else "fail", "detail": "repo validation"})
    (out_dir / "validate_skills.log").write_text((validator.stdout or "") + (validator.stderr or ""), encoding="utf-8")

    if not skill_dir.exists():
        warnings.append(f"target skill not found: {args.target_skill_id}")
    else:
        eval_path = skill_dir / "evals" / "cases.jsonl"
        if eval_path.exists():
            lines = [line for line in eval_path.read_text(encoding="utf-8").splitlines() if line.strip()]
            checks.append({"name": "eval_cases", "status": "pass" if 8 <= len(lines) <= 12 else "fail", "detail": f"{len(lines)} cases"})
        else:
            checks.append({"name": "eval_cases", "status": "fail", "detail": "missing evals/cases.jsonl"})

        for script_path in sorted((skill_dir / "scripts").glob("*")) if (skill_dir / "scripts").exists() else []:
            if script_path.suffix == ".py":
                proc = run(["python3", "-m", "py_compile", str(script_path)], root)
                checks.append({"name": f"py_compile:{script_path.name}", "status": "pass" if proc.returncode == 0 else "fail", "detail": "syntax"})
                help_proc = run(["python3", str(script_path), "--help"], root)
                checks.append({"name": f"help:{script_path.name}", "status": "pass" if help_proc.returncode == 0 else "fail", "detail": "--help"})
            elif script_path.suffix == ".sh":
                proc = run(["bash", "-n", str(script_path)], root)
                checks.append({"name": f"bash-n:{script_path.name}", "status": "pass" if proc.returncode == 0 else "fail", "detail": "syntax"})

    passed = not warnings and all(check["status"] != "fail" for check in checks)
    report = {
        "target_skill_id": args.target_skill_id,
        "passed": passed,
        "checks": checks,
        "warnings": warnings,
        "generated_at": datetime.now(UTC).isoformat(),
    }
    report_path = out_dir / "qa-report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    payload = {
        "passed": passed,
        "summary": "Skill QA passed." if passed else "Skill QA failed or needs review.",
        "warnings": warnings,
        "artifacts": [str(out_dir)],
        "next_steps": ["Use skillful-ran-packaging only after this QA report passes."],
        "qa_report_path": str(report_path),
        "checks": checks,
    }
    print(json.dumps(payload, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
