<#
.SYNOPSIS
Starts the local Telegram Mini App development stack on Windows.

.DESCRIPTION
Starts docker compose infrastructure, FastAPI backend, Vite frontend, two
cloudflared quick tunnels, and the Telegram bot in polling mode. Runtime logs
and process state are written to .codex-run.

.EXAMPLE
powershell -ExecutionPolicy Bypass -File .\scripts\start-telegram-dev.ps1

.EXAMPLE
powershell -ExecutionPolicy Bypass -File .\scripts\start-telegram-dev.ps1 -RunMigrations
#>

[CmdletBinding()]
param(
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 5173,
    [switch]$SkipDocker,
    [switch]$RunMigrations,
    [switch]$NoStopExisting
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$RunDir = Join-Path $Root ".codex-run"
$StatePath = Join-Path $RunDir "telegram-dev-stack.json"
$BackendDir = Join-Path $Root "backend"
$FrontendDir = Join-Path $Root "frontend"
$BotDir = Join-Path $Root "bot"

New-Item -ItemType Directory -Force -Path $RunDir | Out-Null

function Write-Step {
    param([string]$Message)
    Write-Host "[dev] $Message"
}

function Write-WarningLine {
    param([string]$Message)
    Write-Host "[warn] $Message" -ForegroundColor Yellow
}

function Get-RequiredCommand {
    param([string]$Name)

    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if (-not $command) {
        throw "Required command '$Name' was not found on PATH."
    }

    return $command.Source
}

function Stop-ProcessTree {
    param([int]$ProcessId)

    $children = Get-CimInstance Win32_Process -Filter "ParentProcessId = $ProcessId" -ErrorAction SilentlyContinue
    foreach ($child in $children) {
        Stop-ProcessTree -ProcessId ([int]$child.ProcessId)
    }

    Stop-Process -Id $ProcessId -Force -ErrorAction SilentlyContinue
}

function Stop-StateProcesses {
    if (-not (Test-Path $StatePath)) {
        return
    }

    try {
        $state = Get-Content $StatePath -Raw | ConvertFrom-Json
    }
    catch {
        Write-WarningLine "Could not read existing state file: $StatePath"
        return
    }

    if (-not ($state.PSObject.Properties.Name -contains "processes")) {
        return
    }

    foreach ($entry in @($state.processes)) {
        if ($entry.PSObject.Properties.Name -contains "pid") {
            Stop-ProcessTree -ProcessId ([int]$entry.pid)
        }
    }

    foreach ($portProperty in @("backendPort", "frontendPort")) {
        if ($state.PSObject.Properties.Name -contains $portProperty) {
            Stop-PortListeners -Port ([int]$state.$portProperty)
        }
    }

    Remove-Item -LiteralPath $StatePath -Force -ErrorAction SilentlyContinue
}

function Stop-PortListeners {
    param([int]$Port)

    $listeners = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue
    foreach ($listener in @($listeners)) {
        Stop-ProcessTree -ProcessId ([int]$listener.OwningProcess)
    }
}

function Assert-PortFree {
    param([int]$Port)

    $listeners = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue
    if ($listeners) {
        $pids = ($listeners | Select-Object -ExpandProperty OwningProcess -Unique) -join ", "
        throw "Port $Port is already in use by PID(s): $pids. Stop that process or run scripts/stop-telegram-dev.ps1 first."
    }
}

function Get-PortOwner {
    param([int]$Port)

    $listener = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $listener) {
        throw "Port $Port is not listening."
    }

    return [int]$listener.OwningProcess
}

function Invoke-Checked {
    param(
        [string]$Command,
        [string[]]$Arguments,
        [string]$WorkingDirectory
    )

    Push-Location $WorkingDirectory
    try {
        & $Command @Arguments
        if ($LASTEXITCODE -ne 0) {
            throw "Command failed with exit code ${LASTEXITCODE}: $Command $($Arguments -join ' ')"
        }
    }
    finally {
        Pop-Location
    }
}

