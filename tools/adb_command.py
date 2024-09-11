import json
import os
import subprocess
import random
import time
import sys
import threading

# Add the parent directory to the system path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config

def adb_turnoff(device_id):
    subprocess.run(['adb', '-s', device_id, 'emu', 'kill'])
    time.sleep(10)

def adb_turnon(avd_name):
    emulator_command_base = f"{config.ANDROID_SDK_Path}/emulator/emulator -netdelay none -netspeed full -avd"
    command = f"{emulator_command_base} {avd_name} -dns-server 8.8.8.8 -no-snapshot-load"
    subprocess.Popen(command, shell=True)
    time.sleep(40)

def adb_restart(device_id, avd_name):
    adb_turnoff(device_id)
    adb_turnon(avd_name)

def adb_click(x, y, device_id):
    subprocess.run(["adb", "-s", device_id, "shell", "input", "tap", str(x), str(y)])

def adb_swipe(orientation, device_id):
    if orientation == 'up':
        subprocess.run(["adb", "-s", device_id, "shell", "input", "swipe", "540", "2000", "540", "400"])
    elif orientation == 'down':
        subprocess.run(["adb", "-s", device_id, "shell", "input", "swipe", "540", "400", "540", "2000"])
    elif orientation == 'left':
        subprocess.run(["adb", "-s", device_id, "shell", "input", "swipe", "810", "1200", "270", "1200"])
    elif orientation == 'right':
        subprocess.run(["adb", "-s", device_id, "shell", "input", "swipe", "270", "1200", "810", "1200"])

def start_screen_record(device_id, device_path):
    subprocess.run(["adb", "-s", device_id, "shell", "screenrecord", device_path])

def stop_screen_record(device_id):
    subprocess.run(["adb", "-s", device_id, "shell", "pkill", "-2", "screenrecord"])

def pull_screen_record(device_id, device_path, destination_path):
    subprocess.run(["adb", "-s", device_id, "pull", device_path, destination_path])
    subprocess.run(["adb", "-s", device_id, "shell", "rm", device_path])

def adb_restart_app(AVD, app_name):
    adb_close_app(AVD, app_name)
    adb_launch_app(AVD, app_name)

def adb_close_app(AVD, app_name):
    device_id = get_adb_id(AVD)
    subprocess.run(f"adb -s {device_id} shell am force-stop {app_name}", shell=True)
    time.sleep(2)

def adb_launch_app(AVD, app_name):
    device_id = get_adb_id(AVD)
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
    
    while adb_id == None:
        for id in config.EMULATOR_IDS:
            try:
                command = f'adb -s {id} shell getprop | grep avd'
                result = subprocess.run(command, shell=True, capture_output=True, text=True)
                if avd_name in result.stdout:
                    adb_id = id
                    break
            except Exception as e:
                print(f"An error occurred: {e}")
                continue
        
        if adb_id == None:
            print("AVD not found, retrying in 10 seconds or ctrl+c to exit.")
            time.sleep(10)

    return adb_id

def tap_and_recording(AVD_NAME, bbox, name, video_folder):
    '''
    perform the action on the UI element (you can implement your own logic here)
        input : ui_id (int), components (json)
        output : action_detail (json)
    '''
    
    device_path = f"/sdcard/{name}.mp4"
    target_path = os.path.join(video_folder, f"{name}.mp4")

    x = (bbox['column_min'] + bbox['column_max']) // 2
    y = (bbox['row_min'] + bbox['row_max']) // 2

    adb_id = get_adb_id(AVD_NAME)

    screen_record_thread = threading.Thread(target=start_screen_record, args=(adb_id, device_path))
    screen_record_thread.start()
    time.sleep(0.4)
    adb_click(x, y, adb_id)
    time.sleep(2)
    stop_screen_record(adb_id)
    screen_record_thread.join()
    pull_screen_record(adb_id, device_path, target_path)

    # check if the video is correct format

    action_detail = {
        "video": target_path,
        "type": "click",
        "location": [x, y],
        "bbox": bbox,
    }
    return action_detail

def swipe_and_recording(AVD_NAME, orientation, name, video_folder):

    device_path = f"/sdcard/{name}.mp4"
    target_path = os.path.join(video_folder, f"{name}.mp4")
    
    adb_id = get_adb_id(AVD_NAME)

    screen_record_thread = threading.Thread(target=start_screen_record, args=(adb_id, device_path))
    screen_record_thread.start()
    time.sleep(0.4)
    adb_swipe(orientation, adb_id)
    time.sleep(2)
    stop_screen_record(adb_id)
    screen_record_thread.join()
    pull_screen_record(adb_id, device_path, target_path)

    # check if the video is correct format

    action_detail = {
        "video": target_path,
        "type": "swipe",
        "orientation": orientation
    }
    return action_detail

        

if __name__ == "__main__":
    take_screencap("emulator-5554", "/sdcard/screenshot.png")
    pull_file("emulator-5554", "/sdcard/screenshot.png","./screenshot.png")
    