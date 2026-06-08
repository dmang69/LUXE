@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Luxe Collective Demo - Starting...
cls
echo.
echo ============================================================
echo  LUXE COLLECTIVE AI COMMAND PLATFORM - LIVE DEMO
echo  ============================================================
echo.
echo Checking Docker...
where docker >nul 2>&1
if errorlevel 1 (
  echo ERROR: Docker not found. Please install Docker Desktop first.
  pause
  exit /b 1
)

echo.
echo Checking .env file...
if not exist .env (
  echo Creating .env from template...
  copy NUL .env >nul
  set "GENERATED_SECRET="
  for /f %%i in ('powershell -NoProfile -Command "[guid]::NewGuid().ToString('N')" 2^>nul') do set "GENERATED_SECRET=%%i"
  if "!GENERATED_SECRET!"=="" set "GENERATED_SECRET=change-me-local-demo-only"
  echo DATABASE_URL=postgresql://luxe:luxe_secret@db:5432/luxe_collective > .env
  echo SECRET_KEY=!GENERATED_SECRET! >> .env
  echo ALGORITHM=HS256 >> .env
  echo ACCESS_TOKEN_EXPIRE_MINUTES=30 >> .env
  echo GENAI_API_KEY= >> .env
  echo USE_MOCK_AI=true >> .env
  echo CORS_ORIGINS=http://localhost:8501,http://127.0.0.1:8501 >> .env
  echo ALLOWED_HOSTS=localhost,127.0.0.1,api >> .env
  echo.
  echo .env created. PLEASE EDIT IT NOW TO ADD YOUR GenAI API key ^(GENAI_API_KEY^)!
  echo WARNING: DEMO DEFAULTS ARE LOCAL-ONLY. CHANGE DATABASE_URL AND SECRET_KEY BEFORE ANY NON-LOCAL USE.
  echo.
  notepad .env
  echo.
  echo AFTER SAVING .env, PRESS ANY KEY TO CONTINUE...
  pause >nul
)

echo.
echo Pulling demo images (first time only)...
docker compose pull

echo.
echo Starting Luxe Collective Platform...
echo.
echo API Docs: http://localhost:8000/docs
echo Dashboard: http://localhost:8501
echo.
echo IMPORTANT:
echo - Keep THIS WINDOW OPEN to keep services running
echo - Use Ctrl+C in this window or run stop-demo.bat to stop the demo cleanly
echo - First startup: 60-90 seconds (image pull + container initialization)
echo.
docker compose up
