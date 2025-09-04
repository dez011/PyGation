
to pull and restart piSecure service
git -C /opt/PyGation pull && sudo systemctl daemon-reload && sudo systemctl restart piSecure && systemctl status --no-pager -l piSecure

Service file (/etc/systemd/system/piSecure.service):
'''
# 1) Make sure your user owns the repo
sudo chown -R miguelh:miguelh /opt/PyGation

# 2) Replace the service to run as *your* user and pull before start
sudo tee /etc/systemd/system/piSecure.service >/dev/null <<'EOF'
[Unit]
Description=piSecure Main App
After=network-online.target
Wants=network-online.target

[Service]
User=miguelh
WorkingDirectory=/opt/PyGation/piSecureKit
# Pull latest on each (re)start; safe for a public repo
ExecStartPre=/usr/bin/git -C /opt/PyGation pull
# If you use a venv, prepend its Python path in Environment=PATH
ExecStart=/usr/bin/python3 /opt/PyGation/piSecureKit/main.py
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# 3) Reload units and start
sudo systemctl daemon-reload
sudo systemctl enable piSecure
sudo systemctl restart piSecure

# 4) Watch logs if anything flops
journalctl -u piSecure -f

'''

# piSecureKit commands after creating service
sudo systemctl daemon-reload #if changes to service file
sudo systemctl enable piSecure
sudo systemctl start piSecure


# logs
tail -f /opt/PyGation/piSecure.log

