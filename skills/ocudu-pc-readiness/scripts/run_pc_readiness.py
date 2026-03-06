#!/usr/bin/env python3
"""Collect a non-destructive PC readiness report for the OCUDU campaign."""

from __future__ import annotations

import argparse
import json
import platform
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path

REQUIRED_COMMANDS = ["git", "cmake", "make", "gcc", "g++", "pkg-config", "python3"]
RECOMMENDED_PACKAGES = [
    "libmbedtls-dev",
    "libsctp-dev",
    "libyaml-cpp-dev",
    "libgtest-dev",
]


def run(cmd: list[str]) -> tuple[bool, str]:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=10)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False, ""
    return proc.returncode == 0, (proc.stdout or proc.stderr).strip()


def make_stage_dir(workspace: Path) -> Path:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    path = workspace / "stages" / "ocudu-pc-readiness" / stamp
    path.mkdir(parents=True, exist_ok=True)
    return path


def command_checks() -> tuple[list[dict[str, str]], list[str]]:
    checks: list[dict[str, str]] = []
    blockers: list[str] = []
    for name in REQUIRED_COMMANDS:
        location = shutil.which(name)
        checks.append({"name": name, "status": "pass" if location else "fail", "detail": location or "not found"})
        if not location:
            blockers.append(f"command:{name}")
    return checks, blockers


def package_checks() -> tuple[list[dict[str, str]], list[str], list[str]]:
    if shutil.which("dpkg-query") is None:
        return [], [], ["dpkg-query is unavailable; package checks were skipped"]
    checks: list[dict[str, str]] = []
    blockers: list[str] = []
    for package in RECOMMENDED_PACKAGES:
        ok, output = run(["dpkg-query", "-W", "-f=${Status} ${Version}", package])
        installed = ok and "installed" in output
        checks.append({"name": package, "status": "pass" if installed else "fail", "detail": output or "not installed"})
        if not installed:
            blockers.append(f"package:{package}")
    return checks, blockers, []


def docker_checks() -> tuple[list[dict[str, str]], list[str]]:
    checks: list[dict[str, str]] = []
    blockers: list[str] = []
    probes = [
        ("docker", ["docker", "ps"]),
        ("docker compose", ["docker", "compose", "version"]),
    ]
    for name, cmd in probes:
        ok, output = run(cmd)
        checks.append({"name": name, "status": "pass" if ok else "fail", "detail": output or "unavailable"})
        if not ok:
            blockers.append(name.replace(" ", ":"))
    ok, _ = run(["sudo", "-n", "true"])
    checks.append(
        {
            "name": "sudo -n true",
            "status": "pass" if ok else "warn",
            "detail": "passwordless sudo available" if ok else "passwordless sudo unavailable",
        }
    )
    return checks, blockers


def storage_checks() -> tuple[list[dict[str, str]], list[str]]:
    checks: list[dict[str, str]] = []
    warnings: list[str] = []
    usage = shutil.disk_usage("/")
    free_gib = usage.free / (1024**3)
    checks.append({"name": "disk_free_gib", "status": "pass" if free_gib >= 100 else "warn", "detail": f"{free_gib:.1f} GiB free"})
    mem_total_kib = 0
    for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
        if line.startswith("MemTotal:"):
            mem_total_kib = int(line.split()[1])
            break
    mem_gib = mem_total_kib / (1024**2)
    checks.append({"name": "mem_total_gib", "status": "pass" if mem_gib >= 16 else "warn", "detail": f"{mem_gib:.1f} GiB total"})
    if free_gib < 100:
        warnings.append("Less than 100 GiB free on /. Image builds and cloned trees may be constrained.")
    if mem_gib < 16:
        warnings.append("Less than 16 GiB RAM detected. Builds and local runtime may be unstable.")
    return checks, warnings


def hardware_summary(check_usb: bool, profile: str) -> dict[str, object]:
    hardware: dict[str, object] = {"profile": profile, "kernel": platform.release(), "arch": platform.machine()}
    ok, cpu = run(["lscpu"])
    if ok:
        for line in cpu.splitlines():
            if line.startswith("Model name:"):
                hardware["cpu"] = line.split(":", 1)[1].strip()
                break
    ok, pci = run(["lspci"])
    if ok:
        hardware["pcie"] = [
            line.strip()
            for line in pci.splitlines()
            if "VGA compatible controller" in line or "Ethernet controller" in line or "Network controller" in line
        ]
    if check_usb:
        ok, usb = run(["lsusb"])
        hardware["usb"] = [line.strip() for line in usb.splitlines() if line.strip()] if ok else []
    return hardware


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", default=".local/ocudu")
    parser.add_argument("--profile", default="ubuntu-24.04-gaming-pc")
    parser.add_argument("--check-docker", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--check-storage", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--check-usb", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--dry-run", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--strict", action=argparse.BooleanOptionalAction, default=False)
    args = parser.parse_args()

    workspace = Path(args.workspace)
    workspace.mkdir(parents=True, exist_ok=True)
    stage_dir = make_stage_dir(workspace)

    checks, blockers = command_checks()
    package_results, package_blockers, warnings = package_checks()
    checks.extend(package_results)
    blockers.extend(package_blockers)

    if args.check_docker:
        docker_results, docker_blockers = docker_checks()
        checks.extend(docker_results)
        blockers.extend(docker_blockers)

    if args.check_storage:
        storage_results, storage_warnings = storage_checks()
        checks.extend(storage_results)
        warnings.extend(storage_warnings)

    started_at = datetime.now(UTC).isoformat()
    finished_at = datetime.now(UTC).isoformat()
    passed = not blockers if args.strict else not any(item.startswith("docker") for item in blockers)
    payload = {
        "stage_id": "ocudu-pc-readiness",
        "lane": "shared",
        "started_at": started_at,
        "finished_at": finished_at,
        "passed": passed,
        "summary": (
            "PC baseline is ready for the container-first OCUDU campaign."
            if passed
            else "PC baseline still has blockers for the container-first OCUDU campaign."
        ),
        "warnings": warnings,
        "artifacts": [str(stage_dir)],
        "next_steps": [
            "Review the blocker list before starting build or runtime stages.",
            "Use ocudu-docker-build-env next once Docker access is acceptable.",
        ],
        "blockers": sorted(set(blockers)),
        "checks": checks,
        "stage_dir": str(stage_dir),
        "hardware": hardware_summary(args.check_usb, args.profile),
        "source_refs": [],
        "container_images": [],
        "commands": [],
    }
    (stage_dir / "summary.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
