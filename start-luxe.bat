@echo off
setlocal enabledelayedexpansion
title Luxe Collective Platform Launcher

echo.
echo  ================================================================
echo   LUXE COLLECTIVE PLATFORM - Local Demo Launcher
echo  ================================================================
echo.

:: Check for Docker
where docker >nul 2>&1
if errorlevel 1 (
  echo  ERROR: Docker not found in PATH.
  echo  Please install Docker Desktop first:
  echo  https://www.docker.com/products/docker-desktop/
  echo.
  pause
  exit /b 1
)

:: Check if Docker daemon is running
docker info >nul 2>&1
if errorlevel 1 (
  echo  ERROR: Docker Desktop is not running.
  echo  Please start Docker Desktop and wait for it to fully load
  echo  (look for the whale icon in your system tray), then try again.
  echo.
  pause
  exit /b 1
)

:: Check / create .env
if not exist .env (
  echo  WARNING: .env file not found.
  if exist .env.template (
    echo  Copying .env.template to .env...
    copy .env.template .env >nul
    echo.
    echo  !! IMPORTANT: Open .env in a text editor and set your values.
    echo  !! At minimum, review the SECRET_KEY setting.
    echo  !! To use real AI generation, set USE_MOCK_AI=false and add
    echo  !! your GENAI_API_KEY from https://aistudio.google.com/app/apikey
    echo.
    echo  Press any key to open .env in Notepad, then re-run this script.
    pause >nul
    notepad .env
    exit /b 0
  ) else (
    echo  ERROR: .env.template not found either. Cannot start.
    pause
    exit /b 1
  )
)

:: Build images (first run or after code changes)
echo  Building Docker images (this may take a few minutes on first run)...
docker compose build
if errorlevel 1 (
  echo  ERROR: Docker build failed. See output above.
  pause
  exit /b 1
)

echo.
echo  Starting Luxe Collective Platform...
echo.
echo  Once started:
echo    API Docs   : http://localhost:8000/docs
echo    Dashboard  : http://localhost:8501
echo.
echo  First startup pulls images and initializes the database (~1-3 min).
echo  Press Ctrl+C to stop all services.
echo.

docker compose up

echo.
echo  Services stopped. Press any key to close this window...
pause >nul
