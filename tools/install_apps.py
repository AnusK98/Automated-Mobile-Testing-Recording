import subprocess
import re
import time
import os
import json
import sys

# Add the parent directory to the system path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from tools.adb_command import get_adb_id

Android_SDK_Path = config.Android_SDK_Path
apps_directory = config.Apps_directory  # Directory containing the APK files

def install_apps_on_emulator(emulator_id):
    avd_id = get_adb_id(emulator_id)
    emulator_app_map = {}
    # Gather all APK files from the apps directory
    apk_files = [os.path.join(apps_directory, f) for f in os.listdir(apps_directory) if f.endswith('.apk')]
    apk_files.sort()  # Ensure consistency in file ordering

    for apk in apk_files:
        subprocess.run(['adb', '-s', avd_id, 'install', apk])
        print(f"Installed {apk} on {avd_id}")
        
        # Save the mapping of emulator to apps
    emulator_app_map[emulator_id] = [os.path.basename(apk) for apk in apk_files]

    print("App installations complete and mapping saved.")