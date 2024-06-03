import os
import subprocess
import json
import shutil

def get_frame_timestamps_and_durations(video_path):
    # Construct the ffprobe command to run
    ffprobe_cmd = f"ffprobe -v error -show_entries packet=pts_time,duration_time,stream_index -of json {video_path}"

    # Execute the command
    result = subprocess.run(ffprobe_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True)

    # Parse the output to JSON
    try:
        output = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        print(f"Error decoding ffprobe output: {e}")
        return []

    # Extract timestamps and durations
    try:
        timestamps_and_durations = [(float(packet['pts_time']), float(packet['duration_time'])) for packet in output['packets'] if 'pts_time' in packet and 'duration_time' in packet]
    except KeyError as e:
        print(f"Error extracting timestamps and durations: {e}")
        return []

    return timestamps_and_durations

def video_to_images_to_gif(video_path, output_dir, pred_frames, gif_index, remove = True, fps=20):
    # if the output directory exists, remove it
    if os.path.exists(f"{output_dir}/{gif_index}"):
        shutil.rmtree(f"{output_dir}/{gif_index}")
    
    os.makedirs(f"{output_dir}/{gif_index}")

    # extract video into images by start_frames and end_frames
    for i, (start_frame, end_frame) in enumerate(pred_frames):
        extract_command = [
            'ffmpeg',
            '-hide_banner',
            '-loglevel', 'panic',
            '-i', video_path,
            '-vf', f'select=\'between(n\,{start_frame}\,{end_frame})\'',
            '-vsync', '0',
            f'{output_dir}/{gif_index}/{i}_frame_%04d.png'
        ]
        subprocess.run(extract_command)
        generate_palette_command = [
            'ffmpeg',
            '-hide_banner',
            '-loglevel', 'panic',
            '-framerate', str(fps),
            '-i', f'{output_dir}/{gif_index}/{i}_frame_%04d.png',
            '-vf', 'fps=10,scale=320:-1:flags=lanczos,palettegen',
            f'{output_dir}/{gif_index}/palette.png'
        ]
        subprocess.run(generate_palette_command)
        create_gif_command = [
            'ffmpeg',
            '-hide_banner',
            '-loglevel', 'panic',
            '-framerate', str(fps),
            '-i', f'{output_dir}/{gif_index}/{i}_frame_%04d.png',
            '-i', f'{output_dir}/{gif_index}/palette.png',
            '-filter_complex', 'fps=10,scale=512:-1:flags=lanczos[x];[x][1:v]paletteuse',
            f"{output_dir}/{gif_index}.gif"
        ]
        subprocess.run(create_gif_command)
        # remove the extracted images
        if remove:
            shutil.rmtree(f"{output_dir}/{gif_index}")

def video_to_whole_gif(video_path, output_dir, gif_index, fps=10):
    # Path for the output gif
    gif_output_path = os.path.join(output_dir, f"{gif_index}.gif")

    # Ensure the output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Remove existing GIF if necessary
    if os.path.exists(gif_output_path):
        os.remove(gif_output_path)
    try:
        # Generate palette for better color accuracy in GIF
        generate_palette_command = [
            'ffmpeg',
            '-hide_banner',
            '-loglevel', 'panic',
            '-y',  # Overwrite output files without asking
            '-i', video_path,
            '-vf', 'fps={0},scale=320:-1:flags=lanczos,palettegen'.format(fps),
            f"{output_dir}/palette.png"
        ]
        subprocess.run(generate_palette_command, check=True)

        # Create the GIF using the palette
        create_gif_command = [
            'ffmpeg',
            '-hide_banner',
            '-loglevel', 'panic',
            '-y',  # Overwrite output files without asking
            '-i', video_path,
            '-i', f"{output_dir}/palette.png",
            '-filter_complex', 'fps={0},scale=512:-1:flags=lanczos[x];[x][1:v]paletteuse'.format(fps),
            gif_output_path
        ]
        subprocess.run(create_gif_command, check=True)

        # Optionally, remove the palette image after creating the GIF
        os.remove(f"{output_dir}/palette.png")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error creating GIF: {e}")
        return False