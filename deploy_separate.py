#!/usr/bin/env python3
"""
Create repos and deploy E:\2026, E:\2025, E:\2024 to separate GitHub repos
"""

import os
import subprocess
import sys
import requests
from pathlib import Path

# Configuration
GH_USER = "huanlyu123"
DEPLOYMENTS = [
    ("E:\\2026", "docs-2026"),
    ("E:\\2025", "docs-2025"),
    ("E:\\2024", "docs-2024"),
]

def run(cmd, cwd=None):
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
    return result.stdout.strip()

def create_repo(name, token):
    """Create repo via GitHub API"""
    url = f"https://api.github.com/user/repos"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    data = {"name": name, "private": False}
    resp = requests.post(url, headers=headers, json=data)
    if resp.status_code == 201:
        print(f"Created repo: {name}")
    elif resp.status_code == 422:
        print(f"Repo already exists: {name}")
    else:
        print(f"Error creating repo: {resp.text}")

def deploy_folder(folder_path, repo_name, token):
    """Deploy folder to its own repo"""
    source_dir = Path(folder_path)
    if not source_dir.exists():
        print(f"Folder not found: {folder_path}")
        return
    
    os.chdir(source_dir)
    
    # Init git if needed
    if not os.path.exists(".git"):
        run("git init")
        run(f"git remote add origin https://{GH_USER}:{token}@github.com/{GH_USER}/{repo_name}.git")
    
    # Find files
    files = [f for f in source_dir.rglob("*") if f.is_file()]
    print(f"Found {len(files)} files in {source_dir.name}")
    
    # Generate index.html
    index_html = f"<!DOCTYPE html><html><head><meta charset='UTF-8'><title>{source_dir.name}</title>"
    index_html += "<style>body{font-family:-apple-system,sans-serif;max-width:900px;margin:0 auto;padding:20px}"
    index_html += "li{padding:8px 0;border-bottom:1px solid #eee}a{color:#0066cc;text-decoration:none}</style>"
    index_html += f"</head><body><h1>{source_dir.name}</h1><ul>"
    
    for f in files:
        index_html += f'<li><a href="{f.name}">{f.name}</a></li>'
    
    index_html += "</ul></body></html>"
    
    with open(source_dir / "index.html", "w", encoding="utf-8") as f:
        f.write(index_html)
    
    # Git operations
    run('git add -A')
    status = run('git status --porcelain')
    if not status:
        print("No changes")
        return
    
    run('git commit -m "Update"')
    run(f'git push -u origin gh-pages')
    print(f"Deployed! https://{GH_USER}.github.io/{repo_name}/")

def main():
    # Get token
    token = os.environ.get("GH_TOKEN")
    if not token:
        print("Please set GH_TOKEN environment variable")
        return
    
    # Create repos
    print("Creating repos...")
    for folder, repo_name in DEPLOYMENTS:
        create_repo(repo_name, token)
    
    # Deploy each folder
    print("\nDeploying folders...")
    for folder, repo_name in DEPLOYMENTS:
        print(f"\nDeploying {folder} -> {repo_name}")
        deploy_folder(folder, repo_name, token)

if __name__ == "__main__":
    main()