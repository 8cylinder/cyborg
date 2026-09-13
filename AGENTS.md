# AGENTS.md

Cyborg is a small Python CLI wrapping BorgBackup. Multiple backup profiles live
in one INI file.

## Commands

- Sync deps: `uv sync` (uv-managed; Python `>=3.11` pinned in `.python-version`)
- Lint: `uv run ruff check src/` — no ruff config, so defaults apply. There is a
  known pre-existing failure at `src/cyborg/cyborg.py:440` (F541, extraneous
  f-string); don't assume you caused it.
- Typecheck: `uv run ty check` — currently clean.
- Run the CLI: `uv run cyborg --help`
- No test suite, CI, pre-commit, or formatter config exists yet.

`ruff` and `ty` are declared as runtime dependencies (not a dev group), so
`uv run` resolves them without extra setup.

## Architecture

- `pyproject.toml` exposes `cyborg = "cyborg:main"` → `src/cyborg/__init__.py`
  re-exports `main` from `src/cyborg/cli.py`.
- `cli.py` is only click wiring. All real logic is module-level helpers and the
  `Borg` class in `src/cyborg/cyborg.py`.
- CLI shape is `cyborg <command> <profile>` (e.g. `cyborg run nas`,
  `cyborg config copy`). The README's `cyborg NAME COMMAND` table is stale; the
  inline cron comments in `default_config/config.ini` show the real order.
- Bundled templates (`config.ini`, `exclude*`, systemd scripts) live in
  `src/cyborg/default_config/` and are shipped via `[tool.uv_build] include`.
  That same directory is the last-resort active config in a dev checkout.

## Config resolution

`get_config_dir()` searches platform dir (`~/.config/cyborg` via platformdirs)
→ `~/.cyborg` → packaged `src/cyborg/default_config`. `cyborg config` prints the
active dir and validates each profile (path existence, exclude resolution).

## Gotchas

- Hardcoded personal paths are not portable: `cyborg.py:371` runs
  `/home/sm/bin/backup-apps-list`, and `default_config/config.ini` plus the
  exclude files reference `/home/sm`. Don't "fix" these without being asked.
- `Borg.__init__` aborts if `pidof -sx borg` reports a running borg. `error()`
  writes a `CYBORG-ERROR--*` file to `$HOME` and exits 1.
- `run` writes the installed-apps list, creates an archive named
  `{destination}::{hostname}__YYYY-MM-DD__HH-MM`, then auto-runs `prune` and
  writes `LAST-RUN`. Use `cyborg run <profile> --dry-run` when testing.
- `run_prog` joins the arg list and executes with `shell=True`; embedded quoting
  in command strings matters.
- `CLAUDE.md` and `GEMINI.md` are stale (they claim argparse, rclone, and a
  `USER_HOME` variable, none of which are in the code). Trust the source.
