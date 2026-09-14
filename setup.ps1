#!/usr/bin/env pwsh
# ═══════════════════════════════════════════════════════════════════════════
#  TrustMoss — Fully Automated Contributor Setup Script
#  Compatible: Windows (PowerShell 5.1+) | macOS | Linux (pwsh)
#
#  Usage:
#    Windows (run as Admin for Docker install):
#      powershell -ExecutionPolicy Bypass -File setup.ps1
#
#    macOS / Linux:
#      pwsh setup.ps1
#      -- or --
#      chmod +x setup.ps1 && ./setup.ps1
#
#  What it does:
#    1. Detects OS
#    2. Checks / installs Docker Desktop (Windows/macOS) or Docker Engine (Linux)
#    3. Verifies Docker Compose v2 is available
#    4. Copies .env files from .env.example if missing
#    5. Prompts for required API keys (GROQ + Moss) and writes them to .env
#    6. Builds Docker images
#    7. Starts all containers (detached)
#    8. Runs a health check and opens the browser
# ═══════════════════════════════════════════════════════════════════════════

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ── Output helpers ──────────────────────────────────────────────────────
function Write-Header  { param([string]$msg) Write-Host "`n[ $msg ]" -ForegroundColor Cyan  }
function Write-Step    { param([string]$msg) Write-Host "  >> $msg"   -ForegroundColor White }
function Write-Success { param([string]$msg) Write-Host "  OK $msg"   -ForegroundColor Green }
function Write-Warn    { param([string]$msg) Write-Host "  !! $msg"   -ForegroundColor Yellow }
function Write-Fail    { param([string]$msg) Write-Host "  FAIL $msg"   -ForegroundColor Red; exit 1 }

# ─────────────────────────────────────────────────────────────────────────
# SECTION 0 — Banner
# ─────────────────────────────────────────────────────────────────────────
Clear-Host
Write-Host @"
  ████████╗██████╗ ██╗   ██╗███████╗████████╗███╗   ███╗ ██████╗ ███████╗███████╗
  ╚══██╔══╝██╔══██╗██║   ██║██╔════╝╚══██╔══╝████╗ ████║██╔═══██╗██╔════╝██╔════╝
     ██║   ██████╔╝██║   ██║███████╗   ██║   ██╔████╔██║██║   ██║███████╗███████╗
     ██║   ██╔══██╗██║   ██║╚════██║   ██║   ██║╚██╔╝██║██║   ██║╚════██║╚════██║
     ██║   ██║  ██║╚██████╔╝███████║   ██║   ██║ ╚═╝ ██║╚██████╔╝███████║███████║
     ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚══════╝   ╚═╝   ╚═╝     ╚═╝ ╚═════╝ ╚══════╝╚══════╝
"@ -ForegroundColor Magenta

Write-Host "  Real-Time Trust Gateway for AI Agents  |  Contributor Setup  v1.0" -ForegroundColor DarkCyan
Write-Host "  ─────────────────────────────────────────────────────────────────" -ForegroundColor DarkGray

# ─────────────────────────────────────────────────────────────────────────
# SECTION 1 — Detect OS
# ─────────────────────────────────────────────────────────────────────────
Write-Header "Detecting Operating System"

$OS = if ($IsWindows)       { "Windows" }
      elseif ($IsMacOS)     { "macOS"   }
      elseif ($IsLinux)     { "Linux"   }
      else                  { "Unknown" }

Write-Success "Detected: $OS ($([System.Runtime.InteropServices.RuntimeInformation]::OSDescription))"

# Script root (folder containing this file)
$REPO_ROOT = $PSScriptRoot
if (-not $REPO_ROOT) { $REPO_ROOT = (Get-Location).Path }

# ─────────────────────────────────────────────────────────────────────────
# SECTION 2 — Check / Install Docker
# ─────────────────────────────────────────────────────────────────────────
Write-Header "Checking Docker"

