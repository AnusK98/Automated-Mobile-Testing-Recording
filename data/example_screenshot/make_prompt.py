def pop_prompt_id(id):
    return f"For Tester: The above screenshot is an example of a popup window. The UI element tagged with {id} is a popup, so you should prioritize clicking on these elements to manage or close the popup before interacting with other elements of the app."

def example_prompt():
    pop_ids = [[7,8,9],[8,9,10],[3,4,10,11,12,13,14],[4,7,8,9,10,11,12,13,14]]
    pop_prompt = [pop_prompt_id(pop_id) for pop_id in pop_ids]
    video_prompt = "For Examiner: The above two screenshots depict an invalid click since, although the frames are different, they only show different moments of a video, without any actionable click resulting in a functional change in the app."
    load_prompt = "For Examiner: The above two screenshots depict an invalid action. Despite the two different frames, both are part of a loading screen sequence. This indicates no actual operation was performed between the two states, thus rendering the click invalid."
    success_prompt = "For Examiner: The above two screenshots depict a valid action since the two frames are different, showing a change in the UI that confirms the function of the clicked button has been activated."

    example_path = f"/data/Automated_Device_Testing/screenshots/example_screenshot/"

    pop_images = [f"{example_path}pop_{i}.png" for i in range(1, 5)]
    video_images = [[f"{example_path}video_{i}.png", f"{example_path}video_{i}_aft.png"] for i in range(1, 3)]
    load_images = [[f"{example_path}load_{i}.png", f"{example_path}load_{i}_aft.png"] for i in range(1, 2)]
    success_images = [[f"{example_path}sucess_{i}.png", f"{example_path}sucess_{i}_aft.png"] for i in range(1, 4)]

    formatted_list = []
    
    # Append pop images with prompt
    for img, pop in zip(pop_images, pop_prompt):
        formatted_list.append(img)
        formatted_list.append(pop)
    
    # Append video images with prompt
    for imgs in video_images:
        formatted_list.extend(imgs)
        formatted_list.append(video_prompt)
    
    # Append load images with prompt
    for imgs in load_images:
        formatted_list.extend(imgs)
        formatted_list.append(load_prompt)
    
    # Append success images with prompt
    for imgs in success_images:
        formatted_list.extend(imgs)
        formatted_list.append(success_prompt)

    message = {"role": "user", "parts": formatted_list}

    return message