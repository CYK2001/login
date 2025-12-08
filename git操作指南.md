# Git操作指南

## 问题分析
用户尝试执行以下命令时遇到错误：
```bash
git clone https://github.com/CYK2001/yiyu/代码/Login
```

错误信息：
```
fatal: unable to access 'https://github.com/CYK2001/yiyu/代码/Login/': The requested URL returned error: 400
```

### 根本原因
- GitHub不支持在仓库路径中使用中文字符（如"代码"）
- URL中包含非ASCII字符会导致服务器无法正确解析
- 错误400表示Bad Request，即服务器无法理解请求的URL格式

## 解决方案

### 方案一：将当前项目上传到GitHub（推荐）

#### 1. 初始化Git仓库
```bash
# 进入项目目录
cd f:\Work\Login

# 初始化Git仓库
git init

# 添加所有文件
git add .

# 提交初始版本
git commit -m "Initial commit"
```

#### 2. 在GitHub上创建新仓库
- 登录GitHub，点击右上角"+" -> "New repository"
- 输入仓库名称（如"Login-System"）
- 选择仓库类型（公开/私有）
- 不勾选"Initialize this repository with a README"
- 点击"Create repository"

#### 3. 关联本地仓库并推送
```bash
# 关联远程仓库
git remote add origin https://github.com/CYK2001/Login-System.git

# 推送到GitHub
git push -u origin main
```

### 方案二：克隆正确格式的GitHub仓库
如果需要从GitHub克隆代码，请确保URL格式正确：
- 不包含中文字符
- 使用正确的仓库路径
- 例如：`git clone https://github.com/username/repository-name.git`

## 项目结构说明
当前项目是一个完整的Flask登录系统，包含以下内容：
- `app/` - 主应用目录
- `static/` - 静态文件目录
- `templates/` - 模板文件目录
- `app.py` - 应用入口文件
- `config.py` - 配置文件
- `requirements.txt` - 依赖列表
- `免费部署指南.md` - 部署文档

## 后续操作建议
1. 按照上述步骤将项目上传到GitHub
2. 根据`免费部署指南.md`选择合适的平台部署应用
3. 定期备份代码和数据库
4. 注意项目的安全配置（特别是数据库密码等敏感信息）
