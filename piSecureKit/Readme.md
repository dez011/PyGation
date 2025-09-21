sudo git clone https://github.com/dez011/PyGation.git /opt/PyGation
sudo chown -R "$USER":"$USER" /opt/PyGation


sudo python3 piSecureKit/cams/zerov1/scripts/install_deps.py --p7zip --ffmpeg --python --camera --openblas --pip picamera2 Flask Flask-RESTful Pillow watchdog bcrypt
 
 $ sudo nano /boot/firmware/config.txt
Add your required tags to enable your camera. The CM4-Nano-C requires what's below. If you only need to enable camera autodetect, then disregard this step. If you need to add other code instead of what's required for the CM4-Nano-C, then replace your code where the CM4-Nano-C code should go.

camera_auto_detect=0
Place this under [all]
dtoverlay=imx219,cam0
Then do

_#updated run: python3 scripts/deploy.py_

# 1) Install the modern camera stack
sudo apt update
sudo apt install -y rpicam-apps python3-picamera2 v4l-utils

# 2) (Pi Zero + Cam Module 3) give the ISP memory + steady clocks
#   (skip if you already set CMA; harmless if duplicated)
sudo sed -i 's/\bcma=\S*/cma=192M/' /boot/firmware/cmdline.txt || \
  sudo sed -i 's/$/ cma=192M/' /boot/firmware/cmdline.txt
echo 'core_freq_min=250' | sudo tee -a /boot/firmware/config.txt

# 3) (If you’re using Cam Module 3 / IMX708) force the overlay
#    change to ov5647 (V1), imx219 (V2), imx477 (HQ) if that’s your sensor
echo 'dtoverlay=imx708' | sudo tee -a /boot/firmware/config.txt

# 4) Reboot to load everything
sudo reboot

# Should exist now; this is the new name
rpicam-hello --list-cameras
rpicam-hello -t 2000


sudo reboot





sudo LIBCAMERA_LOG_LEVELS=*:DEBUG \
rpicam-vid -t 0 -n --width 1280 --height 720 --framerate 30 \
  --bitrate 2000000 --intra 60 --profile baseline --inline \
  -o /dev/null |& tee /tmp/cam.log

tail -n 60 /tmp/cam.log





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


#deps
sudo apt update
sudo apt install -y python3-flask python3-picamera2 libcamera-apps
sudo apt install python3-flask-restful

#Example https://github.com/IcyG1045/CM4Cam/blob/main/camserver/camserver.py

#view in browser
http://192.168.6.76:8889/hqstream/ #or pi5.local:8889/hqstream/