import cv2
import os
import numpy as np
import sys
import subprocess

# Add the parent directory to the system path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import tools.utils as utils
import config

from tools.adb_command import *
from UIED.run_single import run_single


def apply_som(image_location, components, destination_path):
    '''
    Apply the SOM algorithm to the detected UI elements (you can implement your own logic here)
        input : image_location (str), components (json)
        output : None
    '''
    assert(image_location), "Image location cannot be empty"
    assert(components), "Components cannot be empty"
    assert(destination_path), "Destination path cannot be empty"
    # Load the image
    image_name = os.path.basename(image_location)
    img = cv2.imread(image_location)
    if img is None:
        raise FileNotFoundError(f"Image at location {image_location} not found.")
    
    # Extract the image shape from components
    comp_img_shape = components['img_shape']

    # Check if the image size matches img_shape
    if img.shape != tuple(comp_img_shape):
        # Scale bounding boxes to the size of the image
        scale_x = img.shape[1] / comp_img_shape[1]
        scale_y = img.shape[0] / comp_img_shape[0]
        for comp in components['compos']:
            comp['position']['column_min'] = int(comp['position']['column_min'] * scale_x)
            comp['position']['row_min'] = int(comp['position']['row_min'] * scale_y)
            comp['position']['column_max'] = int(comp['position']['column_max'] * scale_x)
            comp['position']['row_max'] = int(comp['position']['row_max'] * scale_y)
    
    # Apply numbering to each bounding box center
    for idx, comp in enumerate(components['compos']):
        position = comp['position']
        center_x = position['column_min'] + (position['column_max'] - position['column_min']) // 4
        center_y = position['row_min'] + (position['row_max'] - position['row_min']) // 4
        visualize_number(img, center_x, center_y, idx)
    
    # Save the processed image to a new path
    new_path = os.path.join(destination_path, image_name)
    cv2.imwrite(new_path, img)
    return components

def visualize_number(img, center_x, center_y, number, font_scale=1.2, thickness=3):
    '''
    Add number to the image at the specified center location
    '''
    text = str(number)
    text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)[0]
    text_x = center_x - (text_size[0] // 2)
    text_y = center_y + (text_size[1] // 2)
    
    # Calculate the rectangle background size
    rect_left = center_x - (text_size[0] // 2) - thickness
    rect_top = center_y - (text_size[1] // 2) - thickness
    rect_right = center_x + (text_size[0] // 2) + thickness
    rect_bottom = center_y + (text_size[1] // 2) + thickness
    
    # Calculate the average color of the rectangle region
    avg_color = np.mean(img[max(0, rect_top):min(rect_bottom, img.shape[0]), max(0, rect_left):min(rect_right, img.shape[1])], axis=(0, 1))
    
    # Check if the average color is dark or light
    if np.mean(avg_color) < 127:
        rect_color = (255, 255, 255)  # White rectangle
        text_color = (0, 0, 255)  # Red text
    else:
        rect_color = (0, 0, 0)  # Black rectangle
        text_color = (255, 255, 255)  # White text
    
    # Draw a filled rectangle for the background
    cv2.rectangle(img, (rect_left, rect_top), (rect_right, rect_bottom), rect_color, -1)
    
    # Put the text (number) on the image, with the specified color
    cv2.putText(img, text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, text_color, thickness)

def process_ui_detection(image_location, destination_path):
    '''
    process the image to detect the UI elements (you can implement your own logic here)
        input : image_location (str)
        output : detected UI elements (json)
    '''
    command = ["mamba", "run", "-n", "uied-env", "python3", "/data/Automated_Device_Testing/UIED/run_single.py", image_location, destination_path]
    result = subprocess.run(command, capture_output=True, text=True)
    print(result.stdout)


def get_screenshot(AVD_NAME, image_name, destination_path):
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

def preprocess_image(AVD_NAME, image_name):
    components = None
    if os.path.exists(os.path.join(config.SOM_PROCESSED_FOLDER, image_name)):
        image_location = os.path.join(config.RAW_IMAGE_FOLDER, image_name)
    else:
        image_location = get_screenshot(AVD_NAME, image_name, config.RAW_IMAGE_FOLDER)
        process_ui_detection(image_location, config.UIED_PROCESSED_FOLDER)
    components = utils.load_json(os.path.join(config.UIED_PROCESSED_FOLDER, "merge", image_name.replace(".png", ".json")))
    if not components:
        # remove the image
        subprocess.run(["rm", image_location])
        return None, None

    scaled_components = apply_som(image_location, components, config.SOM_PROCESSED_FOLDER)
    som_image_location = os.path.join(config.SOM_PROCESSED_FOLDER, image_name)
    return som_image_location, scaled_components

def get_OCR_text(content):
    OCR_text = ""
    elements = content['compos']
    for element in elements:
        if element["class"] == "Text":
            OCR_text += f"ID: {element['id']}, Text: {element['text_content']}\n"
    
    return OCR_text

def get_bbox(ui_id, components):
    # assert ui_id is number
    assert(isinstance(ui_id, int)), "UI ID must be an integer"
    assert(components), "Components cannot be empty"

    if ui_id >= len(components['compos']):
        print(f"UI ID {ui_id} is not found in the components")
        ui_id = random.randint(0, len(components['compos']) - 1)
    
    ui_compos = components["compos"]
    bbox = ui_compos[ui_id]["position"]

    return bbox