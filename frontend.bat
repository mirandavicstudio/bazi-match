@echo off
chcp 65001 >nul 2>&1
setlocal EnableDelayedExpansion

set "FRONTEND_DIR=%~dp0frontend"
set "PORT=3000"
set "PID_FILE=%~dp0.frontend.pid"

if "%1"=="" goto :menu
if /i "%1"=="start" goto :start
if /i "%1"=="stop" goto :stop
if /i "%1"=="restart" goto :restart
if /i "%1"=="status" goto :status
goto :usage

:menu
powershell -NoProfile -Command "Write-Host ''; Write-Host '================================'; Write-Host '  Bazi-Match Frontend Manager  '; Write-Host '================================'; Write-Host ''; Write-Host '  1. Start frontend'; Write-Host '  2. Stop frontend'; Write-Host '  3. Restart frontend'; Write-Host '  4. Status'; Write-Host '  0. Exit'; Write-Host ''"
set /p choice="Select: "
if "%choice%"=="1" goto :start
if "%choice%"=="2" goto :stop
if "%choice%"=="3" goto :restart
if "%choice%"=="4" goto :status
if "%choice%"=="0" exit /b 0
powershell -NoProfile -Command "Write-Host 'Invalid choice'"
goto :menu

:start
powershell -NoProfile -Command "Write-Host ''; Write-Host '[Start] Launching frontend...' -ForegroundColor Cyan; Write-Host ('[Start] Directory: ' + '%FRONTEND_DIR%') -ForegroundColor Gray; Write-Host ('[Start] Port: ' + '%PORT%') -ForegroundColor Gray"

netstat -ano | findstr ":%PORT% " | findstr "LISTENING" >nul 2>&1
if %errorlevel%==0 (
    powershell -NoProfile -Command "Write-Host '[Error] Port %PORT% is already in use!' -ForegroundColor Red; Write-Host '[Hint] Run stop first, or change PORT in script' -ForegroundColor Yellow"
    if "%1"=="" pause
    exit /b 1
)

if not exist "%FRONTEND_DIR%\index.html" (
    powershell -NoProfile -Command "Write-Host ('[Error] index.html not found: ' + '%FRONTEND_DIR%') -ForegroundColor Red"
    if "%1"=="" pause
    exit /b 1
)

powershell -NoProfile -Command "Write-Host '[Start] Starting Python HTTP server...' -ForegroundColor Cyan"
start /b python -m http.server %PORT% -d "%FRONTEND_DIR%" >nul 2>&1

timeout /t 2 /nobreak >nul

set "PID="
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%PORT% " ^| findstr "LISTENING"') do (
    set "PID=%%a"
)

if defined PID (
    echo %PID% > "%PID_FILE%"
    powershell -NoProfile -Command "Write-Host '[OK] Frontend started!' -ForegroundColor Green; Write-Host ('[OK] PID: %PID%') -ForegroundColor Green; Write-Host ('[OK] URL: http://localhost:%PORT%') -ForegroundColor Green; Write-Host ''; Write-Host 'Tip: Backend API should be at http://localhost:8000' -ForegroundColor DarkGray"
) else (
    powershell -NoProfile -Command "Write-Host '[Warn] Service may not have started, check port %PORT%' -ForegroundColor Yellow"
)

if "%1"=="" pause
exit /b 0

:stop
powershell -NoProfile -Command "Write-Host ''; Write-Host '[Stop] Stopping frontend...' -ForegroundColor Cyan"

set "SAVED_PID="
if exist "%PID_FILE%" (
    set /p SAVED_PID=<"%PID_FILE%"
)

if defined SAVED_PID (
    tasklist /fi "PID eq %SAVED_PID%" 2>nul | findstr "%SAVED_PID%" >nul 2>&1
    if %errorlevel%==0 (
        taskkill /pid %SAVED_PID% /f >nul 2>&1
        powershell -NoProfile -Command "Write-Host ('[OK] Killed PID: %SAVED_PID%') -ForegroundColor Green"
    ) else (
        powershell -NoProfile -Command "Write-Host ('[Info] PID %SAVED_PID% not found') -ForegroundColor DarkGray"
    )
    del "%PID_FILE%" >nul 2>&1
)

for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%PORT% " ^| findstr "LISTENING"') do (
    taskkill /pid %%a /f >nul 2>&1
    powershell -NoProfile -Command "Write-Host ('[OK] Killed process on port %PORT%, PID: %%a') -ForegroundColor Green"
)

powershell -NoProfile -Command "Write-Host '[Done] Frontend stopped' -ForegroundColor Green"
if "%1"=="" pause
exit /b 0

:restart
call :stop
timeout /t 1 /nobreak >nul
call :start
exit /b 0

:status
powershell -NoProfile -Command "Write-Host ''; Write-Host '[Status] Checking...' -ForegroundColor Cyan; Write-Host ('[Status] Port: ' + '%PORT%') -ForegroundColor Gray"

netstat -ano | findstr ":%PORT% " | findstr "LISTENING" >nul 2>&1
if %errorlevel%==0 (
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%PORT% " ^| findstr "LISTENING"') do (
        powershell -NoProfile -Command "Write-Host ('[Running] Frontend is running, PID: %%a') -ForegroundColor Green; Write-Host ('[Running] URL: http://localhost:%PORT%') -ForegroundColor Green"
    )
) else (
    powershell -NoProfile -Command "Write-Host '[Stopped] Frontend is not running' -ForegroundColor Red"
)

if exist "%PID_FILE%" (
    set /p SAVED_PID=<"%PID_FILE%"
    powershell -NoProfile -Command "Write-Host ('[Record] PID file: %SAVED_PID%') -ForegroundColor DarkGray"
) else (
    powershell -NoProfile -Command "Write-Host '[Record] No PID file' -ForegroundColor DarkGray"
)

if "%1"=="" pause
exit /b 0

:usage
powershell -NoProfile -Command "Write-Host ''; Write-Host 'Usage: %~nx0 [start|stop|restart|status]' -ForegroundColor Cyan; Write-Host ''; Write-Host '  start    - Start frontend'; Write-Host '  stop     - Stop frontend'; Write-Host '  restart  - Restart frontend'; Write-Host '  status   - Show status'; Write-Host ''; Write-Host '  Run without args for interactive menu' -ForegroundColor DarkGray"
exit /b 1
