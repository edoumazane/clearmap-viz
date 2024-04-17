#!/usr/bin/env python3

__author__ = "Etienne Doumazane"
__license__ = "MIT"
__version__ = "0.0.1"
__maintainer__ = "Etienne Doumazane"
__email__ = "etienne.doumazane@icm-institute.org"
__status__ = "Development"

"""
This module contains general purpose utils.
"""


import datetime as dt
import shutil

import os
import pandas as pd
from time import sleep

def show_environment():
    """
    Print info on the device, environment and packages.
    """
    hostname = os.uname().nodename
    username = os.environ["USER"]
    conda_env = os.environ["CONDA_DEFAULT_ENV"]
    timestamp_ok(f"Hostname: {hostname}")
    timestamp_ok(f"Username: {username}")
    timestamp_ok(f"Conda environment: {conda_env}")
    # print the result of conda list
    timestamp_ok("Packages:")
    os.system("conda list")


def show_free_disk_space(path="."):
    """
    Print and return the free disk space in GB.
    """
    free_space_GB = round(shutil.disk_usage(path).free / 1e9, 1)
    timestamp_info(f"Free disk space: {free_space_GB} GB.")
    return free_space_GB

def format_time(timestamp, legal_chars_only=False):
    """
    Format a timestamp to a human readable string.
    timestamp: float timestamp or str (can be "now")

    """
    if timestamp == "now":
        timestamp = dt.datetime.now().timestamp()
    if legal_chars_only:
        return dt.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d_%H-%M-%S')
    return dt.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

#################
#### Logging ####
#################

HEADER = "\033[95m"
BLUE = "\033[94m"
CYAN = "\033[96m"
GREEN = "\033[92m"
ORANGE = "\033[93m"
RED = "\033[91m"
ENDC = "\033[0m"
BOLD = "\033[1m"
UNDERLINE = "\033[4m"

def timestamp_info(text):
    """
    Print a timestamped information.
    """
    print(f"{BOLD}{format_time('now')} [INFO] {text}{ENDC}")

def timestamp_ok(text):
    """
    Print a timestamped information.
    """
    print(f"{BOLD + GREEN}{format_time('now')} [OK] {text}{ENDC}")

def timestamp_warning(text):
    """
    Print a timestamped warning.
    """
    print(f"{BOLD + ORANGE}{format_time('now')} [WARNING] {text}{ENDC}")

def timestamp_error(text):
    """
    Print a timestamped error.
    """
    print(f"{BOLD + RED}{format_time('now')} [ERROR] {text}{ENDC}")