# Activate the pinochleMVP virtual environment
$venvPath = "D:\Python\Projects\pinochleMVP\.venv\Scripts\Activate.ps1"

if (Test-Path $venvPath) {
    Write-Host "Activating virtual environment..." -ForegroundColor Green
    & $venvPath
} else {
    Write-Host "ERROR: Virtual environment not found at:" -ForegroundColor Red
    Write-Host "       $venvPath"
}
