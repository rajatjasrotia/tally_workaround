<#
  migrate.ps1 - Run Alembic migrations for this project (PowerShell)
  Usage: .\migrate.ps1 [-DatabaseUrl <string>]
  If DatabaseUrl not provided, defaults to sqlite:///./backend/database.db
#>
param(
    [string]$DatabaseUrl = $(if ($env:DATABASE_URL) { $env:DATABASE_URL } else { "sqlite:///./backend/database.db" })
)

$env:DATABASE_URL = $DatabaseUrl
if ($env:PYTHONPATH) { $env:PYTHONPATH = "$env:PYTHONPATH;backend" } else { $env:PYTHONPATH = "backend" }
Write-Host "Using DATABASE_URL=$env:DATABASE_URL"

# Activate backend venv if present
$venv = Join-Path -Path (Get-Location) -ChildPath "backend\.venv\Scripts\Activate.ps1"
if (Test-Path $venv) {
    Write-Host "Activating venv $venv"
    & $venv
}

python -m alembic upgrade head
