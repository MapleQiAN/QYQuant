$ErrorActionPreference = "Stop"

function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Green
}

function Write-Warn {
    param([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Write-Fail {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Test-Docker {
    try {
        $null = Get-Command docker -ErrorAction Stop
        docker compose version | Out-Null
        return $true
    }
    catch {
        Write-Fail "Docker Desktop with Docker Compose v2 is required."
        return $false
    }
}

function Ensure-EnvFile {
    if (-not (Test-Path .env)) {
        Copy-Item .env.example .env
        Write-Warn ".env did not exist. Created it from .env.example."
        Write-Warn "Review SECRET_KEY, JWT_SECRET, FERNET_KEY, CORS_ORIGINS and exposed ports before production use."
    }
}

function Start-Stack {
    Write-Info "Building and starting the QYQuant Docker stack..."
    docker compose up -d --build
}

function Show-AccessInfo {
    $envValues = @{}
    Get-Content .env | ForEach-Object {
        if ($_ -match '^\s*([^#=]+)=(.*)$') {
            $envValues[$matches[1].Trim()] = $matches[2].Trim()
        }
    }

    $frontendPort = $envValues["FRONTEND_PORT"]
    $backendPort = $envValues["BACKEND_PORT"]
    if (-not $frontendPort) { $frontendPort = "58888" }
    if (-not $backendPort) { $backendPort = "59999" }

    Write-Host ""
    Write-Info "Frontend: http://localhost:$frontendPort"
    Write-Info "Backend API: http://localhost:$backendPort"
    Write-Info "Swagger UI: http://localhost:$backendPort/api/docs"
    Write-Host ""
    Write-Info "Useful commands:"
    Write-Host "  docker compose ps"
    Write-Host "  docker compose logs -f backend"
    Write-Host "  docker compose logs -f frontend"
    Write-Host "  docker compose down"
}

if (-not (Test-Docker)) {
    exit 1
}

Ensure-EnvFile
Start-Stack
Show-AccessInfo
