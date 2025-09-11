sudo git clone https://github.com/dez011/PyGation.git /opt/PyGation \
  && sudo chown -R "$USER":"$USER" /opt/PyGation \
  && sleep 2 \
  && chmod +x /opt/PyGation/piSecureKit/hub/scripts/deploy.sh \
  && chmod +x /opt/PyGation/piSecureKit/hub/scripts/bootstrap_hub.sh \
  && sleep 2 \
  && sudo /opt/PyGation/piSecureKit/hub/scripts/bootstrap_hub.sh
