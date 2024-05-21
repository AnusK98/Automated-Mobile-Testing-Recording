import json
import os
import subprocess
import random
import time
import sys

# Add the parent directory to the system path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config

def adb_click(x, y, device_id):
    subprocess.run(["adb", "-s", device_id, "shell", "input", "tap", str(x), str(y)])

def start_screen_record(device_id, device_path):
    subprocess.run(["adb", "-s", device_id, "shell", "screenrecord", device_path])

def stop_screen_record(device_id):
    subprocess.run(["adb", "-s", device_id, "shell", "pkill", "-2", "screenrecord"])

def pull_screen_record(device_id, device_path, destination_path):
    subprocess.run(["adb", "-s", device_id, "pull", device_path, destination_path])
    subprocess.run(["adb", "-s", device_id, "shell", "rm", device_path])

def adb_restart_app(device_id, app_name):
    adb_close_app(device_id, app_name)
    adb_launch_app(device_id, app_name)

def adb_close_app(device_id, app_name):
    subprocess.run(f"adb -s {device_id} shell am force-stop {app_name}", shell=True)
    time.sleep(2)

def adb_launch_app(device_id, app_name):
    subprocess.run(f"adb -s {device_id} shell monkey -p {app_name} -c android.intent.category.LAUNCHER 1", shell=True)
    time.sleep(2)

def take_screencap(adb_id, image_path):
    assert(adb_id), "ADB ID cannot be empty"
    assert(image_path), "Image path cannot be empty"
    try:
        screencap_command = ['adb', '-s', adb_id, 'shell', 'screencap', '-p', image_path]
        subprocess.run(screencap_command)
    except Exception as e:
        print(f"An error occurred: {e}")

def pull_file(adb_id, file_path, destination_path):
    assert(adb_id), "ADB ID cannot be empty"
    assert(file_path), "File path cannot be empty"
    assert(destination_path), "Destination path cannot be empty"
    try:
        pull_command = ['adb', '-s', adb_id, 'pull', file_path, destination_path]
        subprocess.run(pull_command)
    except Exception as e:
        print(f"An error occurred: {e}")

def delete_file(adb_id, file_path):
    assert(adb_id), "ADB ID cannot be empty"
    assert(file_path), "File path cannot be empty"
    try:
        delete_command = ['adb', '-s', adb_id, 'shell', 'rm', file_path]
        subprocess.run(delete_command)
    except Exception as e:
        print(f"An error occurred: {e}")

def take_screenshot_and_pull(adb_id, source_path, destination_path):
    assert(adb_id), "ADB ID cannot be empty"
    assert(source_path), "Source path cannot be empty"
    assert(destination_path), "Destination path cannot be empty"
    # print(f"Taking screenshot from {adb_id} {source_path} and saving to {destination_path}")
    try:
        take_screencap(adb_id, source_path)
        pull_file(adb_id, source_path, destination_path)
        delete_file(adb_id, source_path)
    except Exception as e:
        print(f"An error occurred: {e}")
    
def get_adb_id(avd_name):
    assert(avd_name), "AVD name cannot be empty"
    adb_id = None
    
    for id in config.Emulator_IDs:
        try:
            command = f'adb -s {id} shell getprop | grep avd'
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            if avd_name in result.stdout:
                adb_id = id
                break
        except Exception as e:
            print(f"An error occurred: {e}")
            continue
    assert(adb_id), f"Could not find the adb id for the AVD: {avd_name}"
    return adb_id

if __name__ == "__main__":
    action = {
        "type": "click",
        "id": 2
    }
    