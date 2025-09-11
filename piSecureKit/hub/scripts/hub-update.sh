sudo tee /usr/local/bin/hub-update >/dev/null <<'EOF'
#!/usr/bin/env bash
set -e
git -C /opt/PyGation pull
cd /opt/PyGation/piSecureKit/hub
sudo docker compose pull
sudo docker compose up -d
EOF
sudo chmod +x /usr/local/bin/hub-update
