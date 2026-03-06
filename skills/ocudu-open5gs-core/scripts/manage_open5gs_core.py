#!/usr/bin/env python3
"""Manage the vendored Open5GS compose stack."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=False)


def stage_dir(workspace: Path) -> Path:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    path = workspace / "stages" / "ocudu-open5gs-core" / stamp
    path.mkdir(parents=True, exist_ok=True)
    return path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", default=".local/ocudu")
    parser.add_argument("--action", choices=["up", "down", "status"], default="status")
    parser.add_argument("--compose-file", default="assets/compose/docker-compose.open5gs.yml")
    parser.add_argument("--dry-run", action=argparse.BooleanOptionalAction, default=True)
    args = parser.parse_args()

    skill_dir = Path(__file__).resolve().parents[1]
    compose_path = (skill_dir / args.compose_file).resolve()
    compose_dir = compose_path.parent
    workspace = Path(args.workspace)
    out_dir = stage_dir(workspace)

    commands = {
        "up": ["docker", "compose", "-f", str(compose_path), "up", "-d", "--build"],
        "down": ["docker", "compose", "-f", str(compose_path), "down", "--remove-orphans"],
        "status": ["docker", "compose", "-f", str(compose_path), "ps"],
    }
    selected = commands[args.action]
    warnings: list[str] = []
    if shutil.which("docker") is None:
        warnings.append("docker is unavailable on PATH")

    if not args.dry_run and not warnings:
        proc = run(selected, compose_dir)
        (out_dir / "compose.log").write_text((proc.stdout or "") + (proc.stderr or ""), encoding="utf-8")
        if proc.returncode != 0:
            warnings.append(f"docker compose {args.action} failed")

    payload = {
        "passed": not warnings,
        "summary": "Open5GS core stage is ready." if not warnings else "Open5GS core stage needs review.",
        "warnings": warnings,
        "artifacts": [str(out_dir), str(compose_path)],
        "next_steps": ["Run ocudu-zmq-open5gs-e2e after the core reports healthy status."],
        "stage_dir": str(out_dir),
        "services": ["5gc"],
        "commands": [" ".join(selected)],
    }
    (out_dir / "summary.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
