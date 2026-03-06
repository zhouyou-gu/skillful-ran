#!/usr/bin/env python3
"""Run the software-only local OCUDU lane inside one container."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True, check=False)


def stage_dir(workspace: Path) -> Path:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    path = workspace / "stages" / "ocudu-local-runtime-test" / stamp
    path.mkdir(parents=True, exist_ok=True)
    return path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", default=".local/ocudu")
    parser.add_argument("--install-dir", default=".local/ocudu/install/srsran-project")
    parser.add_argument("--image", default="skillful-ran/srsran-project-build:release_25_10")
    parser.add_argument("--duration-seconds", type=int, default=60)
    parser.add_argument("--dry-run", action=argparse.BooleanOptionalAction, default=True)
    args = parser.parse_args()

    workspace = Path(args.workspace)
    install_dir = Path(args.install_dir)
    out_dir = stage_dir(workspace)
    asset_dir = Path(__file__).resolve().parents[1] / "assets" / "config"
    config_paths = [asset_dir / "local_cu_cp_no_core.yml", asset_dir / "local_cu_up_no_core.yml", asset_dir / "local_du_zmq_testmode.yml"]

    shell = (
        "export PATH=/install/bin:$PATH; "
        "srscucp -c /assets/local_cu_cp_no_core.yml >/stage/cu_cp.log 2>&1 & "
        "CUCP=$!; "
        "srscuup -c /assets/local_cu_up_no_core.yml >/stage/cu_up.log 2>&1 & "
        "CUUP=$!; "
        "srsdu -c /assets/local_du_zmq_testmode.yml >/stage/du.log 2>&1 & "
        "DU=$!; "
        f"sleep {args.duration_seconds}; "
        "kill $DU $CUUP $CUCP; wait $DU $CUUP $CUCP || true"
    )
    command = (
        f"docker run --rm --network host -v {install_dir}:/install:ro -v {asset_dir}:/assets:ro "
        f"-v {out_dir}:/stage {args.image} bash -lc \"{shell}\""
    )

    warnings: list[str] = []
    if shutil.which("docker") is None:
        warnings.append("docker is unavailable on PATH")
    if not install_dir.exists():
        warnings.append(f"install tree is missing: {install_dir}")

    if not args.dry_run and not warnings:
        proc = run(
            [
                "docker",
                "run",
                "--rm",
                "--network",
                "host",
                "-v",
                f"{install_dir}:/install:ro",
                "-v",
                f"{asset_dir}:/assets:ro",
                "-v",
                f"{out_dir}:/stage",
                args.image,
                "bash",
                "-lc",
                shell,
            ]
        )
        (out_dir / "runtime.log").write_text((proc.stdout or "") + (proc.stderr or ""), encoding="utf-8")
        if proc.returncode != 0:
            warnings.append("local runtime container exited non-zero")

    payload = {
        "passed": not warnings,
        "summary": "Local split-lane runtime stage is ready." if not warnings else "Local split-lane runtime stage needs review.",
        "warnings": warnings,
        "artifacts": [str(out_dir)],
        "next_steps": ["Use ocudu-open5gs-core or ocudu-zmq-open5gs-e2e after this stage is stable."],
        "stage_dir": str(out_dir),
        "config_paths": [str(path) for path in config_paths],
        "commands": [command],
    }
    (out_dir / "summary.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
