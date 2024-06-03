import json
import re
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

def load_json(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def save_json(file_path, data):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

def extract_id_number(input_str):
    match = re.search(r'id:\s*(\d+)', input_str)
    if match:
        return int(match.group(1))
    return None

def build_data_folder():
    if not os.path.exists(config.DATA_FOLDER):
        os.makedirs(config.DATA_FOLDER)
    
    if not os.path.exists(config.JSON_FOLDER):
        os.makedirs(config.JSON_FOLDER)
    
    if not os.path.exists(config.VIDEO_FOLDER):
        os.makedirs(config.VIDEO_FOLDER)

    if not os.path.exists(config.IMAGE_TMP_FOLDER):
        os.makedirs(config.IMAGE_TMP_FOLDER)

    if not os.path.exists(config.RAW_IMAGE_FOLDER):
        os.makedirs(config.RAW_IMAGE_FOLDER)
    
    if not os.path.exists(config.UIED_PROCESSED_FOLDER):
        os.makedirs(config.UIED_PROCESSED_FOLDER)
    
    if not os.path.exists(config.SOM_PROCESSED_FOLDER):
        os.makedirs(config.SOM_PROCESSED_FOLDER)