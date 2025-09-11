#!/usr/bin/env bash
set -euo pipefail

# --- config (edit if your paths differ) ---
REPO_ROOT="/opt/PyGation"
HUB_DIR="$REPO_ROOT/piSecureKit/hub"
SCRIPTS_DIR="$HUB_DIR/scripts"
UNIT_SRC="$SCRIPTS_DIR/hub.service"
UNIT_DST="/etc/systemd/system/hub.service"
DEPLOY="$SCRIPTS_DIR/deploy.sh"

# --- sanity checks ---
if [[ ! -d "$HUB_DIR" ]]; then
  echo "ERR: HUB_DIR not found: $HUB_DIR"
  exit 1
fi
if [[ ! -f "$UNIT_SRC" ]]; then
  echo "ERR: hub.service not found at $UNIT_SRC"
  exit 1
fi
if ! command -v docker >/dev/null 2>&1; then
  echo "ERR: docker not installed or not in PATH"
  exit 1
fi

# --- permissions ---
echo "[bootstrap] chmod +x deploy.sh"
sudo chmod +x "$DEPLOY"

# --- install systemd unit ---
echo "[bootstrap] install hub.service -> $UNIT_DST"
# use 'install' to set correct owner/perm in one go
sudo install -o root -g root -m 0644 "$UNIT_SRC" "$UNIT_DST"

echo "[bootstrap] systemctl daemon-reload"
sudo systemctl daemon-reload

# --- enable & start ---
echo "[bootstrap] enable hub (start on boot)"
sudo systemctl enable hub

# If the service is already active, do a reload (runs deploy).
# If not active yet, start it (ExecStart: docker compose up -d), then reload to pull latest repo/images.
if systemctl is-active --quiet hub; then
  echo "[bootstrap] hub is active -> reload (runs deploy.sh)"
  sudo systemctl reload hub
else
  echo "[bootstrap] starting hub"
  sudo systemctl start hub
  echo "[bootstrap] reload once to ensure latest repo/images"
  sudo systemctl reload hub
fi

echo "[bootstrap] status:"
sudo systemctl --no-pager -l status hub || true

echo "[bootstrap] done."


#sudo chmod +x /opt/PyGation/piSecureKit/hub/scripts/bootstrap_hub.sh
#sudo /opt/PyGation/piSecureKit/hub/scripts/bootstrap_hub.sh
#sudo systemctl reload hub