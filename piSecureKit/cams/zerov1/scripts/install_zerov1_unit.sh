#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="/opt/PyGation"
ZEROV1_DIR="$REPO_ROOT/piSecureKit/cams/zerov1"
UNIT_SRC="$ZEROV1_DIR/scripts/zerov1.service"
UNIT_DST="/etc/systemd/system/zerov1.service"

# sanity checks
[ -f "$UNIT_SRC" ] || { echo "ERR: missing $UNIT_SRC"; exit 1; }
[ -f "$ZEROV1_DIR/main.py" ] || { echo "ERR: missing main.py"; exit 1; }
command -v python3 >/dev/null || { echo "ERR: python3 not found"; exit 1; }

echo "[install] copying unit -> $UNIT_DST"
sudo install -o root -g root -m 0644 "$UNIT_SRC" "$UNIT_DST"

echo "[install] daemon-reload"
sudo systemctl daemon-reload

echo "[install] enable on boot"
sudo systemctl enable zerov1

if systemctl is-active --quiet zerov1; then
  echo "[install] zerov1 already active -> restarting"
  sudo systemctl restart zerov1
else
  echo "[install] starting zerov1"
  sudo systemctl start zerov1
fi

# sudo journalctl -u zerov1 -f
# StandardOutput=append:/var/log/zerov1.log
# StandardError=append:/var/log/zerov1.log
# make executable: chmod +x /opt/PyGation/piSecureKit/cams/zerov1/scripts/install_zerov1_unit.sh
# run: /opt/PyGation/piSecureKit/cams/zerov1/scripts/install_zerov1_unit.sh
