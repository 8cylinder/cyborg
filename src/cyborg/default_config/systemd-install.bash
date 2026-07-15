#!/usr/bin/env bash
#
# Install cyborg systemd system units (requires root).
#
# Run this script once after `cyborg config copy`:
#
#   sudo bash ~/.config/cyborg/systemd-install.bash
#
# What it sets up:
#   cyborg-backup.timer   — runs on boot, every 2 hours, and immediately after
#                           wake if a scheduled run was missed while sleeping
#   cyborg-backup.service — the backup unit called by the timer
#   cyborg-hooks.service  — runs before the system sleeps or shuts down

set -euo pipefail

# ---------------------------------------------------------------------------
# Must run as root
# ---------------------------------------------------------------------------
if [[ $EUID -ne 0 ]]; then
    echo "Error: this script must be run as root (use sudo)." >&2
    exit 1
fi

# Resolve the target user: prefer SUDO_USER, fall back to asking.
if [[ -n "${SUDO_USER:-}" ]]; then
    TARGET_USER="$SUDO_USER"
else
    read -rp "Install for which user? " TARGET_USER
fi

TARGET_HOME=$(getent passwd "$TARGET_USER" | cut -d: -f6)
TARGET_UID=$(id -u "$TARGET_USER")

if [[ -z "$TARGET_HOME" ]]; then
    echo "Error: could not determine home directory for '$TARGET_USER'." >&2
    exit 1
fi

UNIT_DIR="/etc/systemd/system"
BACKUP_SCRIPT="$TARGET_HOME/.config/cyborg/systemd-backup.bash"

if [[ ! -f "$BACKUP_SCRIPT" ]]; then
    echo "Error: backup script not found: $BACKUP_SCRIPT" >&2
    echo "Run 'cyborg config copy' as $TARGET_USER first." >&2
    exit 1
fi

chmod +x "$BACKUP_SCRIPT"

# echo $TARGET_USER
# echo $TARGET_UID
# echo $TARGET_HOME
# echo $BACKUP_SCRIPT
# echo $UNIT_DIR
# exit

# ---------------------------------------------------------------------------
# cyborg-backup.service
# ---------------------------------------------------------------------------
cat > "$UNIT_DIR/cyborg-backup.service" << EOF
[Unit]
Description=Cyborg backup
After=network-online.target

[Service]
Type=oneshot
User=$TARGET_USER
Environment=HOME=$TARGET_HOME
Environment=XDG_RUNTIME_DIR=/run/user/$TARGET_UID
ExecStart=$BACKUP_SCRIPT
EOF

# ---------------------------------------------------------------------------
# cyborg-backup.timer
# ---------------------------------------------------------------------------
# Persistent=true: if a scheduled run was missed while the machine was
# off or sleeping, systemd fires the timer immediately on next boot/wake.
cat > "$UNIT_DIR/cyborg-backup.timer" << 'EOF'
[Unit]
Description=Cyborg backup timer

[Timer]
OnBootSec=2min
OnUnitActiveSec=2h
Persistent=true
Unit=cyborg-backup.service

[Install]
WantedBy=timers.target
EOF

# ---------------------------------------------------------------------------
# cyborg-hooks.service  (pre-sleep and pre-shutdown)
# ---------------------------------------------------------------------------
cat > "$UNIT_DIR/cyborg-hooks.service" << EOF
[Unit]
Description=Cyborg backup before sleep or shutdown
DefaultDependencies=no
Before=sleep.target shutdown.target reboot.target

[Service]
Type=oneshot
User=$TARGET_USER
Environment=HOME=$TARGET_HOME
Environment=XDG_RUNTIME_DIR=/run/user/$TARGET_UID
ExecStart=$BACKUP_SCRIPT
TimeoutStartSec=5min
RemainAfterExit=yes

[Install]
WantedBy=sleep.target shutdown.target
EOF

# ---------------------------------------------------------------------------
# Enable and start
# ---------------------------------------------------------------------------
systemctl daemon-reload

systemctl enable --now cyborg-backup.timer
systemctl enable cyborg-hooks.service

echo ""
echo "Installed for user: $TARGET_USER"
echo "  $UNIT_DIR/cyborg-backup.service"
echo "  $UNIT_DIR/cyborg-backup.timer"
echo "  $UNIT_DIR/cyborg-hooks.service"
echo ""
echo "Timer status:"
systemctl list-timers cyborg-backup.timer
