import requests
from functions import user_data_dir, data_path
import zipfile
import shutil
import os
import subprocess
import MainWindow

# URLs
GITHUB_REPO_URL = 'https://raw.githubusercontent.com/imyago9/JournalTrade4.1/master/version.txt'
GITHUB_DIST_ZIP_URL = 'https://github.com/imyago9/JournalTrade4.1/archive/refs/heads/master.zip'
data_path = os.path.join(user_data_dir, 'data')
LOCAL_VERSION_FILE = os.path.join(data_path, 'version.txt')

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

def download_and_extract_dist(zip_url, extract_to, subfolder):
    try:
        response = requests.get(zip_url, stream=True)
        response.raise_for_status()
        zip_path = os.path.join(extract_to, 'dist.zip')
        with open(zip_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=128):
                file.write(chunk)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        os.remove(zip_path)
        extracted_path = os.path.join(extract_to, 'JournalTrade4.1-master', subfolder)
        merge_directories(extracted_path, extract_to)
        shutil.rmtree(os.path.join(extract_to, 'JournalTrade4.1-master'))
    except requests.RequestException as e:
        print(f"Error downloading dist from GitHub: {e}")

def merge_directories(src, dest):
    for root, dirs, files in os.walk(src):
        relative_path = os.path.relpath(root, src)
        dest_path = os.path.join(dest, relative_path)
        if not os.path.exists(dest_path):
            os.makedirs(dest_path)
        for file in files:
            src_file = os.path.join(root, file)
            dest_file = os.path.join(dest_path, file)
            if os.path.exists(dest_file):
                os.remove(dest_file)
            shutil.move(src_file, dest_file)

def is_dir_empty(directory):
    return not any(os.scandir(directory))

def restart_application():
    # Adjust this to the path of your main executable or script
    main_executable_path = os.path.join(user_data_dir, 'dist', 'JournalTrade.exe')
    print(f"Attempting to restart application from {main_executable_path}")
    if not os.path.isfile(main_executable_path):
        print(f"Executable not found: {main_executable_path}")
    else:
        subprocess.Popen([main_executable_path])
        os._exit(0)  # Terminate current script



def main():
    if not os.path.exists(user_data_dir):
        os.makedirs(user_data_dir)

    if is_dir_empty(user_data_dir):
        print(f'{user_data_dir} is empty. Downloading and installing application from Github.')
        download_and_extract_dist(GITHUB_DIST_ZIP_URL, user_data_dir, 'dist')
        print('Installing complete.')
        MainWindow.main()
    else:
        github_version = get_github_version(GITHUB_REPO_URL)
        local_version = get_local_version(LOCAL_VERSION_FILE)

        if github_version and local_version:
            if github_version != local_version:
                print(f"Version mismatch! GitHub version: {github_version}, Local version: {local_version}")
                print('Updating application.')
                shutil.rmtree(user_data_dir)
                os.makedirs(user_data_dir, exist_ok=True)
                download_and_extract_dist(GITHUB_DIST_ZIP_URL, user_data_dir, 'dist')
                with open(LOCAL_VERSION_FILE, 'w') as file:
                    file.write(github_version)
                print('Update complete. Restarting application..')
                restart_application()
            else:
                print("Versions are up to date.")
                MainWindow.main()
        elif github_version:
            print(f"GitHub version: {github_version}, but local version is missing.")
            print('Updating...')
            download_and_extract_dist(GITHUB_DIST_ZIP_URL, user_data_dir, 'dist')
            with open(LOCAL_VERSION_FILE, 'w') as file:
                file.write(github_version)
            print("Installation complete. Restarting application...")
            restart_application()

if __name__ == "__main__":
    main()