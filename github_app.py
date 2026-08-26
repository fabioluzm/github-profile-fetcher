import os
import time
import tkinter as tk
from tkinter import messagebox, ttk
from dotenv import load_dotenv
import jwt
import requests

# Load variables from the local .env file
load_dotenv()

# Read the values securely from the environment variables
APP_ID = os.getenv("APP_ID")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")

class GitHubAppAuthViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("Authenticated GitHub App Viewer")
        self.root.geometry("500x550")
        self.root.configure(bg="#f6f8fa")

        # Configure styling layouts
        self.style = ttk.Style()
        self.style.configure("TLabel", background="#f6f8fa", font=("Arial", 10))
        self.style.configure("Header.TLabel", font=("Arial", 12, "bold"))
        self.style.configure("Title.TLabel", font=("Arial", 16, "bold"), background="#f6f8fa", foreground="#24292e")

        self.setup_ui()
        self.check_configuration()

    def check_configuration(self):
        """Validates that environment configurations were loaded successfully."""
        if not APP_ID or not PRIVATE_KEY:
            messagebox.showerror(
                "Configuration Error", 
                "Missing environment configuration variables.\n\nPlease ensure your local '.env' file contains valid definitions for:\n- APP_ID\n- PRIVATE_KEY"
            )

    def setup_ui(self):
        title_label = ttk.Label(self.root, text="GitHub Authenticated Viewer", style="Title.TLabel")
        title_label.pack(pady=15)

        input_frame = ttk.Frame(self.root, padding=10)
        input_frame.pack(fill="x", padx=20)

        username_label = ttk.Label(input_frame, text="Target GitHub Username:")
        username_label.pack(side="left", padx=5)

        self.username_entry = ttk.Entry(input_frame, font=("Arial", 10), width=25)
        self.username_entry.pack(side="left", padx=5)
        self.username_entry.focus()
        self.username_entry.bind("<Return>", lambda event: self.fetch_github_data())

        fetch_btn = ttk.Button(input_frame, text="Fetch Data", command=self.fetch_github_data)
        fetch_btn.pack(side="left", padx=5)

        separator = ttk.Separator(self.root, orient="horizontal")
        separator.pack(fill="x", padx=20, pady=10)

        self.info_frame = ttk.Frame(self.root, padding=10)
        self.info_frame.pack(fill="x", padx=20)

        self.name_label = ttk.Label(self.info_frame, text="Name: --", style="Header.TLabel")
        self.name_label.pack(anchor="w", pady=2)

        self.bio_label = ttk.Label(self.info_frame, text="Bio: --", wraplength=450)
        self.bio_label.pack(anchor="w", pady=2)

        self.stats_label = ttk.Label(self.info_frame, text="Public Repos: --  |  Followers: --")
        self.stats_label.pack(anchor="w", pady=2)

        repo_frame = ttk.Frame(self.root, padding=10)
        repo_frame.pack(fill="both", expand=True, padx=20, pady=10)

        repo_list_header = ttk.Label(repo_frame, text="Public Repositories:", style="Header.TLabel")
        repo_list_header.pack(anchor="w", pady=5)

        scrollbar = ttk.Scrollbar(repo_frame)
        scrollbar.pack(side="right", fill="y")

        self.repo_listbox = tk.Listbox(
            repo_frame, 
            yscrollcommand=scrollbar.set, 
            font=("Arial", 10), 
            bg="#ffffff", 
            fg="#24292e", 
            highlightthickness=1, 
            highlightbackground="#e1e4e8"
        )
        self.repo_listbox.pack(fill="both", expand=True)
        scrollbar.config(command=self.repo_listbox.yview)

    def generate_jwt(self):
        """Reads local private key file and signs a secure JWT token for GitHub."""
        try:
            with open(PRIVATE_KEY, "r") as key_file:
                private_key = key_file.read()
        except FileNotFoundError:
            messagebox.showerror("File Error", f"Could not locate private key file at:\n{PRIVATE_KEY}")
            return None

        now = int(time.time())
        payload = {
            "iat": now - 60,
            "exp": now + (10 * 60),
            "iss": APP_ID
        }
        return jwt.encode(payload, private_key, algorithm="RS256")

    def get_installation_access_token(self, jwt_token):
        """Exchanges the App JWT for a valid Installation Access Token."""
        jwt_headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "GitHub-App-Profile-Viewer"  # <-- REQUIRED BY GITHUB
        }
        
        try:
            # Step A: Get all installations of this app
            installations_response = requests.get("https://api.github.com/app/installations", headers=jwt_headers)
            
            if installations_response.status_code != 200:
                messagebox.showerror(
                    "Auth Error", 
                    f"Could not list App installations.\n\nCode: {installations_response.status_code}\n"
                    "Ensure you installed the app on your account and headers are exact."
                )
                return None
                
            installations = installations_response.json()
            
            # FIX: Check if the list contains any active installations
            if not installations or not isinstance(installations, list) or len(installations) == 0:
                messagebox.showerror("Installation Missing", "This App has not been installed on any account yet. Go to your GitHub App settings and click 'Install App'.")
                return None
            
            # FIX: Extract the ID from the first element in the array list [0]
            installation_id = installations[0]["id"]
            
            # Step B: Request an access token for this specific installation
            token_url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
            token_response = requests.post(token_url, headers=jwt_headers)
            
            if token_response.status_code == 201:
                return token_response.json().get("token")
            else:
                messagebox.showerror("Token Generation Error", f"Failed to get installation token. Code: {token_response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Network Error", f"Failed connection during app discovery: {e}")
            return None


    def fetch_github_data(self):
        username = self.username_entry.get().strip()
        if not username:
            messagebox.showwarning("Input Error", "Please enter a GitHub username.")
            return

        # 1. Generate core JWT
        jwt_token = self.generate_jwt()
        if not jwt_token:
            return

        # 2. Convert to Installation Access Token
        installation_token = self.get_installation_access_token(jwt_token)
        if not installation_token:
            return

        self.repo_listbox.delete(0, tk.END)

        # 3. Authenticate headers using the Installation Access Token
        headers = {
            "Authorization": f"token {installation_token}", # Must use the word 'token' here
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "GitHub-App-Profile-Viewer"
        }

        user_url = f"https://api.github.com/users/{username}"
        repos_url = f"https://api.github.com/users/{username}/repos?per_page=30&sort=updated"

        try:
            user_response = requests.get(user_url, headers=headers)
            
            if user_response.status_code == 401:
                messagebox.showerror("Authentication Failed", "GitHub API rejected the installation token.")
                return
            elif user_response.status_code == 404:
                messagebox.showerror("Not Found", f"User '{username}' does not exist on GitHub.")
                return
            elif user_response.status_code != 200:
                messagebox.showerror("Error", f"Failed API connection query. Error Code: {user_response.status_code}")
                return

            user_data = user_response.json()
            self.name_label.config(text=f"Name: {user_data.get('name') or user_data.get('login')}")
            self.bio_label.config(text=f"Bio: {user_data.get('bio') or 'No bio available.'}")
            self.stats_label.config(text=f"Public Repos: {user_data.get('public_repos')}  |  Followers: {user_data.get('followers')}")

            repos_response = requests.get(repos_url, headers=headers)
            if repos_response.status_code == 200:
                repos_data = repos_response.json()
                for repo in repos_data:
                    repo_name = repo.get("name")
                    repo_lang = repo.get("language")
                    display_text = f"📦 {repo_name} ({repo_lang})" if repo_lang else f"📦 {repo_name}"
                    self.repo_listbox.insert(tk.END, display_text)
            else:
                self.repo_listbox.insert(tk.END, "Could not load repositories description list.")

        except requests.exceptions.RequestException:
            messagebox.showerror("Connection Error", "Please verify your active web connection environment.")

if __name__ == "__main__":
    root = tk.Tk()
    app = GitHubAppAuthViewer(root)
    root.mainloop()
