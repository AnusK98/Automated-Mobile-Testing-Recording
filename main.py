import os
import subprocess
import json
import config
import random
import re
import time
import threading

from tools.adb_command import *
from tools.check_apps import get_all_packages, check_launchable_apps
from tools.apply_som import apply_som
from tools.install_apps import install_apps_on_emulator
from UIED.run_single import run_single

MANUAL = True
REMOVE_COMPLETE_APPS = False
INSTALL_APPS = False
REMOVE = False
AVD_NAME = "Medium_Phone_API_31_2"
ACTION_PER_APP = 4
WAIT_TIME = 2

RAW_image_folder = os.path.join(config.Screenshot_Path, "raw_screenshot")
UIED_processed_folder = os.path.join(config.Screenshot_Path, "uied_processed")
SOM_processed_folder = os.path.join(config.Screenshot_Path, "som_processed")
VIDEO_folder = os.path.join(config.Screenshot_Path, "video")

MESSAGE_json = os.path.join(config.Screenshot_Path, f"{AVD_NAME}_message.json")
TMP_MESSAGE_json = os.path.join(config.Screenshot_Path, f"{AVD_NAME}_tmp_message.json")
ACTION_json = os.path.join(config.Screenshot_Path, f"{AVD_NAME}_action.json")
EXAMPLE_json = os.path.join(config.Screenshot_Path, f"example_screenshot", f"example_prompt.json")

OCR_txt = os.path.join(config.Screenshot_Path, f"{AVD_NAME}_OCR.txt")

def remove_all_images_and_create(action_json):
    # Remove all the images and remove the video which is not in the action_json
    for folder in [RAW_image_folder, UIED_processed_folder, SOM_processed_folder]:
        subprocess.run(["rm", "-r", folder])
        subprocess.run(["mkdir", folder])
    
    video_list = [f for f in os.listdir(VIDEO_folder) if f.endswith(".mp4")]
    for app in action_json:
        for action in action_json[app]:
            if action["video"].split("/")[-1] in video_list:
                video_list.remove(action["video"].split("/")[-1])
    
    for video in video_list:
        subprocess.run(["rm", os.path.join(VIDEO_folder, video)])

def extract_id_number(input_str):
    match = re.search(r'id:\s*(\d+)', input_str)
    if match:
        return int(match.group(1))
    return None

def extract_examiner_result(input_str):
    match = re.search(r'valid: (\w+)', input_str)
    if match:
        return match.group(1)
    return None

def save_json(json_file, content):
    with open(json_file, 'w') as file:
        json.dump(content, file, indent=4)

def load_json(json_file):
    with open(json_file, 'r') as file:
        return json.load(file)

def get_OCR_text(content):
    OCR_text = ""
    elements = content['compos']
    for element in elements:
        if element["class"] == "Text":
            OCR_text += f"ID: {element['id']}, Text: {element['text_content']}\n"
    
    # save the OCR text
    with open(OCR_txt, 'w') as file:
        file.write(OCR_text)

def get_screenshot(image_name, destination_path):
    '''
    get the screenshot (you can implement your own logic here), the image need to be saved in the destination_path folder
        input : image_name (str)
        output : image_location (str)
    '''
    adb_id = get_adb_id(AVD_NAME)
    source_path = f"/sdcard/{image_name}"
    destination_path = os.path.join(destination_path, image_name)

    take_screenshot_and_pull(adb_id, source_path, destination_path)
    return destination_path

def process_ui_detection(image_location, destination_path):
    '''
    process the image to detect the UI elements (you can implement your own logic here)
        input : image_location (str)
        output : detected UI elements (json)
    '''
    componenets = run_single(image_location, destination_path)
    return componenets

