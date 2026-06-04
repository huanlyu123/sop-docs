#!/usr/bin/env python3
"""
Deploy E:\2026 folder to its own GitHub repository
Usage: python deploy_2026.py
"""

import os
import subprocess
import sys
from pathlib import Path

SOURCE_DIR = Path("E:\\2026")
GH_USER = "huanlyu123"
REPO_NAME = "docs-2026"
GH_PAGES_BRANCH = "gh-pages"

def run(cmd, cwd=None, check=True):
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0 and check:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result.stdout.strip()

def deploy():
    os.chdir(SOURCE_DIR)
    
    if not os.path.exists(".git"):
        run("git init")
        run(f"git remote add origin https://github.com/{GH_USER}/{REPO_NAME}.git")
    
    files = sorted([f for f in SOURCE_DIR.rglob("*") if f.is_file()], key=lambda x: str(x))
    print(f"Found {len(files)} files")
    
    # Generate index.html
    index_html = "<!DOCTYPE html><html><head><meta charset='UTF-8'><title>2026 Docs</title><style>"
    index_html += "body{font-family:-apple-system,sans-serif;max-width:900px;margin:0 auto;padding:20px}"
    index_html += "li{padding:8px 0;border-bottom:1px solid #eee}a{color:#0066cc;text-decoration:none}"
    index_html += "</style></head><body><h1>2026</h1><ul>"
    
    for f in files:
        path_str = str(f.name)
        index_html += f'<li><a href="{path_str}">{path_str}</a></li>'
    
    index_html += "</ul></body></html>"
    
    with open(SOURCE_DIR / "index.html", "w", encoding="utf-8") as f:
        f.write(index_html)
    
    run('git add -A')
    status = run('git status --porcelain')
    if not status:
        print("No changes")
        return
    
    run('git commit -m "Update"')
    
    branches = run('git branch -a')
    if GH_PAGES_BRANCH not in branches:
        run(f'git checkout --orphan {GH_PAGES_BRANCH}')
        run('git rm -rf .')
    else:
        run(f'git checkout {GH_PAGES_BRANCH}')
    
    run(f'git push -u origin {GH_PAGES_BRANCH}')
    print(f"Done! https://{GH_USER}.github.io/{REPO_NAME}/")

if __name__ == "__main__":
    deploy()