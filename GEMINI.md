# Cyborg

**Cyborg** is a Python wrapper around [BorgBackup](https://borgbackup.readthedocs.io) and [Rclone](https://rclone.org) designed to simplify local and remote backups. It uses a configuration file to manage backup profiles, sources, destinations, and exclusions.

## Project Overview

*   **Primary Language:** Python (Requires >= 3.11)
*   **Core Dependencies:** `borgbackup`, `rclone`, `pidof` (system binaries)
*   **Configuration:** `~/.cyborg/config.ini` (INI format)
*   **Entry Point:** `src/cyborg/cyborg.py` (Script intended for direct execution or symlinking)

## Key Features

*   **Automated Backups:** Wraps `borg create` with standard options (compression, exclusion).
*   **Pruning:** Automates `borg prune` to manage backup retention.
*   **Remote Sync:** Optionally syncs the local Borg repository to a remote destination using `rclone`.
*   **Profiles:** Supports multiple backup configurations via named sections in `config.ini`.
*   **Status & Helpers:** commands to check backup status and generate helper commands.

## Configuration

The application searches for its configuration directory in the following order:
1.  Standard platform-specific location (e.g., `~/.config/cyborg` on Linux, `~/Library/Application Support/cyborg` on macOS).
2.  Legacy `~/.cyborg` directory.
3.  Project root directory (`.cyborg` folder within the project).

### `config.ini`
The main configuration file. It supports multiple sections for different backup profiles.

```ini
[default]
destination = /path/to/local/backup/repo
source = /home/user, /etc
exclude = /home/user/.cyborg/exclude
# Optional remote sync
remote_destination = remote_name:bucket/path

[another_profile]
destination = /another/path
source = /home/user/documents
exclude = /home/user/.cyborg/exclude-docs
passphrase = secret-passphrase
```

**Keys:**
*   `destination`: Path to the local Borg repository.
*   `source`: Comma-separated list of directories to back up.
*   `exclude`: Path to an exclusion file (compatible with `borg --exclude-from`).
*   `remote_destination`: (Optional) Rclone remote destination (e.g., `remote:bucket`).
*   `passphrase`: (Optional) Borg passphrase. If omitted, it may prompt or use environment variables.

### Exclusion Files
Text files listing patterns to exclude from the backup (e.g., `~/.cyborg/exclude`).

## Usage

The script is typically run directly or symlinked to a directory in `PATH` (e.g., `~/bin/cyborg`).

### Common Commands

*   **Run Default Backup:**
    ```bash
    python3 src/cyborg/cyborg.py run
    ```

*   **Run with Remote Sync:**
    ```bash
    python3 src/cyborg/cyborg.py run --remote
    ```

*   **Run Specific Profile:**
    ```bash
    python3 src/cyborg/cyborg.py --name=another_profile run
    ```

*   **Prune Repository:**
    ```bash
    python3 src/cyborg/cyborg.py prune
    ```

*   **Check Status:**
    ```bash
    python3 src/cyborg/cyborg.py status
    ```

*   **Show Manual Commands:**
    ```bash
    python3 src/cyborg/cyborg.py extras
    ```

## Development Notes

*   **Hardcoded Paths:** The script currently contains hardcoded paths (e.g., `USER_HOME = '/home/sm'`). This needs to be generalized for portability.
*   **Helper Scripts:** The `run` command expects helper scripts in `~/bin/`:
    *   `backup-apps-list`: Generates a list of installed applications.
    *   `cron-notify-send`: Sends desktop notifications (currently commented out/disabled in some parts).
*   **Entry Point Discrepancy:** `pyproject.toml` defines `cyborg = "cyborg:main"`, which points to `src/cyborg/__init__.py`. However, the core logic is in `src/cyborg/cyborg.py`. The project seems to be in a transition state between a standalone script and a proper Python package.
