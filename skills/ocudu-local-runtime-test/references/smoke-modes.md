# Smoke Modes

- `local-build`: confirm the build directory exists, detect an executable `gnb` binary, and optionally run `ctest`.
- `install-check`: confirm an installed `gnb` binary exists under the chosen install prefix and responds to `--help`.
- `zeromq-readiness`: inspect `CMakeCache.txt` for `ENABLE_ZEROMQ=ON` before making local transport claims.
- These checks are intentionally workstation-local and do not prove RU, RF, or production readiness.
