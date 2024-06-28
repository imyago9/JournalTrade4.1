import os
import sys
import shutil
import subprocess
import requests
import zipfile
from appdirs import AppDirs

APP_NAME = 'JournalTrade'
APP_AUTHOR = 'Y'

dirs = AppDirs(APP_NAME, APP_AUTHOR)
user_data_dir = dirs.user_data_dir

# URLs
GITHUB_DIST_ZIP_URL = 'https://github.com/imyago9/JournalTrade4.1/archive/refs/heads/master.zip'
LOCAL_VERSION_FILE = os.path.join(user_data_dir, 'version.txt')
MAIN_EXECUTABLE_PATH = os.path.join(user_data_dir, 'JournalTrade.exe')

def download_and_extract_dist(zip_url, extract_to):
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
        extracted_path = os.path.join(extract_to, 'JournalTrade4.1-master')
        merge_directories(extracted_path, extract_to)
        shutil.rmtree(extracted_path)
    except requests.RequestException as e:
        print(f"Error downloading dist from GitHub: {e}")
        sys.exit(1)

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
                os.chmod(dest_file, 0o777)
                os.remove(dest_file)
            shutil.move(src_file, dest_file)

def main():
    app_pid = int(sys.argv[1])

    # Wait for the main application to close
    while True:
        try:
            os.kill(app_pid, 0)
        except OSError:
            break

    # Update the application
    download_and_extract_dist(GITHUB_DIST_ZIP_URL, os.getcwd())

    # Restart the application
    subprocess.Popen([MAIN_EXECUTABLE_PATH])
    sys.exit(0)

if __name__ == "__main__":
    main()
