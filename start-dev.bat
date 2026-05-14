@echo off
REM Double-clickable wrapper for start-dev.ps1. Bypasses PowerShell
REM execution policy so the user doesn't have to run a separate
REM Set-ExecutionPolicy command.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-dev.ps1"
