#!/usr/bin/env bash
set -euo pipefail

workspace=".local/ocudu"
source_ref="main"
build_type="Release"
install_prefix="/usr/local"
bootstrap_deps="false"
enable_zeromq="false"
apply="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --workspace) workspace="$2"; shift 2 ;;
    --source-ref) source_ref="$2"; shift 2 ;;
    --build-type) build_type="$2"; shift 2 ;;
    --install-prefix) install_prefix="$2"; shift 2 ;;
    --bootstrap-deps) bootstrap_deps="true"; shift ;;
    --enable-zeromq) enable_zeromq="true"; shift ;;
    --apply) apply="true"; shift ;;
    *) echo "unknown argument: $1" >&2; exit 1 ;;
  esac
done

src_dir="${workspace}/src/srsRAN_Project"
build_dir="${workspace}/build/srsran-project"
zeromq_flag=""

if [[ "${enable_zeromq}" == "true" ]]; then
  zeromq_flag="-DENABLE_ZEROMQ=ON"
fi

run_cmd() {
  if [[ "${apply}" == "true" ]]; then
    echo "+ $*"
    "$@"
  else
    printf 'DRY-RUN:'
    printf ' %q' "$@"
    printf '\n'
  fi
}

mkdir_cmd() {
  run_cmd mkdir -p "$1"
}

if [[ "${bootstrap_deps}" == "true" ]]; then
  run_cmd sudo apt-get update
  run_cmd sudo apt-get install -y \
    cmake make gcc g++ pkg-config git \
    libfftw3-dev libmbedtls-dev libsctp-dev libyaml-cpp-dev libgtest-dev
fi

mkdir_cmd "${workspace}/src"
mkdir_cmd "${workspace}/build"

if [[ ! -d "${src_dir}/.git" ]]; then
  run_cmd git clone https://github.com/srsran/srsRAN_Project.git "${src_dir}"
else
  if [[ "${apply}" == "true" && -n "$(git -C "${src_dir}" status --porcelain)" ]]; then
    echo "source tree is dirty: ${src_dir}" >&2
    exit 1
  fi
  run_cmd git -C "${src_dir}" fetch --tags --prune origin
fi

run_cmd git -C "${src_dir}" checkout "${source_ref}"
mkdir_cmd "${build_dir}"
run_cmd cmake -S "${src_dir}" -B "${build_dir}" -DCMAKE_BUILD_TYPE="${build_type}" -DCMAKE_INSTALL_PREFIX="${install_prefix}" ${zeromq_flag}
run_cmd cmake --build "${build_dir}" --parallel
run_cmd ctest --test-dir "${build_dir}" --output-on-failure --parallel "$(nproc)"
run_cmd sudo cmake --install "${build_dir}"
