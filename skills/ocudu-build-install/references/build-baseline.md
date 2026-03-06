# Build Baseline

- The current srsRAN Project installation guide documents a standard Linux source build using `git clone`, a dedicated build directory, `cmake`, `make`, `make test`, and `sudo make install`.
- The same guide lists an Ubuntu dependency set built around `cmake`, `make`, `gcc`, `g++`, `pkg-config`, `libfftw3-dev`, `libmbedtls-dev`, `libsctp-dev`, `libyaml-cpp-dev`, and `libgtest-dev`.
- Skillful RAN keeps that flow inside `.local/ocudu/` so scratch source and build trees stay out of tracked repo paths.
- Official sources:
  - https://docs.srsran.com/projects/project/en/latest/user_manuals/source/installation.html
  - https://github.com/srsran/srsRAN_Project
