<#
.SYNOPSIS
    Launches Policy Assistant services in Windows Terminal tabs
    with duplicate prevention and restart/terminate options.

.DESCRIPTION
    - Starts each service in a separate Windows Terminal tab
    - Prevents duplicate service launches
    - Supports:
        - -Restart   → Kill all services and start fresh
        - -Terminate → Kill all services and exit
    - Must be run from project root

.EXAMPLE
    .\run_services_tabs.ps1

.EXAMPLE
    .\run_services_tabs.ps1 -Restart

.EXAMPLE
    .\run_services_tabs.ps1 -Terminate
#>

param (
    [Alias("t")]
    [switch]$Terminate,

    [Alias("r")]
    [switch]$Restart
)

# ---------------- CONFIG ----------------

$root = Get-Location

$services = @{
    "api-gateway"  = "services/api_gateway"
    "chat-service" = "services/chat_service"
    "llm-service"  = "services/llm_service"
    "rag-service"  = "services/rag_service"
    "rag-worker"   = "services/rag_worker"
}

# ---------------- HELPERS ----------------

function Stop-PolicyServices {
    Write-Host "Stopping Policy Assistant services..." -ForegroundColor Yellow

    foreach ($name in $services.Keys) {
        $pattern = "*uv run $name*"

        $procs = Get-CimInstance Win32_Process | Where-Object {
            ($_.Name -eq "cmd.exe" -or $_.Name -eq "powershell.exe" -or $_.Name -eq "pwsh.exe") -and
            $_.CommandLine -like $pattern
        }

        foreach ($p in $procs) {
            Write-Host "Killing $name (PID $($p.ProcessId))" -ForegroundColor DarkYellow
            Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
        }
    }
}

function Is-ServiceRunning($name) {
    $pattern = "*uv run $name*"

    $proc = Get-CimInstance Win32_Process | Where-Object {
        ($_.Name -eq "cmd.exe" -or $_.Name -eq "powershell.exe" -or $_.Name -eq "pwsh.exe") -and
        $_.CommandLine -like $pattern
    }

    return [bool]$proc
}

# ---------------- CONTROL FLOW ----------------

if ($Terminate) {
    Stop-PolicyServices
    Write-Host "All services terminated." -ForegroundColor Green
    exit
}

if ($Restart) {
    Stop-PolicyServices
}

# ---------------- VALIDATION ----------------

if (-not (Get-Command wt.exe -ErrorAction SilentlyContinue)) {
    Write-Error "Windows Terminal (wt.exe) not found in PATH."
    exit 1
}

# ---------------- START SERVICES ----------------

$wtTabs = @()

Write-Host "Checking services..." -ForegroundColor Cyan

foreach ($name in $services.Keys) {
    $relativeDir = $services[$name]
    $fullPath = Join-Path $root $relativeDir

    if (-not (Test-Path $fullPath)) {
        Write-Host "Path not found: $fullPath" -ForegroundColor Red
        continue
    }

    if (-not $Restart -and (Is-ServiceRunning $name)) {
        Write-Host "Skipping $name (already running)" -ForegroundColor Gray
        continue
    }

    Write-Host "Scheduling $name..." -ForegroundColor Green

    # IMPORTANT: cmd /k avoids Windows Terminal parsing issues
    $cmd = "echo Starting $name... && uv run $name"

    $tab = "nt -d `"$fullPath`" --title `"$name`" cmd /k $cmd"
    $wtTabs += $tab
}

# ---------------- EXECUTE ----------------

if ($wtTabs.Count -eq 0) {
    Write-Host "All services are already running." -ForegroundColor Cyan
    exit
}

$finalArgs = $wtTabs -join " ; "

Write-Host "Launching services in Windows Terminal..." -ForegroundColor Green
Start-Process wt.exe -ArgumentList $finalArgs
