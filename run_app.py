import os
import time
import requests
import jwt

# Read configurations from GitHub Secrets
APP_ID = os.getenv("APP_ID")
PRIVATE_KEY_PATH = "private_key.pem"

def generate_jwt():
    try:
        with open(PRIVATE_KEY_PATH, "r") as key_file:
            private_key = key_file.read()
    except FileNotFoundError:
        print("❌ Error: private_key.pem file not found.")
        return None

    now = int(time.time())
    payload = {"iat": now - 60, "exp": now + (10 * 60), "iss": APP_ID}
    return jwt.encode(payload, private_key, algorithm="RS256")

def get_installation_access_token(jwt_token):
    jwt_headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "GitHub-App-Profile-Viewer"
    }
    try:
        # Step A: Get all installations of this app
        res = requests.get("https://api.github.com/app/installations", headers=jwt_headers)
        if res.status_code != 200:
            print(f"❌ Failed to list installations. Code: {res.status_code}")
            return None
            
        installations = res.json()
        if not installations or not isinstance(installations, list) or len(installations) == 0:
            print("❌ App is not installed on any account.")
            return None
        
        # MATCHED FIX: Correctly extract the installation ID from the list structure [0]
        installation_id = installations[0]["id"]
        
        # Step B: Request an access token for this specific installation
        token_url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
        token_res = requests.post(token_url, headers=jwt_headers)
        
        if token_res.status_code == 201:
            return token_res.json().get("token")
        else:
            print(f"❌ Failed to get token. Code: {token_res.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error during token exchange: {e}")
        return None

def main():
    # Read the target user from a local configuration file
    try:
        with open("target_user.txt", "r") as f:
            username = f.read().strip()
    except FileNotFoundError:
        username = "octocat"  # Default fallback if the target file is missing

    print(f"🚀 Fetching profile data for: {username}...")
    
    jwt_token = generate_jwt()
    if not jwt_token: return
    
    installation_token = get_installation_access_token(jwt_token)
    if not installation_token: return

    # MATCHED FIX: Use the specific "token {installation_token}" header format string
    headers = {
        "Authorization": f"token {installation_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "GitHub-App-Profile-Viewer"
    }

    user_res = requests.get(f"https://api.github.com/users/{username}", headers=headers)
    repos_res = requests.get(f"https://api.github.com/users/{username}/repos?per_page=30&sort=updated", headers=headers)

    if user_res.status_code == 200 and repos_res.status_code == 200:
        u_data = user_res.json()
        r_data = repos_res.json()

        # Build a beautiful Markdown report file to showcase on GitHub
        markdown = f"# 👤 GitHub Profile Report: {u_data.get('name') or username}\n\n"
        markdown += f"**Bio:** {u_data.get('bio') or 'No bio available.'}\n"
        markdown += f"**Public Repos:** {u_data.get('public_repos')} | **Followers:** {u_data.get('followers')}\n\n"
        markdown += "### 📦 Top Public Repositories (Recently Updated)\n"
        
        for repo in r_data:
            lang = f" ({repo.get('language')})" if repo.get('language') else ""
            markdown += f"- [{repo['name']}]({repo['html_url']}){lang}\n"

        with open("profile_report.md", "w") as f:
            f.write(markdown)
        print("✅ Success! profile_report.md has been generated.")
    else:
        print(f"❌ API Error. User status: {user_res.status_code}, Repos status: {repos_res.status_code}")

if __name__ == "__main__":
    main()
