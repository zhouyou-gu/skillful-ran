#!/usr/bin/env python3
"""Build or plan the repo-owned Docker images used by the campaign."""

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
    path = workspace / "stages" / "ocudu-docker-build-env" / stamp
    path.mkdir(parents=True, exist_ok=True)
    return path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", default=".local/ocudu")
    parser.add_argument("--image-set", choices=["project", "ue", "all"], default="all")
    parser.add_argument("--project-image", default="skillful-ran/srsran-project-build:release_25_10")
    parser.add_argument("--ue-image", default="skillful-ran/srsran-4g-ue-build:release_23_11")
    parser.add_argument("--dry-run", action=argparse.BooleanOptionalAction, default=True)
    args = parser.parse_args()

    workspace = Path(args.workspace)
    workspace.mkdir(parents=True, exist_ok=True)
    out_dir = stage_dir(workspace)
    skill_dir = Path(__file__).resolve().parents[1]
    docker_dir = skill_dir / "assets" / "docker"

    targets = []
    if args.image_set in {"project", "all"}:
        targets.append((args.project_image, docker_dir / "srsran-project-build.Dockerfile"))
    if args.image_set in {"ue", "all"}:
        targets.append((args.ue_image, docker_dir / "srsran-4g-ue-build.Dockerfile"))

    commands = [f"docker build -f {dockerfile} -t {image} {docker_dir}" for image, dockerfile in targets]
    warnings: list[str] = []
    if shutil.which("docker") is None:
        warnings.append("docker is unavailable on PATH")

    if not args.dry_run and not warnings:
        for image, dockerfile in targets:
            proc = run(["docker", "build", "-f", str(dockerfile), "-t", image, str(docker_dir)], skill_dir)
            (out_dir / f"{image.split('/')[-1].replace(':', '_')}.log").write_text(
                (proc.stdout or "") + (proc.stderr or ""),
                encoding="utf-8",
            )
            if proc.returncode != 0:
                warnings.append(f"docker build failed for {image}")

    payload = {
        "passed": not warnings,
        "summary": "Docker build environment is ready." if not warnings else "Docker build environment needs review.",
        "warnings": warnings,
        "artifacts": [str(out_dir)],
        "next_steps": ["Run ocudu-project-build or srsran-4g-ue-build next."],
        "stage_dir": str(out_dir),
        "images": [image for image, _ in targets],
        "commands": commands,
    }
    (out_dir / "summary.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
