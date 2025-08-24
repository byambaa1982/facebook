# PowerShell script to run Flask in virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Green
& .\.venv\Scripts\Activate.ps1
Write-Host "Starting Flask application..." -ForegroundColor Green
python .\flask_app.py
