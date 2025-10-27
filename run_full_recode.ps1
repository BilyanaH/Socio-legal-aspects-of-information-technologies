# Full Re-Geocoding Script - Run this in PowerShell
Write-Host "=== Starting Full Re-Geocoding ===" -ForegroundColor Green
Write-Host ""
Write-Host "This will take about 60-70 seconds..."
Write-Host "Progress will be shown below:"
Write-Host ""

$startTime = Get-Date

# Run Python script
python full_recode_free.py

$endTime = Get-Date
$duration = ($endTime - $startTime).TotalSeconds

Write-Host ""
Write-Host "=== COMPLETED ===" -ForegroundColor Green
Write-Host "Duration: $duration seconds"
Write-Host ""
Write-Host "Check results in: hospitals_with_coords.csv"
Write-Host ""

# Show quick stats
Write-Host "Quick stats from CSV:"
python -c "import pandas as pd; df=pd.read_csv('hospitals_with_coords.csv'); print(f'Total rows: {len(df)}'); print(f'With coords: {df.lat.notna().sum()}'); print(f'Missing: {df.lat.isna().sum()}')"
