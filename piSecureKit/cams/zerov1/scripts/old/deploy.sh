#!/usr/bin/env bash
set -euo pipefail


# Clone repo and set ownership
echo "[deploy] cloning/updating PyGation repository"
if [ -d "/opt/PyGation" ]; then
    echo "[deploy] repository exists, pulling latest changes"
    cd /opt/PyGation && sudo git pull
else
    echo "[deploy] cloning repository"
    sudo git clone https://github.com/dez011/PyGation.git /opt/PyGation
fi

# Install dependencies first
echo "[deploy] installing dependencies..."
cd /opt/PyGation/piSecureKit/cams/zerov1/scripts
python3 install_deps.py

#echo "[deploy] setting ownership to miguelh"
#sudo chown -R miguelh:miguelh /opt/PyGation

INSTALL_SCRIPT="/opt/PyGation/piSecureKit/cams/zerov1/scripts/install_zerov1_unit.sh"

echo "[deploy] making install script executable"
chmod +x "$INSTALL_SCRIPT"

echo "[deploy] running install script"
"$INSTALL_SCRIPT"

echo "[deploy] installation complete"
echo "[deploy] following logs (Ctrl+C to exit)..."
echo "----------------------------------------"

# Follow logs in real-time
sudo journalctl -u zerov1 -f

# bash /opt/PyGation/piSecureKit/cams/zerov1/scripts/deploy.sh
