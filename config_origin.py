import os

SCREEN_WIDTH = 1080
SCREEN_HEIGHT = 2400

APPS_FOLDER = ""
ANDROID_SDK_Path = ""
DATA_FOLDER = "./data"

IMAGE_TMP_FOLDER = os.path.join(DATA_FOLDER, "temp_images")
RAW_IMAGE_FOLDER = os.path.join(IMAGE_TMP_FOLDER, "raw_screenshot")
UIED_PROCESSED_FOLDER = os.path.join(IMAGE_TMP_FOLDER, "uied_processed")
SOM_PROCESSED_FOLDER = os.path.join(IMAGE_TMP_FOLDER, "som_processed")
EXAMPLE_FOLDER = os.path.join(DATA_FOLDER, "example_screenshot")
JSON_FOLDER = os.path.join(DATA_FOLDER, "temp_json")
VIDEO_FOLDER = os.path.join(DATA_FOLDER, "video")

EMULATOR_IDS = [f"emulator-{5554+2*i}" for i in range(4)]
API_KEYS=[]