import os
import requests
import zipfile
import shutil
import subprocess
from functions import user_data_dir

# URLs
GITHUB_REPO_URL = 'https://raw.githubusercontent.com/imyago9/JournalTrade4.1/master/version.txt'
GITHUB_DIST_URL = 'https://github.com/imyago9/JournalTrade4.1/archive/refs/heads/master.zip'
LOCAL_VERSION_FILE = 'version.txt'

def get_github_version(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text.strip()
    except requests.RequestException as e:
        print(f"Error fetching version from GitHub: {e}")
        return None

def get_local_version(file_path):
    try:
        with open(file_path, 'r') as file:
            return file.read().strip()
    except FileNotFoundError:
        print(f"Local version file not found at {file_path}")
        return None

def download_and_extract_dist(url, extract_to):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        zip_path = os.path.join(extract_to, 'dist.zip')
        with open(zip_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=128):
                file.write(chunk)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        os.remove(zip_path)
    except requests.RequestException as e:
        print(f"Error downloading dist from GitHub: {e}")

def is_dir_empty(directory):
    return not any(os.scandir(directory))

def restart_application():
    # Adjust this to the path of your main executable or script
    main_executable_path = os.path.join(user_data_dir, 'JournalTrade4.1-master', 'dist', 'your_application.exe')
    subprocess.Popen([main_executable_path])
    os._exit(0)  # Terminate current script

def main():
    if is_dir_empty(user_data_dir):
        print(f"{user_data_dir} is empty. Downloading and installing application...")
        download_and_extract_dist(GITHUB_DIST_URL, user_data_dir)
        print("Installation complete.")
    else:
        github_version = get_github_version(GITHUB_REPO_URL)
        local_version = get_local_version(LOCAL_VERSION_FILE)

        if github_version and local_version:
            if github_version != local_version:
                print(f"Version mismatch! GitHub version: {github_version}, Local version: {local_version}")
                print("Updating application...")
                shutil.rmtree(user_data_dir)
                os.makedirs(user_data_dir, exist_ok=True)
                download_and_extract_dist(GITHUB_DIST_URL, user_data_dir)
                with open(LOCAL_VERSION_FILE, 'w') as file:
                    file.write(github_version)
                print("Update complete. Restarting application...")
                restart_application()
            else:
                print("Versions are up to date.")
        elif github_version:
            print(f"GitHub version: {github_version}, but local version is missing. Installing application...")
            download_and_extract_dist(GITHUB_DIST_URL, user_data_dir)
            with open(LOCAL_VERSION_FILE, 'w') as file:
                file.write(github_version)
            print("Installation complete. Restarting application...")
            restart_application()

if __name__ == "__main__":
    main()
