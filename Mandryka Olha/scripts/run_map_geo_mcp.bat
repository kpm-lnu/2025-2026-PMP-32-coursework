@echo off
setlocal
cd /d "%~dp0.."

if not defined MAPY_API_KEY (
  echo [ERROR] MAPY_API_KEY is not set.
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo [ERROR] .venv\Scripts\python.exe not found.
  exit /b 1
)

".venv\Scripts\python.exe" "mcp_infra\mcp_server_map_geo\server.py"
