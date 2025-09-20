#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="/opt/PyGation"
HUB_DIR="$REPO_ROOT/piSecureKit/hub"
PROJECT_NAME="hub"                     # docker compose project name

echo "[deploy] cd $HUB_DIR"
cd "$HUB_DIR"

# ensure git is happy even when invoked by root/systemd
git config --global --add safe.directory "$REPO_ROOT" || true

echo "[deploy] fetch + fast-forward pull..."
git -C "$REPO_ROOT" fetch --prune
git -C "$REPO_ROOT" pull --ff-only

echo "[deploy] pull images if updated..."
COMPOSE_PROJECT_NAME="$PROJECT_NAME" docker compose pull

echo "[deploy] recreate only if needed..."
COMPOSE_PROJECT_NAME="$PROJECT_NAME" docker compose up -d

echo "[deploy] prune old images (dangling only)..."
docker image prune -f

echo "[deploy] done."


#sudo chmod +x /opt/PyGation/piSecureKit/hub/scripts/Z_doesnt-work-deploy.sh
#sudo /opt/PyGation/piSecureKit/hub/scripts/Z_doesnt-work-deploy.sh