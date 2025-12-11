# GitHub 上传指南

## 步骤 1: 安装 Git

如果您的系统还没有安装 Git，请按照以下步骤安装：

### 方法 1: 从官网下载（推荐）
1. 访问 https://git-scm.com/download/win
2. 下载最新版本的 Git for Windows
3. 运行安装程序，使用默认设置即可
4. 安装完成后，**重新打开 PowerShell 或命令提示符**

### 方法 2: 使用 Chocolatey（如果已安装）
```powershell
choco install git
```

## 步骤 2: 配置 Git（首次使用）

安装 Git 后，需要配置您的用户名和邮箱：

```bash
git config --global user.name "您的用户名"
git config --global user.email "您的邮箱"
```

## 步骤 3: 创建 GitHub 仓库

1. 登录 GitHub (https://github.com)
2. 点击右上角的 "+" 号，选择 "New repository"
3. 仓库名称填写：`dnd-agent`
4. 选择 Public 或 Private（根据您的需要）
5. **不要**勾选 "Initialize this repository with a README"（因为我们已经有了代码）
6. 点击 "Create repository"

## 步骤 4: 运行上传脚本

在 PowerShell 中运行以下命令：

```powershell
.\upload_to_github.ps1
```

或者按照下面的手动步骤操作。

## 手动步骤（如果脚本无法运行）

### 1. 初始化 Git 仓库
```bash
git init
```

### 2. 添加所有文件
```bash
git add .
```

### 3. 创建初始提交
```bash
git commit -m "Initial commit: DnD Agent project"
```

### 4. 添加远程仓库
```bash
git remote add origin https://github.com/您的用户名/dnd-agent.git
```

### 5. 推送代码
```bash
git branch -M main
git push -u origin main
```

## 注意事项

- 如果这是您第一次使用 GitHub，可能需要输入用户名和密码（或使用 Personal Access Token）
- 如果遇到认证问题，GitHub 现在要求使用 Personal Access Token 而不是密码
- 创建 Personal Access Token: GitHub Settings > Developer settings > Personal access tokens > Tokens (classic)

