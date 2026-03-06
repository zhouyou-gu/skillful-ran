# Pinned Source

- Repository: `https://github.com/srsran/srsRAN_Project.git`
- Ref: `release_25_10`
- Build model: Docker image installs the build dependencies, then bind-mounts source, build, and install trees from `.local/ocudu/`.
- Default cmake flags:
  - `-GNinja`
  - `-DENABLE_ZEROMQ=ON`
  - `-DENABLE_UHD=OFF`
  - `-DBUILD_TESTING=ON`
  - `-DCMAKE_INSTALL_PREFIX=/install`
- Validation scope on this PC:
  - avoid the full upstream `ctest` sweep
  - verify `gnb --version`, `srscu --version`, `srsdu --version`
  - run the built ZMQ unit tests only