def do_action_and_recording(ui_id, components, index, video_folder):
    '''
    perform the action on the UI element (you can implement your own logic here)
        input : ui_id (int), components (json)
        output : action_detail (json)
    '''
    
    # assert ui_id is number
    assert(isinstance(ui_id, int)), "UI ID must be an integer"
    assert(components), "Components cannot be empty"
    device_path = f"/sdcard/{AVD_NAME}_{index}.mp4"
    target_path = os.path.join(video_folder, f"{AVD_NAME}_{index}.mp4")

    if ui_id >= len(components['compos']):
        print(f"UI ID {ui_id} is not found in the components")
        ui_id = random.randint(0, len(components['compos']) - 1)

    ui_compos = components["compos"]
    bbox = ui_compos[ui_id]["position"]
    x = (bbox['column_min'] + bbox['column_max']) // 2
    y = (bbox['row_min'] + bbox['row_max']) // 2

    adb_id = get_adb_id(AVD_NAME)

    screen_record_thread = threading.Thread(target=start_screen_record, args=(adb_id, device_path))
    screen_record_thread.start()
    adb_click(x, y, adb_id)
    time.sleep(WAIT_TIME)
    stop_screen_record(adb_id)
    screen_record_thread.join()
    pull_screen_record(adb_id, device_path, target_path)

    # check if the video is correct format

    action_detail = {
        "video": target_path,
        "type": "click",
        "location": [x, y],
        "bbox": bbox,
        "id": ui_id
    }
    return action_detail

def send_image_prompt_to_VLM(image_location, API_key, task="tester", message_json=None, OCR=None):
    '''
    send the image prompt to the VLM (you can implement your own logic here)
        input : image_location (str)
        output : response from the VLM (json)
    '''

    command = ["mamba", "run", "-n", "gemini", "python3", "/data/Automated_Device_Testing/tools/vlm_gemini.py", image_location, API_key, task, message_json]
    if OCR:
        command.append(OCR)

    result = subprocess.run(
        command,
        capture_output=True,
        text=True
    )

    try:
        output = json.loads(result.stdout)
        if task == "tester":
            response = output['response']
            messages = output['messages']
            ui_id = extract_id_number(response)
            return response, messages, ui_id
        elif task == "examiner":
            response = output['response']
            messages = output['messages']
            return response, messages, None
        
    except Exception as e:
        print(f"Error: {e}")
        print(result.stdout)
        print(result.stderr)
        return None, None, None

def preprocess_image(image_name):
    if os.path.exists(os.path.join(SOM_processed_folder, image_name)):
        image_location = os.path.join(RAW_image_folder, image_name)
        components = load_json(os.path.join(UIED_processed_folder, "merge", image_name.replace(".png", ".json")))
    else:
        components = None
        image_location = get_screenshot(image_name, RAW_image_folder)
        components = process_ui_detection(image_location, UIED_processed_folder)
        if not components:
            # remove the image
            subprocess.run(["rm", image_location])
            return None, None

    scaled_components = apply_som(image_location, components, SOM_processed_folder)
    som_image_location = os.path.join(SOM_processed_folder, image_name)
    return som_image_location, scaled_components

def tester(API_key, message_json, index):
    image_name = f"{AVD_NAME}_{index}.png"
    som_image_location, scaled_components = preprocess_image(image_name)

    if som_image_location is None:
        return None, "Screenshot is not valid"

    if len(scaled_components["compos"]) == 0:
        return None, None

    if MANUAL:
        print(som_image_location)
        ui_id = int(input("Enter the UI ID: "))
        messages = "Manual"
    
    else:
        get_OCR_text(scaled_components)
        response, messages, ui_id = send_image_prompt_to_VLM(som_image_location, API_key, "tester", message_json, OCR_txt)
        if not response:
            print(som_image_location, API_key, "tester", message_json, OCR_txt)
            return None, None
    
    save_json(message_json, messages)
    return ui_id, scaled_components

def examiner(API_key, message_json, index, prev_scaled_components):
    image_name = f"{AVD_NAME}_{index}.png"
    som_image_location, scaled_components = preprocess_image(image_name)

    if som_image_location is None:
        return False, "Screenshot is not valid"

    # check if the components are the same
    if prev_scaled_components == scaled_components:
        return False, "Components are the same"

    if MANUAL:
        print(som_image_location)
        response = bool(int(input("Is the screenshot valid? (1/0): ")))
        if response == False:
            scaled_components = "Manual"
        messages = "Manual"
    else:
        response, messages, _ = send_image_prompt_to_VLM(som_image_location, API_key, "examiner", message_json)
        
        if not response or extract_examiner_result(response) != "True":
            return False, response
    
    save_json(message_json, messages)
    return response, scaled_components

