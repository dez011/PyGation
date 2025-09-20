#!/usr/bin/env python3
import unittest
import tempfile
import os
import sys
import subprocess
import shutil
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add the scripts directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import your modules
from install_deps import run_command as deps_run_command
from deploy import run_command as deploy_run_command
from install_zerov1_unit import run_command as install_run_command

class TestDeploymentScripts(unittest.TestCase):

    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()

    def tearDown(self):
        """Clean up test environment"""