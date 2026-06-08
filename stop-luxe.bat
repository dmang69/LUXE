@echo off
title Luxe Collective - Stop Services
echo.
echo  Stopping Luxe Collective Platform services...
echo.
docker compose down
echo.
echo  All services stopped.
echo  Your data is preserved in the Docker volume 'pgdata'.
echo  Run start-luxe.bat to start again.
echo.
pause