def get_device_apps():
    adb_id = get_adb_id(AVD_NAME)
    all_packages = get_all_packages(adb_id, True)
    launchable_apps = check_launchable_apps(all_packages, adb_id)

    with open(f"./data/{AVD_NAME}_apps.json", 'w') as file:
        json.dump({AVD_NAME:launchable_apps}, file, indent=4)

    return launchable_apps

def clean_up(app_name):
    subprocess.run(["cp", EXAMPLE_json, MESSAGE_json])
    adb_restart_app(get_adb_id(AVD_NAME), app_name)

def select_apps(action_json):
    with open(f"./data/{AVD_NAME}_apps.json", 'r') as file:
        app_names = json.load(file)[AVD_NAME]

    if REMOVE_COMPLETE_APPS:
        # Remove the apps that already in action_json keys
        for app in list(action_json.keys()):
            if app in app_names:
                app_names.remove(app)

    return app_names

def count_video_numbers():
    action_json = load_json(ACTION_json)
    # count the video in the action_json
    count = 0
    for app in action_json:
        count += len(action_json[app])
    print(count)

def main():
    action_json = {}
    if os.path.exists(ACTION_json):
        action_json = load_json(ACTION_json)

    app_names = select_apps(action_json)

    # Go through each app
    for app_name in app_names[40:]:
        clean_up(app_name)

        repeat, api_count = 0, 0
        if app_name not in action_json:
            action_json[app_name] = []
            index = 0
        else:
            index = len(action_json[app_name])

        while index < ACTION_PER_APP: 
            
            name = [f"{app_name}_{index}", f"{app_name}_{index+1}"]

            api_key = config.Api_key[api_count % len(config.Api_key)]
            api_count += 1
            repeat += 1

            if repeat > 3:
                if repeat > 5:
                    break
                clean_up(app_name)
                subprocess.run(["rm", os.path.join(SOM_processed_folder, f"{AVD_NAME}_{name[0]}.png")])
                subprocess.run(["rm", os.path.join(SOM_processed_folder, f"{AVD_NAME}_{name[1]}.png")])

            subprocess.run(["cp", MESSAGE_json, TMP_MESSAGE_json])

            # Tester
            ui_id, scaled_components = tester(api_key, TMP_MESSAGE_json, name[0])
            if scaled_components == "Screenshot is not valid":
                break
            if ui_id is None:
                continue
            
            # Perform the action
            action_detailed = do_action_and_recording(ui_id, scaled_components, name[0], VIDEO_folder)

            # Examiner
            exam_response, response = examiner(api_key, TMP_MESSAGE_json, name[1], scaled_components)
            if exam_response is False and response != None:
                print(f"Failed : {response}")
                if response == "Screenshot is not valid":
                    break
                if MANUAL:
                    os.remove(os.path.join(SOM_processed_folder, f"{AVD_NAME}_{name[0]}.png"))
                    os.remove(os.path.join(SOM_processed_folder, f"{AVD_NAME}_{name[1]}.png"))
                continue
            
            # Complete the action
            action_json[app_name].append(action_detailed)
            save_json(ACTION_json, action_json)
            index += 1
            repeat = 0
            subprocess.run(["mv", TMP_MESSAGE_json, MESSAGE_json])
        
        # Force stop the app
        adb_close_app(get_adb_id(AVD_NAME), app_name)

if __name__ == "__main__":
    if INSTALL_APPS:
        install_apps_on_emulator(AVD_NAME)
        get_device_apps()
    
    if REMOVE:
        action_json = load_json(ACTION_json)
        remove_all_images_and_create(action_json)

    # main()
    count_video_numbers()
    # preprocess_image("Medium_Phone_API_31_2_com.yogeshpaliyal.keypass_0.png")
