#!/usr/bin/env bash
# Called by systemd to run cyborg backups.
# Installed to ~/.config/cyborg/ by cyborg config copy.
#
# Edit PROFILES below to match the section names in your config.ini.
# Multiple profiles run in sequence; comment out any you don't want.

set -euo pipefail

PROFILES=(
    nas
    borgbase
)

CYBORG="$HOME/.local/bin/cyborg"

for profile in "${PROFILES[@]}"; do
    "$CYBORG" run $profile >> "$HOME/.config/cyborg/log-${profile}.log"
done
