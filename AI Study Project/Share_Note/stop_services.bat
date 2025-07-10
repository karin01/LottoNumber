@echo off
chcp 65001 >nul
echo ========================================
echo    Share_Note 서비스 종료 스크립트
echo ========================================
echo.

:: Flask 서버 종료 (포트 5000 사용 프로세스)
echo [1/2] Flask 서버 종료 중...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5000') do (
    taskkill /F /PID %%a >nul 2>&1
    echo ✓ Flask 서버 종료 완료
)

:: Ollama 서버 종료 (포트 11434 사용 프로세스)
echo.
echo [2/2] Ollama 서버 종료 중...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :11434') do (
    taskkill /F /PID %%a >nul 2>&1
    echo ✓ Ollama 서버 종료 완료
)

echo.
echo ========================================
echo    모든 서비스가 종료되었습니다.
echo ========================================
echo.
pause 