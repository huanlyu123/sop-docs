#!/usr/bin/env python3
"""
Deploy E:\2026 folder to GitHub Pages
Usage: python deploy.py
"""

import os
import subprocess
import sys
import shutil
from pathlib import Path

REPO_DIR = Path(__file__).parent.resolve()
GH_USER = "huanlyu123"
REPO_NAME = "sop-docs"
GH_PAGES_BRANCH = "gh-pages"

def run(cmd, cwd=None):
    """Run shell command."""
    result = subprocess.run(
        cmd, shell=True, cwd=cwd,
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result.stdout.strip()

def deploy():
    # 检查git配置
    os.chdir(REPO_DIR)
    
    # 初始化git仓库（如果需要）
    if not os.path.exists(".git"):
        run("git init")
        run(f"git remote add origin https://github.com/{GH_USER}/{REPO_NAME}.git")
    
    # 创建HTML文件索引
    html_files = []
    for ext in [".html", ".htm", ".txt", ".md"]:
        html_files.extend(REPO_DIR.rglob(f"*{ext}"))
    
    # 生成index.html
    files = sorted([f for f in REPO_DIR.rglob("*") if f.is_file()], key=lambda x: str(x))
    
    index_html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>SOP Docs</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; }
        h1 { color: #333; }
        ul { list-style: none; padding: 0; }
        li { padding: 8px 0; border-bottom: 1px solid #eee; }
        a { color: #0066cc; text-decoration: none; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <h1>SOP Docs</h1>
    <ul>
"""
    for f in files:
        path_str = str(f.relative_to(REPO_DIR)).replace("\\", "/")
        index_html += f'        <li><a href="{path_str}">{path_str}</a></li>\n'
    
    index_html += """    </ul>
</body>
</html>
"""
    
    with open(REPO_DIR / "index.html", "w", encoding="utf-8") as f:
        f.write(index_html)
    
    print(f"Generated index.html with {len(files)} files")
    
    # Git操作 - 推送到gh-pages分支
    # 添加所有文件
    run('git add -A')
    
    # 检查是否有变化
    status = run('git status --porcelain')
    if not status:
        print("No changes to commit")
        return
    
    # 提交
    run('git commit -m "Update docs"')
    
    # 推送到gh-pages分支
    # 先检查分支是否存在
    branches = run('git branch -a')
    if GH_PAGES_BRANCH not in branches:
        run(f'git checkout --orphan {GH_PAGES_BRANCH}')
    else:
        run(f'git checkout {GH_PAGES_BRANCH}')
    
    # 从main切回gh-pages并合并
    run(f'git merge main --no-edit')
    
    # 推送到远程
    token = os.environ.get("GH_TOKEN")
    if token:
        remote_url = f"https://{token}@github.com/{GH_USER}/{REPO_NAME}.git"
        run(f'git push -u {remote_url}')
    else:
        run(f'git push -u origin {GH_PAGES_BRANCH}')
    
    print(f"Deployed! Visit: https://{GH_USER}.github.io/{REPO_NAME}/")

if __name__ == "__main__":
    deploy()