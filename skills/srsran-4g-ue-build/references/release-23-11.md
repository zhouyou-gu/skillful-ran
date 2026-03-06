# Pinned UE Source

- Repository: `https://github.com/srsran/srsRAN_4G.git`
- Ref: `release_23_11`
- Role in this repo: build `srsUE` for the software-only ZMQ proof-of-concept lane
- Important boundary:
  - this is a prototype 5G UE path
  - do not present it as production-grade validation
- Current build note on this PC:
  - upstream ASN.1 test targets trip `-Werror=array-bounds` under the current GCC 13 toolchain
  - parts of `srsUE` itself also hit GCC 13 `array-bounds` warnings promoted to errors
  - this skill therefore patches the cloned workspace to skip test subdirectory inclusion, disables `srsENB` and `srsEPC`, and applies narrow warning overrides before verifying the built `srsUE` binary directly
  - the installed binary also needs `LD_LIBRARY_PATH=/install/lib:$LD_LIBRARY_PATH` during container-side verification
