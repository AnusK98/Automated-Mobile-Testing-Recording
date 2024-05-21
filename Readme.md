# Automated Mobile Testing Recording Dataset

This project aims to automate mobile testing by recording UI interactions and processing screenshots through various tools. It leverages Android emulators, the PaddlePaddle framework, and a modified UIED project to detect and interact with UI elements.

## Project Structure

- `./data`: Contains all generated data by the program.
- `./tools`: Contains all the tools used in the main file.
- `./UIED`: Modified version of the UIED project. [Original UIED project on GitHub](https://github.com/MulongXie/UIED)
- `./config.py`: Configuration file to set parameters such as screen size and paths.
- `./main.py`: Main script that coordinates the mobile testing processes.

## Setup Instructions

### Environment Setup:

1. Install required packages and tools as described in `environment.yml`.
2. Install PaddlePaddle following the steps on [PaddlePaddle's official website](https://www.paddlepaddle.org.cn/).
3. Install PaddleOCR with the command:
   ```bash
   apt install paddleocr
   ```

### Configuration:
1. Copy the `./config_origin.py` to `./config.py`.
2. Set your Android SDK path in `./config.py`.
3. Enter your Google API keys in the Api_key list in `./config.py`.

### Prepare Emulators:
* Manually start your Android emulator before running tests.

### Installing Apps (Optional):
* If you choose to install apps, place all APK files in a specified directory, and set the `Apps_directory` variable in the `./config.json`. The main script will install these apps on the emulator and verify launchable apps.

## Running the Project
Execute the following command to start the automated testing process:
```bash
python3 main.py
```

The script will perform the actions defined, process screenshots, and record interactions as specified in the configurations.

## CITE
This project uses components from the UIED project, which is licensed under the Apache License 2.0. More details can be found at [UIED GitHub repository](https://github.com/MulongXie/UIED).

UIED is developed by Mulong Xie and the team at the Australian National University. For more information on licensing, visit [Apache License 2.0](http://www.apache.org/licenses/LICENSE-2.0).