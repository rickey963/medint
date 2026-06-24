# run_medint_engine.ps1 - Automated MEDINT Engine Runner

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $scriptDir

$loop_interval = 120 # 2 minutes in seconds

Write-Host "Starting MEDINT Engine automation loop..." -ForegroundColor Green
Write-Host "[!] Press Ctrl+C to stop the engine." -ForegroundColor Yellow

while ($true) {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] Starting data fetch (python fetch_data.py)..." -ForegroundColor Cyan

    try {
        python fetch_data.py

        if ($?) {
            Write-Host "[$timestamp] Data update successful!" -ForegroundColor Green
        } else {
            Write-Error "[$timestamp] Data update failed! Check Python errors."
        }
    }
    catch {
        Write-Host "[$timestamp] An error occurred: $_" -ForegroundColor Red
    }

    Write-Host "Waiting for $loop_interval seconds until next update..." -ForegroundColor Gray
    Start-Sleep -Seconds $loop_interval
}
