import subprocess
import json

def get_all_packages(emulator_name, android_app=True):
    # Get a list of all installed packages
    result = subprocess.run(['adb', '-s', emulator_name, 'shell', 'pm', 'list', 'packages'], stdout=subprocess.PIPE)
    packages = result.stdout.decode().strip().splitlines()
    # Remove packages that are prefix with com.android and com.google
    if not android_app:
        packages = [line for line in packages if not line.startswith("package:com.android") and not line.startswith("package:com.google")]
    
    # Extract package names from the package list
    packages = [line.split(":")[1] for line in packages]
    return packages

def get_emulator_id(device_id):
    command = f"adb -s {device_id} shell getprop | grep avd"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout.strip().split(":")[1][2:-1]

def check_launchable_apps(packages, emulator_name):
    launchable_apps = []
    
    for package_name in packages:
        # Construct the monkey command
        command = f"adb -s {emulator_name} shell monkey -p {package_name} -c android.intent.category.LAUNCHER 1"
        
        # Execute the command
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output = result.stdout.decode().strip()
        
        # Check if monkey was aborted due to no activities
        if "** No activities found to run, monkey aborted." not in output:
            print(f"Launchable app found: {package_name}")
            launchable_apps.append(package_name)
        
        # Turn off the app
        subprocess.run(['adb', '-s', emulator_name, 'shell', 'am', 'force-stop', package_name])
    
    return launchable_apps

def read_json(filepath):
    try:
        with open(filepath, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def write_json(filepath, data):
    with open(filepath, "w") as file:
        json.dump(data, file, indent=4)

if __name__ == "__main__":
    json_path = "../settings/launchable_apps.json"

    emulator_names = ["emulator-5554"]

    andorid_apps = [True, False, False, False]
    # Check which apps are launchable
    for i, emulator_name in enumerate(emulator_names):
            # Get the list of all packages
        all_packages = get_all_packages(emulator_name, andorid_apps[i])
        launchable_apps = check_launchable_apps(all_packages, emulator_name)

        # Load existing data from JSON file
        existing_data = read_json(json_path)
        avd_name = get_emulator_id(emulator_name)

        # Update the dictionary with new data
        existing_data[avd_name] = launchable_apps

        # Write the updated dictionary back to the JSON file
        write_json(json_path, existing_data)
