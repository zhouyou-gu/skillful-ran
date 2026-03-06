#!/usr/bin/env python3
"""Run the software-only ZMQ proof-of-concept lane."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path


def run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=False)


def stage_dir(workspace: Path) -> Path:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    path = workspace / "stages" / "ocudu-zmq-open5gs-e2e" / stamp
    path.mkdir(parents=True, exist_ok=True)
    return path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", default=".local/ocudu")
    parser.add_argument("--project-install-dir", default=".local/ocudu/install/srsran-project")
    parser.add_argument("--ue-install-dir", default=".local/ocudu/install/srsran-4g")
    parser.add_argument("--project-image", default="skillful-ran/srsran-project-build:release_25_10")
    parser.add_argument("--ue-image", default="skillful-ran/srsran-4g-ue-build:release_23_11")
    parser.add_argument("--duration-seconds", type=int, default=120)
    parser.add_argument("--dry-run", action=argparse.BooleanOptionalAction, default=True)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[3]
    workspace = Path(args.workspace)
    out_dir = stage_dir(workspace)
    config_dir = Path(__file__).resolve().parents[1] / "assets" / "config"
    compose_file = root / "skills" / "ocudu-open5gs-core" / "assets" / "compose" / "docker-compose.open5gs.yml"
    gnb_name = "skillful-ran-gnb"
    ue_name = "skillful-ran-srsue"

    commands = [
        f"docker compose -f {compose_file} ps",
        f"docker run -d --name {gnb_name} --network host -v {args.project_install_dir}:/install:ro -v {config_dir}:/config:ro -v {out_dir}:/stage {args.project_image} bash -lc \"export PATH=/install/bin:$PATH; export LD_LIBRARY_PATH=/install/lib:${{LD_LIBRARY_PATH:-}}; gnb -c /config/gnb_zmq.yaml >/stage/gnb.log 2>&1\"",
        f"docker run -d --name {ue_name} --network host --privileged --cap-add NET_ADMIN --device /dev/net/tun -v {args.ue_install_dir}:/install:ro -v {config_dir}:/config:ro -v {out_dir}:/stage {args.ue_image} bash -lc \"mkdir -p /run/netns; ip netns add ue1 2>/dev/null || true; export PATH=/install/bin:$PATH; export LD_LIBRARY_PATH=/install/lib:${{LD_LIBRARY_PATH:-}}; srsue /config/ue_zmq.conf >/stage/ue.log 2>&1\"",
        f"docker exec {ue_name} ip netns exec ue1 ping -c 4 10.45.1.1",
    ]

    warnings: list[str] = []
    if shutil.which("docker") is None:
        warnings.append("docker is unavailable on PATH")
    if not Path(args.project_install_dir).exists():
        warnings.append(f"missing project install tree: {args.project_install_dir}")
    if not Path(args.ue_install_dir).exists():
        warnings.append(f"missing UE install tree: {args.ue_install_dir}")

    if not args.dry_run and not warnings:
        status = run(["docker", "compose", "-f", str(compose_file), "ps"], cwd=compose_file.parent)
        (out_dir / "core-status.log").write_text((status.stdout or "") + (status.stderr or ""), encoding="utf-8")
        if status.returncode != 0:
            warnings.append("Open5GS core status check failed")

        run(["docker", "rm", "-f", gnb_name])
        run(["docker", "rm", "-f", ue_name])

        gnb = run(
            [
                "docker",
                "run",
                "-d",
                "--name",
                gnb_name,
                "--network",
                "host",
                "-v",
                f"{args.project_install_dir}:/install:ro",
                "-v",
                f"{config_dir}:/config:ro",
                "-v",
                f"{out_dir}:/stage",
                args.project_image,
                "bash",
                "-lc",
                "export PATH=/install/bin:$PATH; export LD_LIBRARY_PATH=/install/lib:${LD_LIBRARY_PATH:-}; gnb -c /config/gnb_zmq.yaml >/stage/gnb.log 2>&1",
            ]
        )
        if gnb.returncode != 0:
            warnings.append("gNB container failed to start")

        ue = run(
            [
                "docker",
                "run",
                "-d",
                "--name",
                ue_name,
                "--network",
                "host",
                "--privileged",
                "--cap-add",
                "NET_ADMIN",
                "--device",
                "/dev/net/tun",
                "-v",
                f"{args.ue_install_dir}:/install:ro",
                "-v",
                f"{config_dir}:/config:ro",
                "-v",
                f"{out_dir}:/stage",
                args.ue_image,
                "bash",
                "-lc",
                "mkdir -p /run/netns; ip netns add ue1 2>/dev/null || true; export PATH=/install/bin:$PATH; export LD_LIBRARY_PATH=/install/lib:${LD_LIBRARY_PATH:-}; srsue /config/ue_zmq.conf >/stage/ue.log 2>&1",
            ]
        )
        if ue.returncode != 0:
            warnings.append("srsUE container failed to start")

        time.sleep(args.duration_seconds)
        ping = run(["docker", "exec", ue_name, "ip", "netns", "exec", "ue1", "ping", "-c", "4", "10.45.1.1"])
        (out_dir / "ping.log").write_text((ping.stdout or "") + (ping.stderr or ""), encoding="utf-8")
        if ping.returncode != 0:
            warnings.append("attach plus ping check failed")

        for name in (gnb_name, ue_name):
            logs = run(["docker", "logs", name])
            (out_dir / f"{name}.log").write_text((logs.stdout or "") + (logs.stderr or ""), encoding="utf-8")
            run(["docker", "rm", "-f", name])

    payload = {
        "passed": not warnings,
        "summary": "ZMQ proof-of-concept lane is ready." if not warnings else "ZMQ proof-of-concept lane needs review.",
        "warnings": warnings,
        "artifacts": [str(out_dir)],
        "next_steps": ["Promote stable commands and notes only after reviewing the stage logs."],
        "stage_dir": str(out_dir),
        "config_paths": [str(config_dir / "gnb_zmq.yaml"), str(config_dir / "ue_zmq.conf")],
        "commands": commands,
    }
    (out_dir / "summary.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
