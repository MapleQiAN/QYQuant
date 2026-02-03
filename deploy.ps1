# QYQuant Docker 一键部署脚本 (Windows PowerShell)
# 使用方法: .\deploy.ps1

$ErrorActionPreference = "Stop"

# 颜色输出函数
function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Green
}

function Write-Warn {
    param([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# 检查 Docker 是否安装
function Test-Docker {
    try {
        $null = Get-Command docker -ErrorAction Stop
        $null = docker version -ErrorAction Stop
        Write-Info "Docker 环境检查通过"
        return $true
    }
    catch {
        Write-Error "Docker 未安装或未运行，请先安装并启动 Docker Desktop"
        return $false
    }
}

# 检查并创建 .env 文件
function Test-EnvFile {
    if (-not (Test-Path .env)) {
        Write-Warn ".env 文件不存在，从 .env.example 复制..."
        if (Test-Path .env.example) {
            Copy-Item .env.example .env
            Write-Info "已创建 .env 文件，请修改其中的配置（特别是密码和密钥）"

            $edit = Read-Host "是否现在编辑 .env 文件？(y/n)"
            if ($edit -eq 'y') {
                notepad .env
            }
        }
        else {
            Write-Error ".env.example 文件不存在"
            return $false
        }
    }
    else {
        Write-Info "使用现有的 .env 文件"
    }
    return $true
}

# 构建镜像
function Build-Images {
    Write-Info "开始构建 Docker 镜像（包含前端、后端、Celery 等全部服务）..."
    docker compose build --no-cache
    if ($LASTEXITCODE -ne 0) {
        Write-Error "镜像构建失败"
        exit 1
    }
    Write-Info "镜像构建完成"
}

# 启动服务
function Start-Services {
    Write-Info "启动所有服务（前端、后端、数据库、Redis、Celery）..."
    docker compose up -d

    if ($LASTEXITCODE -ne 0) {
        Write-Error "服务启动失败"
        exit 1
    }

    # 等待服务启动
    Write-Info "等待服务启动..."
    Start-Sleep -Seconds 10

    # 检查服务状态
    Write-Info "服务状态："
    docker compose ps
}

# 初始化数据库
function Initialize-Database {
    Write-Info "初始化数据库..."

    # 运行数据库迁移
    try {
        docker compose exec -T backend flask db upgrade
    }
    catch {
        Write-Warn "数据库迁移失败（可能已经执行过）"
    }

    # 创建默认管理员账号
    try {
        docker compose exec -T backend python -c @"
from app import create_app
from app.extensions import db
from app.models.user import User

app = create_app()
with app.app_context():
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@qyquant.com'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print('默认管理员账号已创建: admin / admin123')
    else:
        print('管理员账号已存在')
"@
    }
    catch {
        Write-Warn "创建管理员账号失败"
    }
}

# 显示访问信息
function Show-AccessInfo {
    $envContent = Get-Content .env
    $frontendPort = ($envContent | Where-Object { $_ -match 'FRONTEND_PORT' }) -split '=' | Select-Object -Last 1
    $backendPort = ($envContent | Where-Object { $_ -match 'BACKEND_PORT' }) -split '=' | Select-Object -Last 1

    if (-not $frontendPort) { $frontendPort = "80" }
    if (-not $backendPort) { $backendPort = "5000" }

    Write-Host ""
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host "       部署完成！" -ForegroundColor Green
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host "前端地址: " -NoNewline
    Write-Host "http://localhost:$frontendPort" -ForegroundColor Green
    Write-Host "后端 API: " -NoNewline
    Write-Host "http://localhost:$backendPort" -ForegroundColor Green
    Write-Host "默认账号: " -NoNewline
    Write-Host "admin / admin123" -ForegroundColor Green
    Write-Host ""
    Write-Warn "生产环境请立即修改默认密码！"
    Write-Host ""
    Write-Host "常用命令："
    Write-Host "  查看日志: " -NoNewline
    Write-Host "docker compose logs -f" -ForegroundColor Green
    Write-Host "  停止服务: " -NoNewline
    Write-Host "docker compose down" -ForegroundColor Green
    Write-Host "  重启服务: " -NoNewline
    Write-Host "docker compose restart" -ForegroundColor Green
    Write-Host "  查看状态: " -NoNewline
    Write-Host "docker compose ps" -ForegroundColor Green
    Write-Host "============================================" -ForegroundColor Cyan
}

# 主流程
function Main {
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host "       QYQuant Docker 一键部署脚本" -ForegroundColor Cyan
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host ""

    if (-not (Test-Docker)) {
        exit 1
    }

    if (-not (Test-EnvFile)) {
        exit 1
    }

    Write-Host ""
    $confirm = Read-Host "是否开始构建和部署？(y/n)"
    if ($confirm -ne 'y') {
        Write-Info "部署已取消"
        exit 0
    }

    Build-Images
    Start-Services
    Initialize-Database
    Show-AccessInfo
}

# 执行主流程
Main
