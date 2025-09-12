#!/usr/bin/env python3
import os
import subprocess
import sys

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
    print("[deploy] cloning/updating PyGation repository")

    # Clone or update repository
    if os.path.exists("/opt/PyGation"):
        print("[deploy] repository exists, pulling latest changes")
        run_command("sudo git pull", cwd="/opt/PyGation")
    else:
        print("[deploy] cloning repository")
        run_command("sudo git clone https://github.com/dez011/PyGation.git /opt/PyGation")

    # Install dependencies
    print("[deploy] installing dependencies... .. .")
    scripts_dir = "/opt/PyGation/piSecureKit/cams/zerov1/scripts"
    run_command("python3 install_deps.py", cwd=scripts_dir)

    # Make install script executable and run it
    install_script = "/opt/PyGation/piSecureKit/cams/zerov1/scripts/install_zerov1_unit.sh"
    print("[deploy] making install script executable")
    run_command(f"chmod +x {install_script}")

    print("[deploy] running install script")
    run_command(f'"{install_script}"')

    print("[deploy] installation complete")
    print("[deploy] following logs (Ctrl+C to exit)...")
    print("-" * 40)

    # Follow logs in real-time
    try:
        subprocess.run("sudo journalctl -u zerov1 -f", shell=True)
    except KeyboardInterrupt:
        print("\n[deploy] Stopped following logs")


# python3 /opt/PyGation/piSecureKit/cams/zerov1/scripts/deploy.py