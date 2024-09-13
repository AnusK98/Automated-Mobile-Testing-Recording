import os
import config
import random

import config

from tools.check_apps import read_device_apps
from tools.adb_command import adb_restart_app, tap_and_recording, swipe_and_recording, adb_close_app
from tools.apply_som import preprocess_image, get_OCR_text, get_bbox
from tools.utils import save_json, load_json, extract_action_type, extract_orientation, extract_id_number, build_data_folder
from agents.Agents import Tester, Examiner

MANUAL = False

def get_action_json(AVD_NAME):
    ACTION_json = os.path.join(config.DATA_FOLDER, f"{AVD_NAME}_action.json")
    action_json = {}
    if os.path.exists(ACTION_json):
        action_json = load_json(ACTION_json)
    return action_json

def tester_pipeline(tester, AVD_NAME, iter_name):
    image_name = f"{iter_name}.png"
    som_image_location, scaled_components = preprocess_image(AVD_NAME, image_name) # Process the image and save it to the SOM_processed_folder
    ui_id = ""
    orientation = 0
    while ((not isinstance(ui_id, int)) and (not isinstance(orientation, str))):
        if MANUAL:
            print(som_image_location)
            ui_id = int(input("Enter the UI ID: "))
            res = "Manual Mode"
        else:
            ocr_text = get_OCR_text(scaled_components)
            api_key = random.choice(config.API_KEYS)
            tester.initialize_prompt(som_image_location, ocr_text)
            res = tester.send_prompt_to_VLM(api_key)
            print("----------------- tester_pipeline -----------------")
            print(res)
            action_type = extract_action_type(res)
            if action_type == "tap":
                ui_id = extract_id_number(res)
                bbox = get_bbox(ui_id, scaled_components)
                return res, bbox
            elif action_type == "swipe":
                orientation = extract_orientation(res)
                return res, orientation
    
    

def examiner_pipeline(examiner, AVD_NAME, iter_names):
    image_names = [f"{x}.png" for x in iter_names]
    som_image_location, scaled_components_1 = preprocess_image(AVD_NAME, image_names[1]) # Process the image and save it to the SOM_processed_folder
    _, scaled_components_2 = preprocess_image(AVD_NAME, image_names[0]) # Process the image and save it to the SOM_processed_folder

    if scaled_components_1 == scaled_components_2:
        return False, False

    if MANUAL:
        print(som_image_location)
        res = bool(int(input("True or False (1/0): ")))
        return res, res
    api_key = random.choice(config.API_KEYS)
    examiner.initialize_prompt(som_image_location)
    return examiner.send_prompt_to_VLM(api_key)

def check_reponse(res, names):
    if res is False :
        os.remove(os.path.join(config.SOM_PROCESSED_FOLDER, f"{names[0]}.png"))
        os.remove(os.path.join(config.SOM_PROCESSED_FOLDER, f"{names[1]}.png"))
        return 1
    return 0

def generate_dataset(AVD_NAME, app_name, action_number):
    action_json = get_action_json(AVD_NAME)
    if app_name not in action_json:
        action_json[app_name] = []

    adb_restart_app(AVD_NAME, app_name)

    message_file = os.path.join(config.EXAMPLE_FOLDER, f"example_prompt.json")
    messages = load_json(message_file)

    tester = Tester(MANUAL)
    examiner = Examiner(MANUAL)

    index = 0
    while index < action_number:
        tmp_message = messages.copy()
        print(f"Generating dataset for {app_name} - {index+1}/{action_number}")
        iter_names = [f"{AVD_NAME}_{app_name}_{index}", f"{AVD_NAME}_{app_name}_{index+1}"]

        #----------------- Tester -----------------
        tester.read_messages(tmp_message)
        res, bbox_orientation = tester_pipeline(tester, AVD_NAME, iter_names[0])
        res_code = check_reponse(res, iter_names)
        if res_code == 1:
            continue
        
        #----------------- Action -----------------
        action_type = extract_action_type(res)
        if action_type == "tap":
            action_detail = tap_and_recording(AVD_NAME, bbox_orientation, iter_names[0], config.VIDEO_FOLDER)
        elif action_type == "swipe":
            action_detail = swipe_and_recording(AVD_NAME, bbox_orientation, iter_names[0], config.VIDEO_FOLDER)

        #----------------- Examiner -----------------
        examiner.read_messages(tester.get_messages())
        res = examiner_pipeline(examiner, AVD_NAME, iter_names)
        print("----------------- examiner_pipeline -----------------")
        print(res)
        res_code = check_reponse(res, iter_names)
        if res_code == 1:
            continue
        
        #----------------- Save -----------------
        messages = examiner.get_messages()
        action_json[app_name].append(action_detail)
        save_json(os.path.join(config.DATA_FOLDER, f"{AVD_NAME}_action.json"), action_json)
        index += 1
    
    adb_close_app(AVD_NAME, app_name)

def main(AVD_NAME, ACTION_NUMBER):
    launchable_apps = read_device_apps(AVD_NAME)
    for app in launchable_apps:
        print(f"Starting generate dataset for {app}")
        generate_dataset(AVD_NAME, app, ACTION_NUMBER)

if __name__ == "__main__":
    build_data_folder()
    AVD_NAME = "Medium_Phone_API_31"
    ACTION_NUMBER = 12
    main(AVD_NAME, ACTION_NUMBER)
