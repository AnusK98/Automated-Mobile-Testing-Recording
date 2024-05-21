import cv2
import json
import os
import numpy as np

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
