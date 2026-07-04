Set-Location -LiteralPath 'C:\Users\Dhruvi Jain\Desktop\speech'
Write-Output "Launcher started in $(Get-Location)"
python .\seech.py 8765
Write-Output "Python exited with code $LASTEXITCODE"
