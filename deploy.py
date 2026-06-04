#!/usr/bin/env python3
"""
Deploy E:\2026, E:\2025, E:\2024 folders to GitHub Pages
Usage: python deploy.py
"""

import os
import subprocess
import sys
from pathlib import Path

# 配置要上传的文件夹
SOURCE_DIRS = [
    Path("E:\\2026"),
    Path("E:\\2025"),
    Path("E:\\2024"),
]

REPO_DIR = Path(__file__).parent.resolve()
GH_USER = "huanlyu123"
REPO_NAME = "sop-docs"
GH_PAGES_BRANCH = "gh-pages"

def run(cmd, cwd=None, check=True):
    """Run shell command."""
    result = subprocess.run(
        cmd, shell=True, cwd=cwd,
        capture_output=True, text=True
    )
    if result.returncode != 0 and check:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result.stdout.strip()

def deploy():
    os.chdir(REPO_DIR)
    
    # 初始化git仓库（如果需要）
    if not os.path.exists(".git"):
        run("git init")
        run(f"git remote add origin https://github.com/{GH_USER}/{REPO_NAME}.git")
    
    # 收集所有文件
    all_files = []
    for source_dir in SOURCE_DIRS:
        if source_dir.exists():
            files = sorted([f for f in source_dir.rglob("*") if f.is_file()], key=lambda x: str(x))
            all_files.extend(files)
            print(f"Found {len(files)} files in {source_dir}")
    
    # 生成index.html
    index_html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>SOP Docs</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; }
        h1 { color: #333; }
        h2 { color: #666; margin-top: 30px; }
        ul { list-style: none; padding: 0; }
        li { padding: 8px 0; border-bottom: 1px solid #eee; }
        a { color: #0066cc; text-decoration: none; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <h1>SOP Docs</h1>
"""
    
    # 按年份分组
    for source_dir in SOURCE_DIRS:
        if source_dir.exists():
            year_name = source_dir.name
            index_html += f"    <h2>{year_name}</h2>\n    <ul>\n"
            
            files = sorted([f for f in source_dir.rglob("*") if f.is_file()], key=lambda x: str(x))
            for f in files:
                # 使用相对路径
                path_str = str(f.relative_to(source_dir)).replace("\\", "/")
                full_path = f"{source_dir.name}/{path_str}"
                index_html += f'        <li><a href="{full_path}">{full_path}</a></li>\n'
            
            index_html += "    </ul>\n"
    
    index_html += """</body>
</html>"""
    
    with open(REPO_DIR / "index.html", "w", encoding="utf-8") as f:
        f.write(index_html)
    
    print(f"Generated index.html with {len(all_files)} files")
    
    # Git操作
    run('git add -A')
    
    status = run('git status --porcelain')
    if not status:
        print("No changes to commit")
        return
    
    run('git commit -m "Update docs"')
    
    # 检查分支
    branches = run('git branch -a')
    if GH_PAGES_BRANCH not in branches:
        run(f'git checkout --orphan {GH_PAGES_BRANCH}')
        run('git rm -rf .')
    else:
        run(f'git checkout {GH_PAGES_BRANCH}')
    
    # 合并main
    run('git merge main --no-edit', check=False)
    
    # 推送
    token = os.environ.get("GH_TOKEN")
    if token:
        remote_url = f"https://{token}@github.com/{GH_USER}/{REPO_NAME}.git"
        run(f'git push -u {remote_url} {GH_PAGES_BRANCH}')
    else:
        run(f'git push -u origin {GH_PAGES_BRANCH}')
    
    print(f"Deployed! Visit: https://{GH_USER}.github.io/{REPO_NAME}/")

if __name__ == "__main__":
    deploy()