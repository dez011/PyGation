#!/usr/bin/env python3
import os
import subprocess
import sys
import shutil

def run_command(command, cwd=None):
    """Run command and handle errors"""
    try:
        result = subprocess.run(command, shell=True, check=True, cwd=cwd, text=True)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}")
        print(f"Exit code: {e.returncode}")
        sys.exit(1)

def main():
    print("[install] Installing zerov1 unit...")

    # Copy service file
    service_src = "/opt/PyGation/piSecureKit/cams/zerov1/zerov1.service"
    service_dst = "/etc/systemd/system/zerov1.service"

    print(f"[install] Copying service file to {service_dst}")
    shutil.copy2(service_src, service_dst)

    # Reload systemd and enable service
    print("[install] Reloading systemd daemon")
    run_command("sudo systemctl daemon-reload")

    print("[install] Enabling zerov1 service")
    run_command("sudo systemctl enable zerov1")

    print("[install] Starting zerov1 service")
    run_command("sudo systemctl start zerov1")

    print("[install] Installation complete!")

if __name__ == "__main__":
    main()