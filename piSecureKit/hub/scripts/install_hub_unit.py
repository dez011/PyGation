# python
"""
Replacement for the former shell script `Z_DEPRECATED_install_hub_unit.sh`.

This Python script fully supersedes the old installer.
Responsibilities:
- Clone (or pull) the `PyGation` repo into `/opt/PyGation`
- Copy `hub.service` into `/etc/systemd/system/hub.service`
- Run `systemctl daemon-reload`
- Enable the `hub` service
- Start or restart the service
- Show status

Run as a normal user (do not prefix with sudo); elevation is used only where required.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
import getpass

REPO_ROOT = Path("/opt/PyGation")
HUB_DIR = REPO_ROOT / "piSecureKit" / "hub"
UNIT_SRC = HUB_DIR / "scripts" / "hub.service"
UNIT_DST = Path("/etc/systemd/system/hub.service")
REPO_URL = "https://github.com/dez011/PyGation.git"

def run(cmd, check=True, capture=False, cwd=None):
    """Run a shell command with optional cwd."""
    print(f"[run: cmd] {cmd}")
    result = subprocess.run(
        cmd,
        shell=True,
        cwd=cwd,
        text=True,
        capture_output=capture
    )
    if capture and result.stdout:
        print(result.stdout, end="")
    if capture and result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    if check and result.returncode != 0:
        raise RuntimeError(f"Command failed ({result.returncode}): {cmd}")
    return (result.returncode == 0, (result.stdout.strip() if capture else ""))

def ensure_repo():
    if not REPO_ROOT.exists():
        print(f"[install] cloning repo to {REPO_ROOT}")
        run(f"sudo git clone {REPO_URL} {REPO_ROOT}")
        user = os.environ.get("SUDO_USER") or os.environ.get("USER") or getpass.getuser()
        run(f"sudo chown -R {user}:{user} {REPO_ROOT}")
    elif (REPO_ROOT / ".git").is_dir():
        print("[install] pulling latest changes")
        run("git pull origin master", cwd=str(REPO_ROOT))
    else:
        print(f"ERR: {REPO_ROOT} exists but is not a git repo")
        sys.exit(1)

def validate():
    if not UNIT_SRC.is_file():
        print(f"ERR: missing {UNIT_SRC}")
        sys.exit(1)
    if shutil.which("docker") is None:
        print("ERR: docker not found")
        sys.exit(1)

def install_unit():
    print(f"[install] copying unit -> {UNIT_DST}")
    run(f"sudo install -o root -g root -m 0644 {UNIT_SRC} {UNIT_DST}")

def systemd_reload_enable():
    print("[install] daemon-reload")
    run("sudo systemctl daemon-reload")
    print("[install] enable on boot")
    run("sudo systemctl enable hub")

def start_or_restart():
    active, _ = run("systemctl is-active --quiet hub", check=False)
    if active:
        print("[install] hub already active -> restarting")
        run("sudo systemctl restart hub")
    else:
        print("[install] starting hub")
        run("sudo systemctl start hub")

def show_status():
    print("[install] status:")
    run("sudo systemctl --no-pager -l status hub", check=False)

def main():
    try:
        ensure_repo()
        validate()
        install_unit()
        systemd_reload_enable()
        start_or_restart()
        show_status()
    except Exception as e:
        print(f"ERR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

# python3 scripts/install_hub_unit.py