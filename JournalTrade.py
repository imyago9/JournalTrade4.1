import requests
import os
from PyQt5.QtWidgets import QMessageBox
import MainWindow
import shutil

# URLs
GITHUB_REPO_URL = 'https://raw.githubusercontent.com/imyago9/JournalTrade4.1/master/version.txt'
GITHUB_DIST_ZIP_URL = 'https://github.com/imyago9/JournalTrade4.1/archive/refs/heads/master.zip'
user_data_dir = os.path.join(os.getenv('LOCALAPPDATA'), 'Y', 'JournalTrade')
LOCAL_VERSION_FILE = os.path.join(user_data_dir, 'version.txt')
TEMP_DIR = os.path.join(os.getenv('LOCALAPPDATA'), 'Y', 'JournalTrade', 'new_files')


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


def is_dir_empty(directory):
    return not any(os.scandir(directory))

def delete_temp_dir(temp_dir):
    if os.path.exists(temp_dir):
        try:
            shutil.rmtree(temp_dir)
            print(f"Temporary directory {temp_dir} deleted successfully.")
        except Exception as e:
            print(f"Error deleting temporary directory {temp_dir}: {e}")
    else:
        print('No need for deleting temporary files.')



def check_for_updates():
    github_version = get_github_version(GITHUB_REPO_URL)
    local_version = get_local_version(os.path.join(os.getenv('LOCALAPPDATA'), 'Y', 'JournalTrade', 'version.txt'))

    if github_version and local_version and github_version != local_version:
        QMessageBox.information(None, 'Update Available', 'A new version of JournalTrade is available. Please '
                                                          'close the application and run InstallerUpdater.exe.')
        MainWindow.main()
        delete_temp_dir(TEMP_DIR)
    elif github_version == local_version:
        print(f'Version Match! GitHub Version: {github_version}. Local Version: {local_version}')
        print('Opening Application.')
        MainWindow.main()
        delete_temp_dir(TEMP_DIR)


if __name__ == "__main__":
    check_for_updates()
