import subprocess
import json
import os
import sys


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.adb_command import get_adb_id
import config

def get_all_packages(emulator_name, android_app=True):
    # Get a list of all installed packages
    result = subprocess.run(['adb', '-s', emulator_name, 'shell', 'pm', 'list', 'packages'], stdout=subprocess.PIPE)
    packages = result.stdout.decode().strip().splitlines()
    # Remove packages that are prefix with com.android and com.google
    if not android_app:
        packages = [line for line in packages if not line.startswith("package:com.android") and not line.startswith("package:com.google")]
    
    # Extract package names from the package list
    packages = [line.split(":")[1] for line in packages]
    return packages

def get_emulator_id(device_id):
    command = f"adb -s {device_id} shell getprop | grep avd"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout.strip().split(":")[1][2:-1]

def check_launchable_apps(packages, emulator_name):
    launchable_apps = []
    
    for package_name in packages:
        # Construct the monkey command
        command = f"adb -s {emulator_name} shell monkey -p {package_name} -c android.intent.category.LAUNCHER 1"
        
        # Execute the command
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output = result.stdout.decode().strip()
        
        # Check if monkey was aborted due to no activities
        if "** No activities found to run, monkey aborted." not in output:
            print(f"Launchable app found: {package_name}")
            launchable_apps.append(package_name)
        
        # Turn off the app
        subprocess.run(['adb', '-s', emulator_name, 'shell', 'am', 'force-stop', package_name])
    
    return launchable_apps

def read_json(filepath):
    try:
        with open(filepath, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def write_json(filepath, data):
    with open(filepath, "w") as file:
        json.dump(data, file, indent=4)

def get_device_apps(AVD_NAME):
    adb_id = get_adb_id(AVD_NAME)
    all_packages = get_all_packages(adb_id, True)
    launchable_apps = check_launchable_apps(all_packages, adb_id)

    with open(os.path.join(config.DATA_FOLDER, f"{AVD_NAME}_apps.json"), "w") as file:
        json.dump({AVD_NAME:launchable_apps}, file, indent=4)

    return launchable_apps

def read_device_apps(AVD_NAME):
    with open(os.path.join(config.DATA_FOLDER, f"{AVD_NAME}_apps.json"), "r") as file:
        return json.load(file)[AVD_NAME]

if __name__ == "__main__":
    AVD_NAME = "Medium_Phone_API_31"
    get_device_apps(AVD_NAME)
