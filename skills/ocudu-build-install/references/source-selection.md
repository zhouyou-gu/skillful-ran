# Source Selection

- Prefer an explicit tag or commit for repeatable lab notes.
- Use `main` only when the user explicitly wants the newest upstream behavior.
- Record the chosen `source_ref` in build notes so later smoke tests point at the same tree.
- Keep the upstream clone under `.local/ocudu/src/` and the build tree under `.local/ocudu/build/`.
