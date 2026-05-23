<#
.SYNOPSIS
Stops processes started by scripts/start-telegram-dev.ps1.

.EXAMPLE
powershell -ExecutionPolicy Bypass -File .\scripts\stop-telegram-dev.ps1
#>

[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$RunDir = Join-Path $Root ".codex-run"
$StatePath = Join-Path $RunDir "telegram-dev-stack.json"

function Stop-ProcessTree {
    param([int]$ProcessId)

    $children = Get-CimInstance Win32_Process -Filter "ParentProcessId = $ProcessId" -ErrorAction SilentlyContinue
    foreach ($child in $children) {
        Stop-ProcessTree -ProcessId ([int]$child.ProcessId)
    }

    Stop-Process -Id $ProcessId -Force -ErrorAction SilentlyContinue
}

function Stop-PortListeners {
    param([int]$Port)

    $listeners = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue
    foreach ($listener in @($listeners)) {
        Write-Host "Stopping listener on port $Port PID $($listener.OwningProcess)"
        Stop-ProcessTree -ProcessId ([int]$listener.OwningProcess)
    }
}

if (-not (Test-Path $StatePath)) {
    Write-Host "No telegram dev stack state found at $StatePath"
    exit 0
}

$state = Get-Content $StatePath -Raw | ConvertFrom-Json
if ($state.PSObject.Properties.Name -contains "processes") {
    foreach ($entry in @($state.processes)) {
        if ($entry.PSObject.Properties.Name -contains "pid") {
            Write-Host "Stopping $($entry.name) PID $($entry.pid)"
            Stop-ProcessTree -ProcessId ([int]$entry.pid)
        }
    }
}

foreach ($portProperty in @("backendPort", "frontendPort")) {
    if ($state.PSObject.Properties.Name -contains $portProperty) {
        Stop-PortListeners -Port ([int]$state.$portProperty)
    }
}

Remove-Item -LiteralPath $StatePath -Force -ErrorAction SilentlyContinue
Write-Host "Telegram dev stack stopped."
