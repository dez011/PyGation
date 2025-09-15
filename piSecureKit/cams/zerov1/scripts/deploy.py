#!/usr/bin/env python3
"""
Installer for the Zero V1 camera unit.

Responsibilities:
- Clone (or pull) the `PyGation` repo into `/opt/PyGation`
- Run dependency installer: `python3 install_deps.py`
- Install the systemd unit (prefer copying zerov1.service; fallback to install_zerov1_unit.sh)
- systemctl daemon-reload, enable, start/restart
- Show status (optional: follow logs with --follow)

Run as a normal user; elevation (sudo) is invoked only where required.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
import getpass
import argparse

REPO_URL   = "https://github.com/dez011/PyGation.git"
REPO_ROOT  = Path("/opt/PyGation")
UNIT_NAME  = "zerov1"

# Project paths
ZEROV1_DIR   = REPO_ROOT / "piSecureKit" / "cams" / "zerov1"
SCRIPTS_DIR  = ZEROV1_DIR / "scripts"
UNIT_SRC     = SCRIPTS_DIR / f"{UNIT_NAME}.service"
UNIT_DST     = Path(f"/etc/systemd/system/{UNIT_NAME}.service")
DEPS_SCRIPT  = SCRIPTS_DIR / "install_deps.py"
FALLBACK_SH  = SCRIPTS_DIR / "install_zerov1_unit.sh"

def run(cmd, check=True, capture=False, cwd=None):
    """Run a shell command with logging, optional capture, and cwd."""
    print(f"[run] {cmd}")
    result = subprocess.run(
        cmd,
        shell=True,
        text=True,
        cwd=str(cwd) if cwd else None,
        capture_output=capture,
    )
    if capture and result.stdout:
        print(result.stdout, end="")
    if capture and result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    if check and result.returncode != 0:
        raise RuntimeError(f"Command failed ({result.returncode}): {cmd}")
    return result.returncode == 0

def ensure_repo():
    """Clone or pull the repo; ensure user owns the working tree."""
    if not REPO_ROOT.exists():
        print(f"[install] cloning repo to {REPO_ROOT}")
        run(f"sudo git clone {REPO_URL} {REPO_ROOT}")
        user = os.environ.get("SUDO_USER") or os.environ.get("USER") or getpass.getuser()
        run(f"sudo chown -R {user}:{user} {REPO_ROOT}")
    elif (REPO_ROOT / ".git").is_dir():
        print("[install] pulling latest changes")
        run("git pull origin master", cwd=REPO_ROOT)
    else:
        raise RuntimeError(f"{REPO_ROOT} exists but is not a git repository")

def validate():
    """Basic validations before install."""
    if not SCRIPTS_DIR.is_dir():
        raise RuntimeError(f"Missing scripts directory: {SCRIPTS_DIR}")
    if not DEPS_SCRIPT.is_file():
        raise RuntimeError(f"Missing dependency installer: {DEPS_SCRIPT}")
    # We can proceed without UNIT_SRC if fallback exists
    if not UNIT_SRC.is_file() and not FALLBACK_SH.is_file():
        raise RuntimeError(f"Neither {UNIT_SRC} nor fallback {FALLBACK_SH} exists.")
    if shutil.which("systemctl") is None:
        raise RuntimeError("systemctl not found")
    if shutil.which("python3") is None:
        raise RuntimeError("python3 not found")

def install_deps(extra_args=None, require_root=True):
    """Run the dependency installer script."""
    script_path = (SCRIPTS_DIR / "install_deps.py").resolve()  # absolute path
    if not script_path.is_file():
        raise RuntimeError(f"Missing dependency installer: {script_path}")

    print("[install] installing dependencies... .. .")

    # only sudo if we need root AND we’re not already root
    need_sudo = bool(require_root and os.geteuid() != 0)

    parts = []
    if need_sudo:
        parts += ["sudo", "-n"]  # remove "-n" if you want interactive password prompts
    parts += ["python3", str(script_path)]
    if extra_args:
        parts += list(extra_args)

    cmd = " " #.join(shlex.quote(p) for p in parts)
    # cmd = " ".join(shlex.quote(p) for p in parts)
    # no cwd needed anymore since we pass an absolute path
    run(cmd)

def install_unit():
    """Prefer copying zerov1.service; otherwise run the fallback installer."""
    if UNIT_SRC.is_file():
        print(f"[install] copying unit -> {UNIT_DST}")
        run(f"sudo install -o root -g root -m 0644 {UNIT_SRC} {UNIT_DST}")
    else:
        print(f"[install] unit file not found; using fallback: {FALLBACK_SH}")
        run(f"chmod +x {FALLBACK_SH}")
        run(f"sudo {FALLBACK_SH}")

def systemd_reload_enable():
    print("[install] systemd daemon-reload")
    run("sudo systemctl daemon-reload")
    print(f"[install] enable {UNIT_NAME} on boot")
    run(f"sudo systemctl enable {UNIT_NAME}")

def start_or_restart():
    active = run(f"systemctl is-active --quiet {UNIT_NAME}", check=False)
    if active:
        print(f"[install] {UNIT_NAME} already active -> restarting")
        run(f"sudo systemctl restart {UNIT_NAME}")
    else:
        print(f"[install] starting {UNIT_NAME}")
        run(f"sudo systemctl start {UNIT_NAME}")

def show_status():
    print(f"[install] status for {UNIT_NAME}:")
    run(f"sudo systemctl --no-pager -l status {UNIT_NAME}", check=False)

def follow_logs():
    print(f"[install] following logs for {UNIT_NAME} (Ctrl+C to exit)")
    print("-" * 40)
    try:
        subprocess.run(f"sudo journalctl -u {UNIT_NAME} -f", shell=True)
    except KeyboardInterrupt:
        print("\n[install] stopped following logs")

def main():
    parser = argparse.ArgumentParser(description="Install/Update zerov1 unit.")
    parser.add_argument("--follow", action="store_true", help="Follow logs after (re)start")
    args = parser.parse_args()

    try:
        ensure_repo()
        validate()
        install_deps()
        install_unit()
        systemd_reload_enable()
        start_or_restart()
        show_status()
        if args.follow:
            follow_logs()
    except Exception as e:
        print(f"ERR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

# to run: python3 install_zerov1_unit.py --follow