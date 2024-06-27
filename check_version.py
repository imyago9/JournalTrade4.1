import requests

# URLs
GITHUB_REPO_URL = 'https://raw.githubusercontent.com/your-username/your-repo/main/version.txt'
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

def main():
    github_version = get_github_version(GITHUB_REPO_URL)
    local_version = get_local_version(LOCAL_VERSION_FILE)

    if github_version and local_version:
        if github_version != local_version:
            print(f"Version mismatch! GitHub version: {github_version}, Local version: {local_version}")
        else:
            print("Versions are up to date.")
    elif github_version:
        print(f"GitHub version: {github_version}, but local version is missing.")
    elif local_version:
        print(f"Local version: {local_version}, but unable to fetch GitHub version.")

if __name__ == "__main__":
    main()
