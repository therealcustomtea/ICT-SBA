@echo off
setlocal
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install-Cipherboard.ps1"
if errorlevel 1 (
  echo.
  echo Cipherboard installation did not complete.
  pause
  exit /b 1
)
pause
