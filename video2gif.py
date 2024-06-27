import imageio
import os
import subprocess
import shlex
import json
import matplotlib.pyplot as plt
import shutil
import numpy as np
from tqdm import tqdm

from tools.ffprobe_tools import get_frame_timestamps_and_durations, video_to_whole_gif
import config

def main(source_dataset_path, target_dataset_path, emulator_id=None):
    timestamp_filename = os.path.join(config.DATA_FOLDER, f"")
    if emulator_id is not None:
        timestamp_filename = f'{emulator_id}_action.json'

    action_file_path = os.path.join(source_dataset_path, timestamp_filename)
    output_dir = os.path.join(target_dataset_path, 'segments')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    output_json_path = os.path.join(target_dataset_path, 'action.json')
    videos_path = os.path.join(source_dataset_path, 'video')

    with open(action_file_path) as file:
        actions_data = json.load(file)

    # if the output action file exists, read it as gif_action_pairs
    if os.path.exists(output_json_path):
        with open(output_json_path) as file:
            gif_action_pairs = json.load(file)
    else:
        gif_action_pairs = {}
    # get the largest gif index from the existing gifs
    gif_files = [f for f in os.listdir(output_dir) if f.endswith('.gif')]
    gif_index = len(gif_files)

    print(f"Processing {len(actions_data)} apps with {sum([len(entries) for entries in actions_data.values()])} actions.")

    # Process each video ID and its associated actions
    for app_name, entries in actions_data.items():
        for entry in entries:  # Skip the app name, start from the first video entry
            video_name = entry["video"]
            video_path = video_name

            if "type" not in entry or "location" not in entry or "bbox" not in entry:
                continue
            
            if not os.path.exists(video_path):
                print(f"Video file for {video_name} does not exist. Skipping.")
                continue

            # Assuming you have a function to check and extract frames based on timestamps and return boolean success
            timestamps_and_durations = get_frame_timestamps_and_durations(video_path)
            if not timestamps_and_durations:
                print(f"Error processing video {video_name}. Skipping.")
                continue

            # Here we process and create GIF

            successful = video_to_whole_gif(video_path, output_dir, gif_index)
            if successful:
                gif_action_pairs[f"{gif_index}.gif"] = {
                    "app": app_name,
                    "type": entry["type"],
                    "location": entry["location"],
                    "bbox": entry["bbox"]
                }
                gif_index += 1
   
    # Write the output JSON
    with open(output_json_path, 'w') as outfile:
        json.dump(gif_action_pairs, outfile, indent=4)

if __name__ == "__main__":
    source_dataset_path = '/data/Automated_Device_Testing/data'
    target_dataset_path = '/data/dataset/manual_validate/demo'
    for emulator_id in ['Medium_Phone_API_31_2']:
        main(source_dataset_path, target_dataset_path, emulator_id=emulator_id)
