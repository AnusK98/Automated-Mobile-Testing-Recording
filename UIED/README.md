# Automate dataset generation

## Steps
1. open Android emulator
    ```
    ./emulator -netdelay none -netspeed full -no-snapshot-load -avd Pixel_6a_API_30_google_play -dns-server 8.8.8.8
    ```
2. run sceenshot.py
    ```
    python3 screenshot.py
    ```
    then the preprocess image will saved at ./processed_images



