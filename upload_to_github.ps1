# GitHub 上传脚本
# 此脚本将帮助您将项目上传到 GitHub

Write-Host "=== GitHub 上传脚本 ===" -ForegroundColor Green
Write-Host ""

# 检查 Git 是否安装
Write-Host "检查 Git 安装状态..." -ForegroundColor Yellow
try {
    $gitVersion = git --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Git 已安装: $gitVersion" -ForegroundColor Green
    } else {
        throw "Git 未安装"
    }
} catch {
    Write-Host "✗ Git 未安装或不在 PATH 中" -ForegroundColor Red
    Write-Host ""
    Write-Host "请先安装 Git:" -ForegroundColor Yellow
    Write-Host "1. 访问 https://git-scm.com/download/win" -ForegroundColor Cyan
    Write-Host "2. 下载并安装 Git for Windows" -ForegroundColor Cyan
    Write-Host "3. 安装完成后，重新运行此脚本" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "或者查看 GITHUB_UPLOAD_GUIDE.md 获取详细说明" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# 检查是否已经是 Git 仓库
if (Test-Path ".git") {
    Write-Host "检测到已存在的 Git 仓库" -ForegroundColor Yellow
    $continue = Read-Host "是否继续？(y/n)"
    if ($continue -ne "y" -and $continue -ne "Y") {
        Write-Host "操作已取消" -ForegroundColor Yellow
        exit 0
    }
} else {
    Write-Host "初始化 Git 仓库..." -ForegroundColor Yellow
    git init
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ Git 初始化失败" -ForegroundColor Red
        exit 1
    }
    Write-Host "✓ Git 仓库初始化成功" -ForegroundColor Green
}

Write-Host ""

# 检查远程仓库配置
$remoteUrl = git remote get-url origin 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "检测到远程仓库: $remoteUrl" -ForegroundColor Yellow
    $changeRemote = Read-Host "是否更改远程仓库 URL？(y/n)"
    if ($changeRemote -eq "y" -or $changeRemote -eq "Y") {
        $newUrl = Read-Host "请输入新的仓库 URL (例如: https://github.com/用户名/dnd-agent.git)"
        git remote set-url origin $newUrl
        Write-Host "✓ 远程仓库 URL 已更新" -ForegroundColor Green
    }
} else {
    Write-Host "未检测到远程仓库" -ForegroundColor Yellow
    $addRemote = Read-Host "是否添加远程仓库？(y/n)"
    if ($addRemote -eq "y" -or $addRemote -eq "Y") {
        $repoUrl = Read-Host "请输入仓库 URL (例如: https://github.com/用户名/dnd-agent.git)"
        git remote add origin $repoUrl
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ 远程仓库已添加" -ForegroundColor Green
        } else {
            Write-Host "✗ 添加远程仓库失败" -ForegroundColor Red
            exit 1
        }
    }
}

Write-Host ""

# 添加文件
Write-Host "添加文件到 Git..." -ForegroundColor Yellow
git add .
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ 添加文件失败" -ForegroundColor Red
    exit 1
}
Write-Host "✓ 文件已添加" -ForegroundColor Green

Write-Host ""

# 检查是否有未提交的更改
$status = git status --porcelain
if ($status) {
    Write-Host "创建提交..." -ForegroundColor Yellow
    $commitMessage = Read-Host "请输入提交信息 (直接回车使用默认信息)"
    if ([string]::IsNullOrWhiteSpace($commitMessage)) {
        $commitMessage = "Initial commit: DnD Agent project"
    }
    git commit -m $commitMessage
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ 提交失败" -ForegroundColor Red
        exit 1
    }
    Write-Host "✓ 提交成功" -ForegroundColor Green
} else {
    Write-Host "没有需要提交的更改" -ForegroundColor Yellow
}

Write-Host ""

# 检查当前分支
$currentBranch = git branch --show-current
if ([string]::IsNullOrWhiteSpace($currentBranch)) {
    Write-Host "创建 main 分支..." -ForegroundColor Yellow
    git branch -M main
}

Write-Host ""

# 推送到 GitHub
Write-Host "准备推送到 GitHub..." -ForegroundColor Yellow
Write-Host "注意: 如果这是第一次推送，您可能需要输入 GitHub 用户名和 Personal Access Token" -ForegroundColor Cyan
Write-Host ""
$push = Read-Host "是否现在推送到 GitHub？(y/n)"
if ($push -eq "y" -or $push -eq "Y") {
    Write-Host "正在推送..." -ForegroundColor Yellow
    git push -u origin main
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✓ 代码已成功推送到 GitHub！" -ForegroundColor Green
        Write-Host ""
        $remoteUrl = git remote get-url origin
        Write-Host "仓库地址: $remoteUrl" -ForegroundColor Cyan
    } else {
        Write-Host ""
        Write-Host "✗ 推送失败" -ForegroundColor Red
        Write-Host "可能的原因:" -ForegroundColor Yellow
        Write-Host "1. 认证失败 - 请使用 Personal Access Token 而不是密码" -ForegroundColor Cyan
        Write-Host "2. 仓库不存在 - 请先在 GitHub 上创建仓库" -ForegroundColor Cyan
        Write-Host "3. 网络问题" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "请查看 GITHUB_UPLOAD_GUIDE.md 获取详细帮助" -ForegroundColor Yellow
    }
} else {
    Write-Host "跳过推送。您可以稍后使用以下命令推送:" -ForegroundColor Yellow
    Write-Host "  git push -u origin main" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "=== 完成 ===" -ForegroundColor Green

