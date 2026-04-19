#!/usr/bin/env bash
#
# Install cyborg systemd user units.
#
# Run this script once after `cyborg config copy`:
#
#   bash ~/.config/cyborg/systemd-install.bash
#
# What it sets up:
#   cyborg-backup.timer   — runs on boot, every 2 hours, and immediately after
#                           wake if a scheduled run was missed while sleeping
#   cyborg-backup.service — the backup unit called by the timer
#   cyborg-hooks.service  — runs before the system sleeps or shuts down

set -euo pipefail

UNIT_DIR="$HOME/.config/systemd/user"
CONFIG_DIR="$HOME/.config/cyborg"
BACKUP_SCRIPT="$CONFIG_DIR/systemd-backup.bash"

mkdir -p "$UNIT_DIR"

# Make sure the backup script is executable.
chmod +x "$BACKUP_SCRIPT"

# ---------------------------------------------------------------------------
# cyborg-backup.service
# ---------------------------------------------------------------------------
cat > "$UNIT_DIR/cyborg-backup.service" << 'EOF'
[Unit]
Description=Cyborg backup
After=network-online.target

[Service]
Type=oneshot
ExecStart=%h/.config/cyborg/systemd-backup.bash
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
cat > "$UNIT_DIR/cyborg-hooks.service" << 'EOF'
[Unit]
Description=Cyborg backup before sleep or shutdown
DefaultDependencies=no
Before=sleep.target shutdown.target

[Service]
Type=oneshot
ExecStart=%h/.config/cyborg/systemd-backup.bash
TimeoutStartSec=5min
RemainAfterExit=yes

[Install]
WantedBy=sleep.target shutdown.target
EOF

# ---------------------------------------------------------------------------
# Enable and start
# ---------------------------------------------------------------------------
systemctl --user daemon-reload

systemctl --user enable --now cyborg-backup.timer
systemctl --user enable cyborg-hooks.service

echo ""
echo "Installed:"
echo "  $UNIT_DIR/cyborg-backup.service"
echo "  $UNIT_DIR/cyborg-backup.timer"
echo "  $UNIT_DIR/cyborg-hooks.service"
echo ""
echo "Timer status:"
systemctl --user list-timers cyborg-backup.timer
