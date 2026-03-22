# 🤖 Cyborg

A Python wrapper around [BorgBackup](https://borgbackup.readthedocs.io) that
automates backups via a simple CLI. Multiple backup profiles are defined in a
single config file.

## Requirements

- Python 3.11+
- [BorgBackup](https://borgbackup.readthedocs.io/en/stable/installation.html)
- [uv](https://docs.astral.sh/uv/) (for installation)

## Installation

```bash
uv tool install .
```

## Setup

**1. Install the default config:**

```bash
cyborg config copy
```

This copies the bundled template to `~/.config/cyborg/`. To see where cyborg
is looking for config and which directory is active:

```bash
cyborg config
```

**2. Edit `~/.config/cyborg/config.ini`** to define your backup profiles.
Each INI section is a named profile:

```ini
[nas]
destination: /mnt/nas/backups/myhost
source: /home/user, /etc
exclude: exclude

[offsite]
destination: user@host.repo.borgbase.com:repo
source: /home/user, /etc
exclude: exclude-cloud
passphrase: your-passphrase-here
remote_destination: remote:bucket/path
```

| Key | Required | Description |
|-----|----------|-------------|
| `destination` | yes | Path or SSH URL of the Borg repository |
| `source` | yes | Comma-separated list of paths to back up |
| `exclude` | yes | Exclude file — relative paths resolve from config dir |
| `passphrase` | no | Borg repository passphrase |

**3. Initialize the Borg repository:**

```bash
cyborg nas extras
```

Copy and run the `borg init` command shown in the output.

## Usage

```
cyborg NAME COMMAND [OPTIONS]
```

| Command | Description |
|---------|-------------|
| `cyborg NAME run` | Run backup and prune |
| `cyborg NAME run --dry-run` | Simulate without writing |
| `cyborg NAME prune` | Prune old archives only |
| `cyborg NAME prune --dry-run` | Simulate prune |
| `cyborg NAME status` | List archives and show useful commands |
| `cyborg NAME extras` | Print copy-pasteable borg commands |
| `cyborg config` | Show config dir info |
| `cyborg config copy` | Install default config to `~/.config/cyborg/` |

## Exclude Files

The config dir contains exclude files referenced by name in `config.ini`.
Patterns follow [Borg's exclude syntax](https://borgbackup.readthedocs.io/en/stable/usage/help.html).

The bundled defaults include `exclude` (for local backups) and `exclude-cloud`
(a more aggressive list that also excludes large media directories). Add your
own or create additional ones per profile.

## Automation with Cron

```cron
# Run backup every two hours
0  8,10,12,14,16,18  *  *  *  cyborg nas run >> ~/.config/cyborg/nas.log

# Run remote offsite backup once a day
30 8  *  *  *  cyborg offsite run --remote >> ~/.config/cyborg/offsite.log
```

## Archive Naming

Archives are named: `{hostname}__{YYYY-MM-DD}__{HH-MM}`

## Retention Policy

Each `run` automatically prunes the repository with:

- All archives within the last 2 days
- 14 daily archives
- 4 weekly archives
- 6 monthly archives
- 1 yearly archive

## Error Handling

On fatal errors, cyborg logs to the terminal and creates a file in `~/`
named `CYBORG-ERROR--{timestamp}--{!!!...}` so cron jobs leave a visible
indicator even without a notification daemon.
