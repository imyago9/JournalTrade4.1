import requests
import os
from PyQt5.QtWidgets import QMessageBox
import MainWindow

# URLs
GITHUB_REPO_URL = 'https://raw.githubusercontent.com/imyago9/JournalTrade4.1/master/version.txt'
GITHUB_DIST_ZIP_URL = 'https://github.com/imyago9/JournalTrade4.1/archive/refs/heads/master.zip'
user_data_dir = os.path.join(os.getenv('LOCALAPPDATA'), 'Y', 'JournalTrade')
LOCAL_VERSION_FILE = os.path.join(user_data_dir, 'version.txt')


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


def check_for_updates():
    github_version = get_github_version(GITHUB_REPO_URL)
    local_version = get_local_version(os.path.join(os.getenv('LOCALAPPDATA'), 'Y', 'JournalTrade', 'version.txt'))

    if github_version and local_version and github_version != local_version:
        QMessageBox.information(None, 'Update Available', 'A new version of JournalTrade is available. Please '
                                                          'close the application and run InstallerUpdater.exe.')
        MainWindow.main()
    else:
        print('No updates available, running the application...')
        MainWindow.main()


if __name__ == "__main__":
    check_for_updates()
