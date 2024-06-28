import requests
from functions import user_data_dir
import os
import subprocess
import MainWindow
import sys

# URLs
GITHUB_REPO_URL = 'https://raw.githubusercontent.com/imyago9/JournalTrade4.1/master/version.txt'
GITHUB_DIST_ZIP_URL = 'https://github.com/imyago9/JournalTrade4.1/archive/refs/heads/master.zip'
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

def restart_with_update():
    updater_path = os.path.join(os.path.dirname(__file__), 'updater.py')
    subprocess.Popen([sys.executable, updater_path, str(os.getpid())])
    sys.exit(0)

# Check for updates and restart with updater if needed
def check_for_updates():
    github_version = get_github_version(GITHUB_REPO_URL)
    local_version = get_local_version(LOCAL_VERSION_FILE)

    if github_version != local_version:
        print('Version Mismatch')
        print(github_version)
        print(local_version)
        print('Updating application...')
        restart_with_update()
    else:
        print(github_version)
        print(local_version)
        print('No updates needed opening application.')
        MainWindow.main()

# Call check_for_updates() instead of directly calling MainWindow.main()
if __name__ == "__main__":
    check_for_updates()