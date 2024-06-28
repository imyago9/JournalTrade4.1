import os
import sys
import requests
import zipfile
import shutil
import subprocess
from PyQt5.QtWidgets import QApplication, QMessageBox

# URLs
GITHUB_VERSION_URL = 'https://raw.githubusercontent.com/imyago9/JournalTrade4.1/master/version.txt'
GITHUB_EXE_URL = 'https://github.com/imyago9/JournalTrade4.1/raw/master/JournalTrade.exe'
GITHUB_UPDATER_URL = 'https://github.com/imyago9/JournalTrade4.1/raw/master/InstallerUpdater.exe'
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

def download_file(url, save_path):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(save_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=128):
                file.write(chunk)
    except requests.RequestException as e:
        print(f"Error downloading file from GitHub: {e}")


def create_update_script():
    update_script_path = os.path.join(user_data_dir, 'update.bat')
    if not os.path.exists(update_script_path):
        with open(update_script_path, 'w') as file:
            file.write(
                '''@echo off
echo Starting update...
ping 127.0.0.1 -n 5 > nul
xcopy /s /y "%~dp0new_files\\*" "%~dp0"
rmdir /s /q "%~dp0new_files"
start "" "%~dp0JournalTrade.exe"
exit
''')

def main():
    app = QApplication(sys.argv)

    create_update_script()

    github_version = get_github_version(GITHUB_VERSION_URL)
    local_version = get_local_version(LOCAL_VERSION_FILE)

    if not os.path.exists(user_data_dir) or local_version is None:
        reply = QMessageBox.question(None, 'Install JournalTrade', 'No installation found. Do you want to install JournalTrade?', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if reply == QMessageBox.Yes:
            if not os.path.exists(user_data_dir):
                os.makedirs(user_data_dir)
            if not os.path.exists(TEMP_DIR):
                os.makedirs(TEMP_DIR)
            download_file(GITHUB_EXE_URL, os.path.join(TEMP_DIR, 'JournalTrade.exe'))
            download_file(GITHUB_UPDATER_URL, os.path.join(TEMP_DIR, 'InstallerUpdater.exe'))
            shutil.copytree(TEMP_DIR, user_data_dir, dirs_exist_ok=True)
            with open(LOCAL_VERSION_FILE, 'w') as file:
                file.write(github_version)
            subprocess.Popen([os.path.join(user_data_dir, 'update.bat')])
            sys.exit(0)
    elif github_version != local_version:
        reply = QMessageBox.question(None, 'Update JournalTrade', 'An update is available. Do you want to update JournalTrade?', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if reply == QMessageBox.Yes:
            if not os.path.exists(TEMP_DIR):
                os.makedirs(TEMP_DIR)
            download_file(GITHUB_EXE_URL, os.path.join(TEMP_DIR, 'JournalTrade.exe'))
            download_file(GITHUB_UPDATER_URL, os.path.join(TEMP_DIR, 'InstallerUpdater.exe'))
            shutil.copytree(TEMP_DIR, user_data_dir, dirs_exist_ok=True)
            with open(LOCAL_VERSION_FILE, 'w') as file:
                file.write(github_version)
            subprocess.Popen([os.path.join(user_data_dir, 'update.bat')])
            sys.exit(0)
    elif github_version == local_version:
        print('Version Match')
        print(github_version)
        print(local_version)
        QMessageBox.information(None, 'Up-to-date', 'JournalTrade is up-to-date.')

    sys.exit()

if __name__ == "__main__":
    main()
