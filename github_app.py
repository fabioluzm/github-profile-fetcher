import tkinter as tk
from tkinter import messagebox, ttk
import requests

class GitHubDataApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Simple GitHub API Integration App")
        self.root.geometry("500x550")
        self.root.configure(bg="#f6f8fa")  # GitHub-like light gray background

        # Custom Styles
        self.style = ttk.Style()
        self.style.configure("TLabel", background="#f6f8fa", font=("Arial", 10))
        self.style.configure("Header.TLabel", font=("Arial", 12, "bold"))
        self.style.configure("Title.TLabel", font=("Arial", 16, "bold"), background="#f6f8fa", foreground="#24292e")

        self.setup_ui()

    def setup_ui(self):
        # Title Label
        title_label = ttk.Label(self.root, text="GitHub Profile Viewer", style="Title.TLabel")
        title_label.pack(pady=15)

        # Input Frame
        input_frame = ttk.Frame(self.root, padding=10)
        input_frame.pack(fill="x", padx=20)

        username_label = ttk.Label(input_frame, text="Enter GitHub Username:")
        username_label.pack(side="left", padx=5)

        self.username_entry = ttk.Entry(input_frame, font=("Arial", 10), width=25)
        self.username_entry.pack(side="left", padx=5)
        self.username_entry.focus()

        # Bind Enter key to fetch data
        self.username_entry.bind("<Return>", lambda event: self.fetch_github_data())

        fetch_btn = ttk.Button(input_frame, text="Fetch Data", command=self.fetch_github_data)
        fetch_btn.pack(side="left", padx=5)

        # Separator Line
        separator = ttk.Separator(self.root, orient="horizontal")
        separator.pack(fill="x", padx=20, pady=10)

        # Profile Info Display Frame
        self.info_frame = ttk.Frame(self.root, padding=10)
        self.info_frame.pack(fill="x", padx=20)

        self.name_label = ttk.Label(self.info_frame, text="Name: --", style="Header.TLabel")
        self.name_label.pack(anchor="w", pady=2)

        self.bio_label = ttk.Label(self.info_frame, text="Bio: --", wraplength=450)
        self.bio_label.pack(anchor="w", pady=2)

        self.stats_label = ttk.Label(self.info_frame, text="Public Repos: --  |  Followers: --")
        self.stats_label.pack(anchor="w", pady=2)

        # Repositories List Frame
        repo_frame = ttk.Frame(self.root, padding=10)
        repo_frame.pack(fill="both", expand=True, padx=20, pady=10)

        repo_list_header = ttk.Label(repo_frame, text="Public Repositories:", style="Header.TLabel")
        repo_list_header.pack(anchor="w", pady=5)

        # Scrollable Listbox for Repos
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

    def fetch_github_data(self):
        username = self.username_entry.get().strip()
        if not username:
            messagebox.showwarning("Input Error", "Please enter a GitHub username.")
            return

        # Clear previous data
        self.repo_listbox.delete(0, tk.END)

        # Base URLs for GitHub REST API V3
        user_url = f"https://github.com{username}"
        repos_url = f"https://github.com{username}/repos?per_page=30&sort=updated"

        try:
            # 1. Fetch Profile Data
            user_response = requests.get(user_url)
            
            if user_response.status_code == 404:
                messagebox.showerror("Not Found", f"User '{username}' does not exist on GitHub.")
                return
            elif user_response.status_code != 200:
                messagebox.showerror("Error", "Failed to retrieve data from GitHub API.")
                return

            user_data = user_response.json()

            # Update Profile Labels
            self.name_label.config(text=f"Name: {user_data.get('name') or user_data.get('login')}")
            self.bio_label.config(text=f"Bio: {user_data.get('bio') or 'No bio available.'}")
            self.stats_label.config(text=f"Public Repos: {user_data.get('public_repos')}  |  Followers: {user_data.get('followers')}")

            # 2. Fetch Repositories
            repos_response = requests.get(repos_url)
            if repos_response.status_code == 200:
                repos_data = repos_response.json()
                for repo in repos_data:
                    repo_name = repo.get("name")
                    repo_lang = repo.get("language")
                    display_text = f"📦 {repo_name} ({repo_lang})" if repo_lang else f"📦 {repo_name}"
                    self.repo_listbox.insert(tk.END, display_text)
            else:
                self.repo_listbox.insert(tk.END, "Could not load repositories.")

        except requests.exceptions.RequestException:
            messagebox.showerror("Connection Error", "Please check your internet connection.")

if __name__ == "__main__":
    root = tk.Tk()
    app = GitHubDataApp(root)
    root.mainloop()
