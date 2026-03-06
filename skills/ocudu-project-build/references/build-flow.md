# Build Flow

Workspace layout used by the helper:

- `src/srsran-project`
- `build/srsran-project`
- `install/srsran-project`
- `stages/ocudu-project-build/<timestamp>/`

The helper records:

- clone or fetch commands
- Docker build command used for the compile environment
- cmake configure, build, test, and install commands
- a compact `summary.json`