function Test-Command { param([string]$cmd) return (Get-Command $cmd -ErrorAction SilentlyContinue) -ne $null }

if (-not (Test-Command "docker")) {
    Write-Warn "Docker not found. Attempting automated install..."

    switch ($OS) {
        "Windows" {
            Write-Step "Downloading Docker Desktop for Windows..."
            $installer = "$env:TEMP\DockerDesktopInstaller.exe"
            Invoke-WebRequest -Uri "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe" `
                              -OutFile $installer -UseBasicParsing
            Write-Step "Running Docker Desktop installer (this may take a few minutes)..."
            Start-Process -FilePath $installer -ArgumentList "install", "--quiet", "--accept-license" -Wait
            $env:Path += ";$env:ProgramFiles\Docker\Docker\resources\bin"
            Write-Success "Docker Desktop installed. You may need to restart your terminal."
        }
        "macOS" {
            if (Test-Command "brew") {
                Write-Step "Installing Docker Desktop via Homebrew..."
                brew install --cask docker
            } else {
                Write-Fail "Homebrew not found. Install it first: https://brew.sh, then re-run this script."
            }
        }
        "Linux" {
            Write-Step "Installing Docker Engine via official convenience script..."
            Invoke-WebRequest -Uri "https://get.docker.com" -UseBasicParsing | Select-Object -ExpandProperty Content | bash
            Write-Step "Adding current user to docker group..."
            $user = (& whoami)
            sudo usermod -aG docker $user
            Write-Warn "You must log out and back in (or run: newgrp docker) for group changes to take effect."
            Write-Step "Starting Docker service..."
            sudo systemctl enable docker
            sudo systemctl start docker
        }
        default { Write-Fail "Unsupported OS. Install Docker manually: https://docs.docker.com/get-docker/" }
    }
} else {
    $dockerVersion = (docker version --format '{{.Server.Version}}' 2>$null)
    Write-Success "Docker found: v$dockerVersion"
}

# ─────────────────────────────────────────────────────────────────────────
# SECTION 3 — Check Docker Compose v2
# ─────────────────────────────────────────────────────────────────────────
Write-Header "Checking Docker Compose"

$composeCmd = $null

# Try `docker compose` (v2 plugin — preferred)
try {
    $composeVersion = (docker compose version --short 2>$null)
    if ($composeVersion) {
        $composeCmd = "docker compose"
        Write-Success "Docker Compose v2 (plugin): $composeVersion"
    }
} catch {}

# Fallback: standalone docker-compose (v1 legacy)
if (-not $composeCmd -and (Test-Command "docker-compose")) {
    $composeCmd = "docker-compose"
    $v = (docker-compose version --short 2>$null)
    Write-Warn "Using legacy docker-compose v1: $v (consider upgrading Docker)"
}

if (-not $composeCmd) {
    Write-Fail "Docker Compose not available. Ensure Docker Desktop is running, or install Compose v2: https://docs.docker.com/compose/install/"
}

# ─────────────────────────────────────────────────────────────────────────
# SECTION 4 — Verify Docker daemon is running
# ─────────────────────────────────────────────────────────────────────────
Write-Header "Verifying Docker Daemon"

try {
    docker info *>$null 2>&1
    Write-Success "Docker daemon is running."
} catch {
    Write-Fail "Docker daemon is not running. Start Docker Desktop (Windows/macOS) or run: sudo systemctl start docker (Linux)"
}

# ─────────────────────────────────────────────────────────────────────────
# SECTION 5 — Environment Configuration
# ─────────────────────────────────────────────────────────────────────────
Write-Header "Environment Configuration"

# ── Root .env (ports & shared config) ───────────────────────────────────
$rootEnv     = Join-Path $REPO_ROOT ".env"
$rootEnvEx   = Join-Path $REPO_ROOT ".env.example"

if (-not (Test-Path $rootEnv)) {
    Copy-Item $rootEnvEx $rootEnv
    Write-Success "Created $rootEnv from .env.example"
} else {
    Write-Success "$rootEnv already exists — skipping copy."
}

# ── API .env (secret keys) ───────────────────────────────────────────────
$apiEnv    = Join-Path $REPO_ROOT "apps/api/.env"
$apiEnvEx  = Join-Path $REPO_ROOT "apps/api/.env.example"

if (-not (Test-Path $apiEnv)) {
    Copy-Item $apiEnvEx $apiEnv
    Write-Success "Created $apiEnv from .env.example"
} else {
    Write-Success "$apiEnv already exists — skipping copy."
}

# ── Prompt for missing API keys ──────────────────────────────────────────
Write-Step "Checking for required API keys..."

function Get-EnvValue {
    param([string]$file, [string]$key)
    if (Test-Path $file) {
        $line = Get-Content $file | Where-Object { $_ -match "^$key=" } | Select-Object -First 1
        if ($line) { return ($line -split "=", 2)[1].Trim() }
    }
    return ""
}

function Set-EnvValue {
    param([string]$file, [string]$key, [string]$value)
    $content = if (Test-Path $file) { Get-Content $file } else { @() }
    $updated = $false
    $newContent = $content | ForEach-Object {
        if ($_ -match "^$key=") { "$key=$value"; $updated = $true }
        else { $_ }
    }
    if (-not $updated) { $newContent += "$key=$value" }
    Set-Content $file $newContent -Encoding UTF8
}

# Check GROQ_API_KEY
$groqKey = Get-EnvValue $apiEnv "GROQ_API_KEY"
if (-not $groqKey -or $groqKey -eq "your_groq_api_key_here") {
    Write-Host ""
    Write-Warn "GROQ_API_KEY is not set."
    Write-Host "  Get a free key at: https://console.groq.com/keys" -ForegroundColor DarkCyan
    $groqKey = Read-Host "  Enter your Groq API Key (or press Enter to skip)"
    if ($groqKey) {
        Set-EnvValue $apiEnv "GROQ_API_KEY" $groqKey
        Write-Success "GROQ_API_KEY saved to $apiEnv"
    } else {
        Write-Warn "Skipped. The API will use mock mode until GROQ_API_KEY is set."
    }
} else {
    Write-Success "GROQ_API_KEY is already configured."
}

# Check MOSS_PROJECT_KEY
$mossKey = Get-EnvValue $apiEnv "MOSS_PROJECT_KEY"
if (-not $mossKey -or $mossKey -eq "your_moss_api_key_here") {
    Write-Host ""
    Write-Warn "MOSS_PROJECT_KEY is not set."
    Write-Host "  Get your key from: https://moss.ai/dashboard" -ForegroundColor DarkCyan
    $mossKey = Read-Host "  Enter your Moss Project Key (or press Enter to skip)"
    if ($mossKey) {
        Set-EnvValue $apiEnv "MOSS_PROJECT_KEY" $mossKey
        Write-Success "MOSS_PROJECT_KEY saved to $apiEnv"
    } else {
        Write-Warn "Skipped. The API will use mock Moss retrieval until the key is set."
    }
} else {
    Write-Success "MOSS_PROJECT_KEY is already configured."
}

# Check MOSS_PROJECT_ID
$mossId = Get-EnvValue $apiEnv "MOSS_PROJECT_ID"
if (-not $mossId -or $mossId -eq "") {
    Write-Host ""
    $mossId = Read-Host "  Enter your Moss Project ID (or press Enter to skip)"
    if ($mossId) {
        Set-EnvValue $apiEnv "MOSS_PROJECT_ID" $mossId
        Write-Success "MOSS_PROJECT_ID saved."
    }
}

# ─────────────────────────────────────────────────────────────────────────
# SECTION 6 — Build Docker Images
# ─────────────────────────────────────────────────────────────────────────
Write-Header "Building Docker Images"
Write-Step "Running: $composeCmd build (this takes 1-3 min on first run)..."

Set-Location $REPO_ROOT
& $composeCmd.Split(" ")[0] ($composeCmd.Split(" ") | Select-Object -Skip 1) build

if ($LASTEXITCODE -ne 0) {
    Write-Fail "Docker build failed. Check the output above for errors."
}
Write-Success "All images built successfully."

# ─────────────────────────────────────────────────────────────────────────
# SECTION 7 — Start Containers
# ─────────────────────────────────────────────────────────────────────────
Write-Header "Starting TrustMoss Services"
Write-Step "Running: $composeCmd up -d"

& $composeCmd.Split(" ")[0] ($composeCmd.Split(" ") | Select-Object -Skip 1) up -d

if ($LASTEXITCODE -ne 0) {
    Write-Fail "Failed to start containers. Run: $composeCmd logs for details."
}
Write-Success "Containers started in detached mode."

# ─────────────────────────────────────────────────────────────────────────
# SECTION 8 — Health Check
# ─────────────────────────────────────────────────────────────────────────
Write-Header "Running Health Check"

$apiPort = Get-EnvValue $rootEnv "API_PORT"
if (-not $apiPort) { $apiPort = "8000" }
$webPort = Get-EnvValue $rootEnv "WEB_PORT"
if (-not $webPort) { $webPort = "3000" }

Write-Step "Waiting for API to become healthy..."
$maxAttempts = 12
$attempt = 0
$healthy = $false

while ($attempt -lt $maxAttempts -and -not $healthy) {
    Start-Sleep -Seconds 5
    $attempt++
    try {
        $resp = Invoke-WebRequest -Uri "http://localhost:$apiPort/health" -UseBasicParsing -TimeoutSec 5 -ErrorAction SilentlyContinue
        if ($resp.StatusCode -eq 200) {
            $healthy = $true
        }
    } catch {}
    Write-Step "Attempt $attempt/$maxAttempts..."
}

if ($healthy) {
    Write-Success "API is healthy at http://localhost:$apiPort"
} else {
    Write-Warn "API health check timed out. It may still be starting. Check: docker compose logs api"
}

# ─────────────────────────────────────────────────────────────────────────
# SECTION 9 — Open Browser
# ─────────────────────────────────────────────────────────────────────────
Write-Header "Opening TrustMoss Dashboard"

$dashboardUrl = "http://localhost:$webPort"
$apiDocsUrl   = "http://localhost:$apiPort/docs"

Write-Step "Dashboard URL : $dashboardUrl"
Write-Step "API Docs URL  : $apiDocsUrl"

try {
    switch ($OS) {
        "Windows" { Start-Process $dashboardUrl }
        "macOS"   { open $dashboardUrl }
        "Linux"   {
            if (Test-Command "xdg-open") { xdg-open $dashboardUrl }
            elseif (Test-Command "sensible-browser") { sensible-browser $dashboardUrl }
        }
    }
    Write-Success "Browser opened."
} catch {
    Write-Warn "Could not open browser automatically. Navigate to: $dashboardUrl"
}

# ─────────────────────────────────────────────────────────────────────────
# SECTION 10 — Summary
# ─────────────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  TrustMoss is running.                                   " -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Dashboard  ->  http://localhost:$webPort" -ForegroundColor White
Write-Host "  API Docs   ->  http://localhost:$apiPort/docs" -ForegroundColor White
Write-Host "  Health     ->  http://localhost:$apiPort/health" -ForegroundColor White
Write-Host ""
Write-Host "  Useful commands:" -ForegroundColor DarkGray
Write-Host "    $composeCmd logs -f api     # stream API logs" -ForegroundColor DarkGray
Write-Host "    $composeCmd ps              # container status" -ForegroundColor DarkGray
Write-Host "    $composeCmd down            # stop everything" -ForegroundColor DarkGray
Write-Host "    $composeCmd up --build      # rebuild and restart" -ForegroundColor DarkGray
Write-Host ""
