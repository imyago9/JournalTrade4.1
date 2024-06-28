import os
import sys
import requests
import zipfile
import shutil
import subprocess
from PyQt5.QtWidgets import QApplication, QMessageBox

# URLs
GITHUB_REPO_URL = 'https://raw.githubusercontent.com/imyago9/JournalTrade4.1/master/version.txt'
GITHUB_DIST_ZIP_URL = 'https://github.com/imyago9/JournalTrade4.1/archive/refs/heads/master.zip'
user_data_dir = os.path.join(os.getenv('LOCALAPPDATA'), 'Y', 'JournalTrade')
LOCAL_VERSION_FILE = os.path.join(user_data_dir, 'version.txt')
MAIN_EXECUTABLE_PATH = os.path.join(user_data_dir, 'JournalTrade.exe')
UPDATER_PATH = os.path.join(user_data_dir, 'InstallerUpdater.exe')
TEMP_DIR = os.path.join(user_data_dir, 'new_files')

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
        return None

def download_and_extract_dist(zip_url, extract_to):
    try:
        if not os.path.exists(extract_to):
            os.makedirs(extract_to)

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
    app = QApplication(sys.argv)

    github_version = get_github_version(GITHUB_REPO_URL)
    local_version = get_local_version(LOCAL_VERSION_FILE)

    if not os.path.exists(user_data_dir) or local_version is None:
        reply = QMessageBox.question(None, 'Install JournalTrade', 'No installation found. Do you want to install JournalTrade?', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if reply == QMessageBox.Yes:
            if not os.path.exists(user_data_dir):
                os.makedirs(user_data_dir)
            download_and_extract_dist(GITHUB_DIST_ZIP_URL, TEMP_DIR)
            with open(LOCAL_VERSION_FILE, 'w') as file:
                file.write(github_version)
            subprocess.call([os.path.join(user_data_dir, 'update.bat')])
    elif github_version != local_version:
        reply = QMessageBox.question(None, 'Update JournalTrade', 'An update is available. Do you want to update JournalTrade?', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if reply == QMessageBox.Yes:
            download_and_extract_dist(GITHUB_DIST_ZIP_URL, TEMP_DIR)
            with open(LOCAL_VERSION_FILE, 'w') as file:
                file.write(github_version)
            subprocess.call([os.path.join(user_data_dir, 'update.bat')])
    elif github_version == local_version:
        QMessageBox.information(None, 'Up-to-date', 'JournalTrade is up-to-date.')

    sys.exit()

if __name__ == "__main__":
    main()
