#!/usr/bin/env bash
set -euo pipefail

workspace=".local/ocudu"
build_dir=""
mode="local-build"
install_prefix="/usr/local"
run_ctest="true"
dry_run="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --workspace) workspace="$2"; shift 2 ;;
    --build-dir) build_dir="$2"; shift 2 ;;
    --mode) mode="$2"; shift 2 ;;
    --install-prefix) install_prefix="$2"; shift 2 ;;
    --run-ctest) run_ctest="$2"; shift 2 ;;
    --dry-run) dry_run="$2"; shift 2 ;;
    *) echo "unknown argument: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "${build_dir}" ]]; then
  build_dir="${workspace}/build/srsran-project"
fi

run_cmd() {
  if [[ "${dry_run}" == "true" ]]; then
    printf 'DRY-RUN:'
    printf ' %q' "$@"
    printf '\n'
  else
    echo "+ $*"
    "$@"
  fi
}

find_gnb() {
  local root="$1"
  find "${root}" -maxdepth 4 -type f -name gnb -perm -111 2>/dev/null | head -n 1
}

case "${mode}" in
  local-build)
    test -d "${build_dir}"
    gnb_path="$(find_gnb "${build_dir}")"
    [[ -n "${gnb_path}" ]]
    run_cmd "${gnb_path}" --help
    if [[ "${run_ctest}" == "true" ]]; then
      run_cmd ctest --test-dir "${build_dir}" --output-on-failure --parallel "$(nproc)"
    fi
    ;;
  install-check)
    gnb_path="$(find_gnb "${install_prefix}")"
    [[ -n "${gnb_path}" ]]
    run_cmd "${gnb_path}" --help
    ;;
  zeromq-readiness)
    cache_file="${build_dir}/CMakeCache.txt"
    test -f "${cache_file}"
    grep -q 'ENABLE_ZEROMQ:BOOL=ON' "${cache_file}"
    ;;
  *)
    echo "unsupported mode: ${mode}" >&2
    exit 1
    ;;
esac
