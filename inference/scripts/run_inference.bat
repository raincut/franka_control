@echo off
setlocal
set "PROJECT_DIR=%~dp0"
set "PYTHON=%USERPROFILE%\.conda\envs\mujoco\python.exe"

if not exist "%PYTHON%" (
  echo Python not found: %PYTHON%
  exit /b 1
)

cd /d "%PROJECT_DIR%"
"%PYTHON%" inference.py --episodes 2000 --video ..\videos\inference_episode.mp4 %*
