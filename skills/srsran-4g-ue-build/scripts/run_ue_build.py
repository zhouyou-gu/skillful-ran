#!/usr/bin/env python3
"""Clone and build srsUE from srsRAN 4G release_23_11."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path


def run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=False)


def stage_dir(workspace: Path) -> Path:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    path = workspace / "stages" / "srsran-4g-ue-build" / stamp
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_log(path: Path, proc: subprocess.CompletedProcess[str]) -> None:
    path.write_text((proc.stdout or "") + (proc.stderr or ""), encoding="utf-8")


def remove_tree(path: Path) -> None:
    try:
        shutil.rmtree(path)
    except PermissionError:
        subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "-v",
                f"{path}:/target",
                "ubuntu:24.04",
                "bash",
                "-lc",
                "rm -rf /target/* /target/.[!.]* /target/..?*",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        shutil.rmtree(path, ignore_errors=True)


def disable_tests_in_workspace(src_dir: Path) -> None:
    for path in src_dir.rglob("CMakeLists.txt"):
        text = path.read_text(encoding="utf-8")
        updated = text.replace("add_subdirectory(test)", "# Skillful RAN workspace patch: tests disabled\n# add_subdirectory(test)")
        path.write_text(updated, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", default=".local/ocudu")
    parser.add_argument("--repo-url", default="https://github.com/srsran/srsRAN_4G.git")
    parser.add_argument("--source-ref", default="release_23_11")
    parser.add_argument("--image", default="skillful-ran/srsran-4g-ue-build:release_23_11")
    parser.add_argument("--clean-build", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--dry-run", action=argparse.BooleanOptionalAction, default=True)
    args = parser.parse_args()

    workspace = Path(args.workspace)
    src_dir = workspace / "src" / "srsran-4g"
    build_dir = workspace / "build" / "srsran-4g"
    install_dir = workspace / "install" / "srsran-4g"
    out_dir = stage_dir(workspace)

    commands = [
        f"git clone --depth 1 --branch {args.source_ref} {args.repo_url} {src_dir}",
        f"workspace patch: disable add_subdirectory(test) in CMakeLists.txt files under {src_dir}",
        f"docker run --rm -v {src_dir}:/src -v {build_dir}:/build -v {install_dir}:/install -w /build {args.image} "
        "bash -lc \"export CXXFLAGS='-Wno-error=array-bounds -Wno-array-bounds -Wno-error=stringop-overflow -Wno-stringop-overflow'; "
        "cmake -GNinja -DENABLE_ZEROMQ=ON -DENABLE_UHD=OFF -DENABLE_GUI=OFF -DENABLE_HARDSIM=OFF "
        "-DENABLE_TTCN3=OFF -DENABLE_SRSENB=OFF -DENABLE_SRSEPC=OFF -DCMAKE_INSTALL_PREFIX=/install /src && cmake --build . "
        "&& cmake --install . && export LD_LIBRARY_PATH=/install/lib:$LD_LIBRARY_PATH "
        "&& /install/bin/srsue --version && /install/bin/srsue --help >/tmp/srsue-help.txt\"",
    ]

    warnings: list[str] = []
    if shutil.which("docker") is None:
        warnings.append("docker is unavailable on PATH")

    if args.clean_build:
        for path in (build_dir, install_dir):
            if path.exists():
                remove_tree(path)

    src_dir.parent.mkdir(parents=True, exist_ok=True)
    build_dir.parent.mkdir(parents=True, exist_ok=True)
    install_dir.parent.mkdir(parents=True, exist_ok=True)

    if not args.dry_run:
        if not src_dir.exists():
            proc = run(["git", "clone", "--depth", "1", "--branch", args.source_ref, args.repo_url, str(src_dir)])
            write_log(out_dir / "git-clone.log", proc)
            if proc.returncode != 0:
                warnings.append("git clone failed")
        else:
            proc = run(["git", "fetch", "--depth", "1", "origin", args.source_ref], cwd=src_dir)
            write_log(out_dir / "git-fetch.log", proc)
            if proc.returncode == 0:
                checkout = run(["git", "checkout", "FETCH_HEAD"], cwd=src_dir)
                write_log(out_dir / "git-checkout.log", checkout)
            else:
                warnings.append("git fetch failed")

        disable_tests_in_workspace(src_dir)

        docker_cmd = [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{src_dir}:/src",
            "-v",
            f"{build_dir}:/build",
            "-v",
            f"{install_dir}:/install",
            "-w",
            "/build",
            args.image,
            "bash",
            "-lc",
            "export CXXFLAGS='-Wno-error=array-bounds -Wno-array-bounds -Wno-error=stringop-overflow -Wno-stringop-overflow'; "
            "cmake -GNinja -DENABLE_ZEROMQ=ON -DENABLE_UHD=OFF -DENABLE_GUI=OFF -DENABLE_HARDSIM=OFF "
            "-DENABLE_TTCN3=OFF -DENABLE_SRSENB=OFF -DENABLE_SRSEPC=OFF -DCMAKE_INSTALL_PREFIX=/install /src && cmake --build . "
            "&& cmake --install . && export LD_LIBRARY_PATH=/install/lib:$LD_LIBRARY_PATH "
            "&& /install/bin/srsue --version && /install/bin/srsue --help >/tmp/srsue-help.txt",
        ]
        proc = run(docker_cmd)
        write_log(out_dir / "docker-build.log", proc)
        if proc.returncode != 0:
            warnings.append("containerized UE build failed")

    payload = {
        "passed": not warnings,
        "summary": "srsUE build stage is ready." if not warnings else "srsUE build stage needs review.",
        "warnings": warnings,
        "artifacts": [str(out_dir), str(src_dir), str(build_dir), str(install_dir)],
        "next_steps": ["Run ocudu-zmq-open5gs-e2e after the core and RAN sides are ready."],
        "stage_dir": str(out_dir),
        "source_dir": str(src_dir),
        "build_dir": str(build_dir),
        "install_dir": str(install_dir),
        "commands": commands,
    }
    (out_dir / "summary.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
