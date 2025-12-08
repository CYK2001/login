#!/usr/bin/env python3
"""
Flask应用自动化部署脚本
支持将应用部署到Render平台
"""

import os
import sys
import subprocess
import json
import requests
from pathlib import Path


def run_command(command, cwd=None):
    """执行命令并返回结果"""
    print(f"执行命令: {command}")
    try:
        result = subprocess.run(
            command, shell=True, cwd=cwd, 
            capture_output=True, text=True, 
            check=True
        )
        print(f"命令执行成功:\n{result.stdout}")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"命令执行失败:\n{e.stderr}")
        return None


def create_github_repo(repo_name, github_token):
    """创建GitHub仓库"""
    print(f"创建GitHub仓库: {repo_name}")
    url = "https://api.github.com/user/repos"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "name": repo_name,
        "private": False,
        "auto_init": False
    }
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 201:
        print(f"GitHub仓库创建成功: {response.json()['clone_url']}")
        return response.json()['clone_url']
    else:
        print(f"GitHub仓库创建失败: {response.status_code} {response.text}")
        return None


def init_git_repo(project_dir):
    """初始化Git仓库"""
    print("初始化Git仓库...")
    
    # 检查是否已经是Git仓库
    if not os.path.exists(os.path.join(project_dir, ".git")):
        run_command("git init", cwd=project_dir)
        run_command("git config user.name 'Automated Deploy'", cwd=project_dir)
        run_command("git config user.email 'deploy@example.com'", cwd=project_dir)
    else:
        print("Git仓库已经存在")


def create_render_service(service_name, github_repo, render_token):
    """在Render上创建Web服务"""
    print(f"在Render上创建Web服务: {service_name}")
    url = "https://api.render.com/v1/services"
    headers = {
        "Authorization": f"Bearer {render_token}",
        "Content-Type": "application/json"
    }
    data = {
        "name": service_name,
        "type": "web",
        "repo": github_repo,
        "branch": "main",
        "region": "ohio",
        "buildCommand": "pip install -r requirements.txt",
        "startCommand": "gunicorn app:app",
        "envVars": [
            {"key": "FLASK_ENV", "value": "production"},
            {"key": "FLASK_SECRET_KEY", "value": os.urandom(24).hex()}
        ],
        "plan": "free"
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 201:
        print(f"Render服务创建成功: {response.json()['service']['url']}")
        return response.json()['service']['id'], response.json()['service']['url']
    else:
        print(f"Render服务创建失败: {response.status_code} {response.text}")
        return None, None


def update_render_env_vars(service_id, render_token, env_vars):
    """更新Render服务的环境变量"""
    print(f"更新Render服务环境变量: {service_id}")
    url = f"https://api.render.com/v1/services/{service_id}/env-vars"
    headers = {
        "Authorization": f"Bearer {render_token}",
        "Content-Type": "application/json"
    }
    
    # 获取当前环境变量
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"获取环境变量失败: {response.status_code} {response.text}")
        return False
    
    current_env_vars = response.json()
    new_env_vars = current_env_vars.copy()
    
    # 更新或添加环境变量
    for key, value in env_vars.items():
        found = False
        for i, env_var in enumerate(new_env_vars):
            if env_var['key'] == key:
                new_env_vars[i]['value'] = value
                found = True
                break
        if not found:
            new_env_vars.append({"key": key, "value": value})
    
    # 更新环境变量
    response = requests.put(url, headers=headers, json=new_env_vars)
    
    if response.status_code == 200:
        print("环境变量更新成功")
        return True
    else:
        print(f"环境变量更新失败: {response.status_code} {response.text}")
        return False


def main():
    """主函数"""
    print("=== Flask应用自动化部署工具 ===")
    
    # 获取项目目录
    project_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"项目目录: {project_dir}")
    
    # 获取用户输入
    repo_name = input("请输入GitHub仓库名称: ")
    github_token = input("请输入GitHub Personal Access Token: ")
    render_token = input("请输入Render API Token: ")
    service_name = input("请输入Render服务名称 (默认: login-system): ") or "login-system"
    
    # 创建.gitignore文件（如果不存在）
    gitignore_path = os.path.join(project_dir, ".gitignore")
    if not os.path.exists(gitignore_path):
        print("创建.gitignore文件...")
        with open(gitignore_path, "w") as f:
            f.write("""
# Virtual environments
venv/
env/

# Python cache files
__pycache__/
*.pyc

# Environment variables
.env
.env.local
.env.*.local

# Logs
logs/
*.log

# Uploads
static/uploads/
app/static/uploads/

# IDE files
.idea/
.vscode/
*.swp
*.swo
*~

# OS files
.DS_Store
Thumbs.db

# Build files
build/
dist/
*.egg-info/

# Database files
*.db
*.sqlite3
*.sql

# Temporary files
*.tmp
*.temp
""")
    
    # 创建Procfile文件（如果不存在）
    procfile_path = os.path.join(project_dir, "Procfile")
    if not os.path.exists(procfile_path):
        print("创建Procfile文件...")
        with open(procfile_path, "w") as f:
            f.write("web: gunicorn app:app\n")
    
    # 初始化Git仓库
    init_git_repo(project_dir)
    
    # 创建GitHub仓库
    github_repo = create_github_repo(repo_name, github_token)
    if not github_repo:
        print("无法创建GitHub仓库，部署失败")
        return
    
    # 提交代码
    run_command("git add .", cwd=project_dir)
    run_command("git commit -m 'Initial commit for deployment'", cwd=project_dir)
    run_command(f"git remote add origin {github_repo}", cwd=project_dir)
    run_command("git branch -M main", cwd=project_dir)
    run_command("git push -u origin main", cwd=project_dir)
    
    # 在Render上创建服务
    service_id, service_url = create_render_service(service_name, github_repo, render_token)
    if not service_id:
        print("无法创建Render服务，部署失败")
        return
    
    # 更新环境变量（如果需要）
    # 这里可以根据需要添加更多环境变量
    env_vars = {
        "FLASK_ENV": "production",
        "FLASK_SECRET_KEY": os.urandom(24).hex()
    }
    update_render_env_vars(service_id, render_token, env_vars)
    
    print("\n=== 部署完成 ===")
    print(f"GitHub仓库: {github_repo}")
    print(f"Render服务: {service_url}")
    print("\n注意:")
    print("1. 您需要在Render控制台中配置数据库连接信息")
    print("2. 首次部署可能需要几分钟时间")
    print("3. 部署完成后可以访问: {service_url}")


if __name__ == "__main__":
    main()
