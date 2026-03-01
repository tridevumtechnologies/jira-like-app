# ─────────────────────────────────────────────────────────────────────────────
#  run_mock.ps1  –  Start backend in mock mode (SQLite + fakeredis, no Docker)
# ─────────────────────────────────────────────────────────────────────────────
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

# Load .env.dev into the current process environment
foreach ($line in Get-Content "$root\.env.dev") {
    if ($line -match '^\s*#' -or $line -match '^\s*$') { continue }
    $parts = $line -split '=', 2
    if ($parts.Length -eq 2) {
        $key   = $parts[0].Trim()
        $value = $parts[1].Trim()
        [System.Environment]::SetEnvironmentVariable($key, $value, "Process")
        Write-Host "  SET $key"
    }
}

Write-Host ""
Write-Host "Starting Jira-Like API  [MOCK MODE — SQLite + fakeredis]"
Write-Host "Docs  → http://127.0.0.1:8000/docs"
Write-Host "Press Ctrl-C to stop"
Write-Host ""

& "$root\.venv\Scripts\uvicorn.exe" app.main:app --reload --host 127.0.0.1 --port 8000
