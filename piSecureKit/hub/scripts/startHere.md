#this does not work yet. SKIP
sudo git clone https://github.com/dez011/PyGation.git /opt/PyGation \
  && sudo chown -R "$USER":"$USER" /opt/PyGation \
  && sleep 2 \
  && chmod +x /opt/PyGation/piSecureKit/hub/scripts/deploy.sh \
  && chmod +x /opt/PyGation/piSecureKit/hub/scripts/bootstrap_hub.sh \
  && sleep 2 \
  && sudo /opt/PyGation/piSecureKit/hub/scripts/bootstrap_hub.sh






##REMOVING OLD INSTALL
The above does not work yet you will have to manually do this:
# 1) Stop & remove the hub systemd unit if it exists
sudo systemctl stop hub 2>/dev/null || true
sudo systemctl disable hub 2>/dev/null || true
sudo rm -f /etc/systemd/system/hub.service
sudo systemctl daemon-reload

# 2) Stop/remove any running mediamtx from the old /hub
[ -d /hub ] && (cd /hub && docker compose down) || true

# 3) Remove previous repo clone
sudo rm -rf /opt/PyGation


##IF FRESH INSTALL GO HERE
Fresh install clone+permissions
sudo git clone https://github.com/dez011/PyGation.git /opt/PyGation \
  && sudo chown -R "$USER":"$USER" /opt/PyGation

cd /opt/PyGation/piSecureKit/hub

#to run the install script and copy/run the system service
#sudo chmod +x /opt/PyGation/piSecureKit/hub/scripts/install_hub_unit.sh && /opt/PyGation/piSecureKit/hub/scripts/install_hub_unit.sh


update and restart docker
git -C /opt/PyGation pull \
  && cd /opt/PyGation/piSecureKit/hub \
  && sudo docker compose pull \
  && sudo docker compose up -d
