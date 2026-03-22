# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Does

Cyborg is a Python wrapper around [BorgBackup](https://borgbackup.readthedocs.io) and [Rclone](https://rclone.org) that automates local and remote backups via a simple CLI. It reads profiles from a config file and runs borg/rclone commands with standard options.

## Development Commands

Uses `uv` for dependency management:

```bash
uv run cyborg run            # Run a backup
uv run cyborg prune          # Prune the repository
uv run cyborg status         # Show backup status and helpful commands
uv run cyborg extras         # Print example borg/rclone commands
uv run cyborg rclone         # Sync to remote via rclone
uv run cyborg --name=borgbase run  # Use a specific config profile
uv run cyborg run --dry-run  # Dry run (no actual changes)
```

No test suite or linter is configured yet.

## Architecture

### Entry Points

- `pyproject.toml` defines `cyborg = "cyborg:main"`
- `src/cyborg/__init__.py` imports `main` from `cli.py`
- `src/cyborg/cli.py` — argparse-based CLI; parses subcommands and delegates to `Borg` class
- `src/cyborg/cyborg.py` — core `Borg` class with all backup logic

### Configuration

Config file (`config.ini`) is loaded from (in order of precedence):
1. Platform config dir (e.g., `~/.config/cyborg/` on Linux)
2. `~/.cyborg/`
3. `.cyborg/` in the project root

Each section in the INI file is a named profile:

```ini
[profile_name]
destination = /path/to/borg/repo   # required
source = /home/user, /etc          # required
exclude = /path/to/exclude-file    # required
remote_destination = remote:bucket # optional, for rclone
passphrase = secret                # optional
```

The `.cyborg/` directory in this repo serves as a working example config.

### Key Implementation Details

- `USER_HOME = '/home/sm'` is hardcoded in `cyborg.py:16` — needs generalization
- The `notify()` function (desktop notifications) always returns early (disabled)
- Before running, checks if borg/rclone is already running via `pidof`
- On error, writes an alert file to `~/` with a timestamp
- Archive naming: `{destination}::{hostname}__YYYY-MM-DD__HH-MM`
- Default retention: 2 days, 14 daily, 4 weekly, 6 monthly, 1 yearly
