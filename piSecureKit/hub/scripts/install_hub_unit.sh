#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="/opt/PyGation"
HUB_DIR="$REPO_ROOT/piSecureKit/hub"
UNIT_SRC="$HUB_DIR/scripts/hub.service"
UNIT_DST="/etc/systemd/system/hub.service"

# sanity checks
[ -f "$UNIT_SRC" ] || { echo "ERR: missing $UNIT_SRC"; exit 1; }
command -v docker >/dev/null || { echo "ERR: docker not found"; exit 1; }

echo "[install] copying unit -> $UNIT_DST"
sudo install -o root -g root -m 0644 "$UNIT_SRC" "$UNIT_DST"

echo "[install] daemon-reload"
sudo systemctl daemon-reload

echo "[install] enable on boot"
sudo systemctl enable hub

if systemctl is-active --quiet hub; then
  echo "[install] hub already active -> restarting"
  sudo systemctl restart hub
else
  echo "[install] starting hub"
  sudo systemctl start hub
fi

echo "[install] status:"
sudo systemctl --no-pager -l status hub || true

#sudo chmod +x /opt/PyGation/piSecureKit/hub/scripts/install_hub_unit.sh && /opt/PyGation/piSecureKit/hub/scripts/install_hub_unit.sh