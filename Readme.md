# Automated Mobile Testing Recording Dataset

This project aims to automate mobile testing by recording UI interactions and processing screenshots through various tools. It leverages Android emulators, the PaddlePaddle framework, and a modified UIED project to detect and interact with UI elements.

## Project Structure

- `./data`: Contains all generated data by the program.
- `./tools`: Contains all the tools used in the main file.
- `./agents`: Contains two agents in our paper.
- `./UIED`: Modified version of the UIED project. [Original UIED project on GitHub](https://github.com/MulongXie/UIED)
- `./config.py`: Configuration file to set parameters such as screen size and paths.
- `./main.py`: Main script that coordinates the mobile testing processes.

## Setup Instructions

### Environment Setup:

We have two distinct environment configuration files in the environments folder due to specific version requirements for different components of our project:

1. **Main Environment Setup**:
    - The `main` environment requires Python 3.9 due to dependencies such as `google-ai-generative`.
    - Install the required packages and tools as specified in the `environments/environment-main.yml`.

2. **UIED Environment Setup**:
    - The `UIED` environment specifically requires Python 3.8.
    - Install the necessary tools and packages as listed in `environments/environment-uied.yml`.

#### Steps to Build the Environments:

1. **Install PaddlePaddle**:
   - Follow the installation steps on [PaddlePaddle's official website](https://www.paddlepaddle.org.cn/).

2. **Install PaddleOCR**:
   - Use the following command to install PaddleOCR:
     ```bash
     apt install paddleocr
     ```

3. **Create and Activate Environments**:
   - To create and activate the `main` environment, use:
     ```bash
     conda env create -f environment-main.yml
     conda activate main-env
     ```
   - To create and activate the `UIED` environment, use:
     ```bash
     conda env create -f environment-uied.yml
     conda activate uied-env
     ```

Please follow these steps to ensure that each component of the project operates within the correct software environment, maintaining compatibility and functionality.


### Configuration:
1. Copy the `./config_origin.py` to `./config.py`.
2. Set your Android SDK path in `./config.py`.
3. Enter your Google API keys in the Api_key list in `./config.py`.

### Prepare Emulators:
* Manually start your Android emulator before running tests. [Android Studio](https://developer.android.com/studio)

### Installing Apps (Optional):
* If you choose to install apps, place all APK files in a specified directory, and set the `Apps_directory` variable in the `./config.py`. Then start the install script in `./tools/install_apps.py`.

## Running the Project
1. Remember to get all apps name and save the list of name to `./data/{AVD_NAME}_apps.json`. You can run the script to check all the valiable apps in the emulator. (Need to start emulator first).
```bash
python3 tools/check_apps.py
```
2. Execute the following command to start the automated testing process:
```bash
python3 main.py
```

The script will perform the actions defined, process screenshots, and record interactions as specified in the configurations.
The labels will be saved in `/data/{AVD_NAME}_action.json`, and the videos will be stored in `/data/video`

## CITE
This project uses components from the UIED project, which is licensed under the Apache License 2.0. More details can be found at [UIED GitHub repository](https://github.com/MulongXie/UIED).

UIED is developed by Mulong Xie and the team at the Australian National University. For more information on licensing, visit [Apache License 2.0](http://www.apache.org/licenses/LICENSE-2.0).