function Start-LoggedProcess {
    param(
        [string]$Name,
        [string]$FilePath,
        [string[]]$Arguments,
        [string]$WorkingDirectory,
        [hashtable]$Environment = @{}
    )

    $stdout = Join-Path $RunDir "$Name.out.log"
    $stderr = Join-Path $RunDir "$Name.err.log"
    Remove-Item -LiteralPath $stdout, $stderr -Force -ErrorAction SilentlyContinue

    $previousEnv = @{}
    foreach ($key in $Environment.Keys) {
        $previousEnv[$key] = [Environment]::GetEnvironmentVariable($key, "Process")
        [Environment]::SetEnvironmentVariable($key, [string]$Environment[$key], "Process")
    }

    try {
        $process = Start-Process `
            -FilePath $FilePath `
            -ArgumentList $Arguments `
            -WorkingDirectory $WorkingDirectory `
            -RedirectStandardOutput $stdout `
            -RedirectStandardError $stderr `
            -WindowStyle Hidden `
            -PassThru
    }
    finally {
        foreach ($key in $Environment.Keys) {
            [Environment]::SetEnvironmentVariable($key, $previousEnv[$key], "Process")
        }
    }

    return [pscustomobject]@{
        name = $Name
        pid = $process.Id
        stdout = $stdout
        stderr = $stderr
    }
}

function Wait-HttpOk {
    param(
        [string]$Url,
        [int]$TimeoutSeconds = 60
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        try {
            $response = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 10
            if ([int]$response.StatusCode -ge 200 -and [int]$response.StatusCode -lt 400) {
                return
            }
        }
        catch {
            Start-Sleep -Seconds 2
            continue
        }

        Start-Sleep -Seconds 2
    }

    throw "Timed out waiting for $Url"
}

function Wait-TunnelUrl {
    param(
        [string]$Name,
        [int]$TimeoutSeconds = 60
    )

    $stdout = Join-Path $RunDir "$Name.out.log"
    $stderr = Join-Path $RunDir "$Name.err.log"
    $pattern = "https://[-a-z0-9]+\.trycloudflare\.com"
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)

    while ((Get-Date) -lt $deadline) {
        $content = ""
        if (Test-Path $stdout) {
            $content += Get-Content $stdout -Raw
        }
        if (Test-Path $stderr) {
            $content += Get-Content $stderr -Raw
        }

        $matches = [regex]::Matches($content, $pattern)
        if ($matches.Count -gt 0) {
            return $matches[$matches.Count - 1].Value
        }

        Start-Sleep -Seconds 2
    }

    throw "Timed out waiting for $Name tunnel URL. Check $stderr"
}

function Wait-PostgresHealthy {
    $deadline = (Get-Date).AddSeconds(90)
    while ((Get-Date) -lt $deadline) {
        $status = & docker inspect -f "{{.State.Health.Status}}" learning-os-postgres 2>$null
        if ($LASTEXITCODE -eq 0 -and $status -eq "healthy") {
            return
        }
        Start-Sleep -Seconds 3
    }

    throw "Postgres container did not become healthy in time."
}

function Test-DatabaseHasSchema {
    $result = docker exec learning-os-postgres psql -U postgres -d learning_os -tAc "SELECT to_regclass('public.users') IS NOT NULL" 2>$null
    return ($LASTEXITCODE -eq 0 -and $result.Trim() -eq "t")
}

function Invoke-Migrations {
    $migrationDir = Join-Path $BackendDir "migrations"
    $files = Get-ChildItem $migrationDir -Filter "*.sql" | Sort-Object Name
    foreach ($file in $files) {
        Write-Step "Running migration $($file.Name)"
        Get-Content $file.FullName | docker exec -i learning-os-postgres psql -U postgres -d learning_os -v ON_ERROR_STOP=1
        if ($LASTEXITCODE -ne 0) {
            throw "Migration failed: $($file.FullName)"
        }
    }
}

function Start-CloudflaredTunnel {
    param(
        [string]$Name,
        [string]$TargetUrl,
        [int]$Attempts = 3
    )

    for ($attempt = 1; $attempt -le $Attempts; $attempt++) {
        Write-Step "Starting $Name tunnel (attempt $attempt/$Attempts)"
        $process = Start-LoggedProcess `
            -Name $Name `
            -FilePath $cloudflared `
            -Arguments @("tunnel", "--url", $TargetUrl) `
            -WorkingDirectory $Root

        $publicUrl = Wait-TunnelUrl -Name $Name
        if (Get-Process -Id ([int]$process.pid) -ErrorAction SilentlyContinue) {
            return [pscustomobject]@{
                process = $process
                url = $publicUrl
            }
        }

        Write-WarningLine "$Name tunnel exited before it became usable."
        Start-Sleep -Seconds 4
    }

    throw "Could not create a reachable $Name tunnel after $Attempts attempts."
}

if (-not $NoStopExisting) {
    Stop-StateProcesses
}

Assert-PortFree -Port $BackendPort
Assert-PortFree -Port $FrontendPort

$cloudflared = Get-RequiredCommand "cloudflared"
$npm = Get-RequiredCommand "npm.cmd"

$uvicorn = Join-Path $BackendDir ".venv\Scripts\uvicorn.exe"
$botPython = Join-Path $BotDir ".venv\Scripts\python.exe"

if (-not (Test-Path $uvicorn)) {
    throw "Backend virtualenv is missing: $uvicorn"
}
if (-not (Test-Path $botPython)) {
    throw "Bot virtualenv is missing: $botPython"
}
if (-not (Test-Path (Join-Path $FrontendDir "node_modules"))) {
    throw "Frontend dependencies are missing. Run: cd frontend; npm install"
}

if (-not $SkipDocker) {
    Get-RequiredCommand "docker" | Out-Null
    Write-Step "Starting postgres and redis with docker compose"
    Invoke-Checked -Command "docker" -Arguments @("compose", "up", "-d", "postgres", "redis") -WorkingDirectory $Root
    Wait-PostgresHealthy

    if ($RunMigrations -or -not (Test-DatabaseHasSchema)) {
        Invoke-Migrations
    }
}

$processes = @()

Write-Step "Starting backend on 127.0.0.1:$BackendPort"
$backendInitial = Start-LoggedProcess `
    -Name "backend-initial" `
    -FilePath $uvicorn `
    -Arguments @("app.main:app", "--host", "127.0.0.1", "--port", [string]$BackendPort) `
    -WorkingDirectory $BackendDir
$processes += $backendInitial
Wait-HttpOk -Url "http://127.0.0.1:$BackendPort/health"

$backendTunnel = Start-CloudflaredTunnel `
    -Name "cloudflared-backend" `
    -TargetUrl "http://127.0.0.1:$BackendPort"
$processes += $backendTunnel.process
$backendUrl = $backendTunnel.url

Write-Step "Starting frontend on 127.0.0.1:$FrontendPort"
$frontend = Start-LoggedProcess `
    -Name "frontend" `
    -FilePath $npm `
    -Arguments @("run", "dev", "--", "--host", "127.0.0.1", "--port", [string]$FrontendPort) `
    -WorkingDirectory $FrontendDir `
    -Environment @{ VITE_API_BASE_URL = $backendUrl }
$processes += $frontend
Wait-HttpOk -Url "http://127.0.0.1:$FrontendPort/"
$frontend.pid = Get-PortOwner -Port $FrontendPort

$frontendTunnel = Start-CloudflaredTunnel `
    -Name "cloudflared-frontend" `
    -TargetUrl "http://127.0.0.1:$FrontendPort"
$processes += $frontendTunnel.process
$frontendUrl = $frontendTunnel.url

Write-Step "Restarting backend with frontend tunnel in ALLOWED_ORIGINS"
Stop-ProcessTree -ProcessId ([int]$backendInitial.pid)
$processes = @($processes | Where-Object { $_.name -ne "backend-initial" })
Start-Sleep -Seconds 2

$allowedOrigins = @(
    "http://localhost:$FrontendPort",
    "http://127.0.0.1:$FrontendPort",
    $frontendUrl
) | ConvertTo-Json -Compress

$backend = Start-LoggedProcess `
    -Name "backend" `
    -FilePath $uvicorn `
    -Arguments @("app.main:app", "--host", "127.0.0.1", "--port", [string]$BackendPort) `
    -WorkingDirectory $BackendDir `
    -Environment @{ ALLOWED_ORIGINS = $allowedOrigins }
$processes += $backend
Wait-HttpOk -Url "http://127.0.0.1:$BackendPort/health"

$headers = @{
    Origin = $frontendUrl
    "Access-Control-Request-Method" = "GET"
    "Access-Control-Request-Headers" = "authorization"
}
$corsResponse = Invoke-WebRequest -UseBasicParsing -Method Options -Uri "http://127.0.0.1:$BackendPort/api/v1/users/me" -Headers $headers -TimeoutSec 20
if ($corsResponse.Headers["Access-Control-Allow-Origin"] -ne $frontendUrl) {
    Write-WarningLine "CORS preflight did not echo the frontend tunnel origin."
}

Write-Step "Starting Telegram bot in polling mode"
$bot = Start-LoggedProcess `
    -Name "bot" `
    -FilePath $botPython `
    -Arguments @("main.py") `
    -WorkingDirectory $BotDir `
    -Environment @{
        MINI_APP_URL = $frontendUrl
        USE_WEBHOOK = "false"
        DEBUG = "false"
    }
$processes += $bot
Start-Sleep -Seconds 5

if (-not (Get-Process -Id ([int]$bot.pid) -ErrorAction SilentlyContinue)) {
    throw "Bot process exited early. Check $($bot.stderr)"
}

$readyStatus = "unknown"
try {
    $readyResponse = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:$BackendPort/health/ready" -TimeoutSec 20
    $readyStatus = $readyResponse.Content
}
catch {
    $readyStatus = "not_ready"
}

$state = [ordered]@{
    startedAt = (Get-Date).ToString("o")
    backendUrl = $backendUrl
    frontendUrl = $frontendUrl
    backendPort = $BackendPort
    frontendPort = $FrontendPort
    readyStatus = $readyStatus
    processes = $processes
}

$state | ConvertTo-Json -Depth 6 | Set-Content -Path $StatePath -Encoding UTF8

Write-Host ""
Write-Host "Telegram dev stack is running." -ForegroundColor Green
Write-Host "Frontend tunnel: $frontendUrl"
Write-Host "Backend tunnel:  $backendUrl"
Write-Host "Local frontend:  http://127.0.0.1:$FrontendPort"
Write-Host "Local backend:   http://127.0.0.1:$BackendPort"
Write-Host "State file:      $StatePath"
Write-Host "Logs:            $RunDir"

if ($readyStatus -eq "not_ready") {
    Write-WarningLine "Backend readiness is not ready. If this is a fresh DB, rerun with -RunMigrations."
}
