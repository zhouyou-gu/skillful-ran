#!/usr/bin/env python3
"""Collect a compact, non-destructive host readiness report."""

from __future__ import annotations

import argparse
import json
import platform
import shutil
import subprocess
from pathlib import Path

REQUIRED_COMMANDS = ["git", "cmake", "make", "gcc", "g++", "pkg-config", "python3"]
RECOMMENDED_PACKAGES = [
    "libfftw3-dev",
    "libmbedtls-dev",
    "libsctp-dev",
    "libyaml-cpp-dev",
    "libgtest-dev",
]


def run(cmd: list[str]) -> tuple[bool, str]:
    try:
        proc = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False, ""
    output = (proc.stdout or proc.stderr).strip()
    return proc.returncode == 0, output


def load_os_release() -> dict[str, str]:
    path = Path("/etc/os-release")
    data: dict[str, str] = {}
    if not path.exists():
        return data
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key] = value.strip().strip('"')
    return data


def command_checks() -> tuple[list[dict[str, str]], list[str]]:
    checks: list[dict[str, str]] = []
    missing: list[str] = []
    for name in REQUIRED_COMMANDS:
        location = shutil.which(name)
        status = "pass" if location else "fail"
        checks.append({"name": name, "status": status, "detail": location or "not found"})
        if not location:
            missing.append(f"command:{name}")
    return checks, missing


def package_checks() -> tuple[list[dict[str, str]], list[str], list[str]]:
    checks: list[dict[str, str]] = []
    missing: list[str] = []
    warnings: list[str] = []

    if shutil.which("dpkg-query") is None:
        warnings.append("dpkg-query is unavailable; package validation was skipped")
        return checks, missing, warnings

    for package in RECOMMENDED_PACKAGES:
        ok, output = run(["dpkg-query", "-W", "-f=${Status} ${Version}", package])
        if ok and "installed" in output:
            checks.append({"name": package, "status": "pass", "detail": output})
            continue
        checks.append({"name": package, "status": "fail", "detail": output or "not installed"})
        missing.append(f"package:{package}")
    return checks, missing, warnings


def hardware_summary(check_network: bool) -> dict[str, object]:
    os_release = load_os_release()
    hardware: dict[str, object] = {
        "profile_os": os_release.get("PRETTY_NAME", platform.platform()),
        "kernel": platform.release(),
        "arch": platform.machine(),
    }

    ok, cpu = run(["lscpu"])
    if ok and cpu:
        for line in cpu.splitlines():
            if line.startswith("Model name:"):
                hardware["cpu"] = line.split(":", 1)[1].strip()
                break

    ok, gpu = run(["lspci"])
    if ok and gpu:
        hardware["pcie_summary"] = [
            line.strip()
            for line in gpu.splitlines()
            if "VGA compatible controller" in line or "Ethernet controller" in line or "Network controller" in line
        ]

    if check_network:
        ok, links = run(["ip", "-brief", "link"])
        if ok and links:
            hardware["interfaces"] = [line.strip() for line in links.splitlines() if line.strip()]

    return hardware


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", default=".local/ocudu")
    parser.add_argument("--profile", default="ubuntu-24.04-gaming-pc")
    parser.add_argument("--check-network", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--check-packages", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--strict", action=argparse.BooleanOptionalAction, default=False)
    args = parser.parse_args()

    checks: list[dict[str, str]] = []
    warnings: list[str] = []
    missing: list[str] = []

    cmd_checks, cmd_missing = command_checks()
    checks.extend(cmd_checks)
    missing.extend(cmd_missing)

    if args.check_packages:
        pkg_checks, pkg_missing, pkg_warnings = package_checks()
        checks.extend(pkg_checks)
        missing.extend(pkg_missing)
        warnings.extend(pkg_warnings)

    workspace = Path(args.workspace)
    if not workspace.exists():
        warnings.append(f"workspace {workspace} does not exist yet; create it before build work")

    passed = not missing if args.strict else not any(item.startswith("command:") for item in missing)
    hardware = hardware_summary(args.check_network)
    hardware["profile"] = args.profile
    summary = "Host baseline looks ready for the documented OCUDU build flow." if passed else "Host baseline is incomplete for the documented OCUDU build flow."

    next_steps = []
    if missing:
        next_steps.append("Install the missing commands or Ubuntu packages called out in the audit.")
    next_steps.append("Run ocudu-build-install only after the host baseline is acceptable.")

    payload = {
        "passed": passed,
        "summary": summary,
        "warnings": warnings,
        "artifacts": [str(workspace.resolve())] if workspace.exists() else [str(workspace)],
        "next_steps": next_steps,
        "hardware": hardware,
        "missing": missing,
        "checks": checks,
    }
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
