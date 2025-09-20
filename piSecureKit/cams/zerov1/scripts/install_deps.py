#!/usr/bin/env python3
import argparse, os, shutil, subprocess, sys, time

STAMP = "/var/lib/pisecure/setup.stamp"
LOG   = "/var/log/pisecure-setup.log"

def log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[setup] {ts} {msg}"
    print(line, flush=True)
    try:
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        with open(LOG, "a") as f: f.write(line + "\n")
    except Exception:
        pass

def run(cmd, cwd=None):
    log(f"$ {cmd}")
    subprocess.run(cmd, shell=True, check=True, cwd=cwd)

def ensure_root():
    if os.geteuid() != 0:
        sys.exit("Please run with sudo/root: sudo python3 /usr/local/sbin/pisecure_setup.py ...")

def dpkg_missing(pkgs):
    missing = []
    for p in pkgs:
        r = subprocess.run(["dpkg", "-s", p], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if r.returncode != 0:
            missing.append(p)
    return missing

def apt_install(pkgs):
    pkgs = dpkg_missing(pkgs)
    if not pkgs:
        log("apt: all requested packages already installed; skipping")
        return
    run("apt-get update -y")
    run("apt-get install -y " + " ".join(pkgs))

def pip_install(pkgs):
    if not pkgs: return
    # --break-system-packages keeps Debian/Bookworm happy
    run("python3 -m pip install --upgrade pip")
    run("python3 -m pip install --break-system-packages " + " ".join(pkgs))

def swap_imx219():
    vc4 = "/usr/share/libcamera/ipa/rpi/vc4"
    a = os.path.join(vc4, "imx219.json")
    b = os.path.join(vc4, "imx219_noir.json")
    if not (os.path.isdir(vc4) and os.path.isfile(a) and os.path.isfile(b)):
        log("IMX219 swap: files not found; skipping")
        return
    for f in (a, b):
        bak = f + ".bak"
        if not os.path.exists(bak):
            shutil.copy2(f, bak)
    ir = os.path.join(vc4, "imx219_ir.json")
    if os.path.exists(ir): os.remove(ir)
    shutil.move(a, ir)     # imx219.json -> imx219_ir.json
    shutil.move(b, a)      # imx219_noir.json -> imx219.json
    log("IMX219 swap: completed (backups *.bak kept)")

def main():
    parser = argparse.ArgumentParser(description="PiSecure one-shot setup (Python). Choose only the steps you want.")
    parser.add_argument("--once", action="store_true", help="run only once; skip if previously completed")
    parser.add_argument("--p7zip", action="store_true", help="install p7zip-full")
    parser.add_argument("--ffmpeg", action="store_true", help="install ffmpeg")
    parser.add_argument("--python", action="store_true", help="install python3 + pip")
    parser.add_argument("--camera", action="store_true", help="install libcamera tools + python3-picamera2")
    parser.add_argument("--openblas", action="store_true", help="install libopenblas-dev")
    parser.add_argument("--pip", nargs="*", default=[], help="pip3 packages to install (space-separated)")
    parser.add_argument("--rename-imx219", action="store_true", help="swap imx219/imx219_noir JSON")
    parser.add_argument("--reboot", action="store_true", help="reboot after success")
    parser.add_argument("--self-delete", action="store_true", help="remove this script after success")

    args = parser.parse_args()
    ensure_root()

    if args.once and os.path.exists(STAMP):
        with open(STAMP) as f: when = f.read().strip()
        log(f"stamp exists ({when}); --once => nothing to do")
        return

    os.makedirs(os.path.dirname(STAMP), exist_ok=True)
    log("starting")

    # APT in one or two batches max (only missing packages)
    apt_pkgs = []
    if args.p7zip:   apt_pkgs += ["p7zip-full"]
    if args.ffmpeg:  apt_pkgs += ["ffmpeg"]
    if args.python:  apt_pkgs += ["python3", "python3-pip"]
    if args.camera:  apt_pkgs += ["libcamera-apps", "libcamera-tools", "python3-picamera2"]
    if args.openblas:apt_pkgs += ["libopenblas-dev"]
    if apt_pkgs: apt_install(apt_pkgs)

    if args.rename_imx219:
        swap_imx219()

    if args.pip:
        pip_install(args.pip)

    # mark success
    with open(STAMP, "w") as f: f.write(time.strftime("%Y-%m-%d %H:%M:%S"))
    log("done")

    if args.reboot:
        log("rebooting in 3s…")
        time.sleep(3)
        run("reboot")

    if args.self_delete:
        path = os.path.abspath(__file__)
        log(f"self-delete {path}")
        os.remove(path)

if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        log(f"ERROR: {e}")
        sys.exit(e.returncode)
    except Exception as e:
        log(f"ERROR: {e}")
        sys.exit(1)


'''
sudo python3 piSecureKit/cams/zerov1/scripts/install_deps.py --p7zip --ffmpeg --python --camera --openblas --pip picamera2 Flask Flask-RESTful Pillow watchdog bcrypt
'''


# import subprocess
#
#
# def run_command(command):
#     try:
#         subprocess.run(command, check=True, shell=True, text=True)
#     except subprocess.CalledProcessError as e:
#         print(f"An error occurred: {e}")
#
#
# def main():
#     # Install p7zip-full
#     run_command('sudo apt-get install -y p7zip-full')
#
#     # Download and extract CM4_dt_blob.7z
#     run_command('wget https://files.waveshare.com/upload/4/41/CM4_dt_blob.7z')
#     run_command('7z x CM4_dt_blob.7z -O./CM4_dt_blob')
#
#     # Change permissions and navigate into the directory
#     run_command('sudo chmod 777 -R CM4_dt_blob')
#     run_command('cd CM4_dt_blob')
#
#     # Rename JSON files
#     run_command('cd /usr/share/libcamera/ipa/rpi/vc4')
#     run_command('sudo mv imx219.json imx219_ir.json')
#     run_command('sudo mv imx219_noir.json imx219.json')
#
#     # Install additional packages
#     run_command('sudo apt install -y ffmpeg')
#     run_command('sudo apt install -y python3 python3-pip')
#     run_command('sudo apt install -y libcamera-tools')
#     run_command('sudo apt-get install -y libopenblas-dev')
#
#     # Install Python packages individually
#     run_command('pip3 install picamera2')
#     run_command('pip3 install Flask')
#     run_command('pip3 install Flask-RESTful')
#     run_command('pip3 install Pillow')
#     run_command('pip3 install watchdog')
#     run_command('pip3 install bcrypt')
#
#     # Set permissions for specific directories
#     run_command('sudo chmod u+rwx /home/CM4Cam/camserver/static/pictures/')
#     run_command('sudo chmod u+rwx /home/CM4Cam/camserver/static/video/')
#     run_command('sudo chmod -R 777 /home/CM4Cam/camserver/static/pictures/')
#     run_command('sudo chmod -R 777 /home/CM4Cam/camserver/static/video/')
#
#     # Install Flask and camera packages
#     run_command('sudo apt install -y python3-flask python3-picamera2 libcamera-apps')
#     run_command('sudo apt install -y python3-flask-restful')
#
#     # Reboot not sure if i want this here for dev
#     # run_command('sudo reboot')
#
#
# if __name__ == "__main__":
#     main()