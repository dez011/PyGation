#!/usr/bin/env python3
"""
Dry run deployment - shows what would happen without executing
"""
import os
import shutil
from unittest.mock import patch

def mock_run_command(command, cwd=None):
    """Mock command that prints what would be executed"""
    cwd_info = f" (in {cwd})" if cwd else ""
    print(f"[DRY RUN] Would execute: {command}{cwd_info}")

def dry_run_deploy():
    """Run deployment in dry-run mode"""
    print("=== DRY RUN DEPLOYMENT ===")

    # Patch all subprocess calls
    with patch('deploy.run_command', side_effect=mock_run_command):
        with patch('install_deps.run_command', side_effect=mock_run_command):
            with patch('install_zerov1_unit.run_command', side_effect=mock_run_command):
                with patch('os.path.exists', return_value=True):
                    with patch('shutil.copy2') as mock_copy:
                        mock_copy.side_effect = lambda src, dst: print(f"[DRY RUN] Would copy {src} to {dst}")

                        from deploy import main as deploy_main

                        try:
                            deploy_main()
                        except KeyboardInterrupt:
                            print("[DRY RUN] Would follow logs...")

if __name__ == "__main__":
    dry_run_deploy()