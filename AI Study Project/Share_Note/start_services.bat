@echo off
chcp 65001 >nul
echo ========================================
echo    Share_Note 서비스 시작 스크립트
echo ========================================
echo.

:: 현재 디렉토리를 Share_Note 폴더로 변경
cd /d "%~dp0"

:: 1. 가상환경 활성화
echo [1/4] 가상환경 활성화 중...
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo ✓ 가상환경 활성화 완료
) else (
    echo ✗ 가상환경을 찾을 수 없습니다. venv 폴더가 있는지 확인하세요.
    pause
    exit /b 1
)

:: 2. Ollama 서버 시작 (백그라운드)
echo.
echo [2/4] Ollama 서버 시작 중...
start /B ollama serve
timeout /t 3 /nobreak >nul
echo ✓ Ollama 서버 시작 완료

:: 3. 필요한 패키지 설치 확인
echo.
echo [3/4] 필요한 패키지 확인 중...
pip install -r backend/requirements.txt >nul 2>&1
echo ✓ 패키지 확인 완료

:: 4. Flask 서버 시작
echo.
echo [4/4] Flask 서버 시작 중...
echo ✓ 모든 서비스가 시작되었습니다!
echo.
echo ========================================
echo    서비스 정보
echo ========================================
echo • 웹앱: http://localhost:5000
echo • Ollama API: http://localhost:11434
echo.
echo 서비스를 종료하려면 stop_services.bat을 실행하세요.
echo ========================================
echo.

:: Flask 서버 실행 (이 명령어가 끝나면 배치 파일도 종료됨)
cd backend
python app.py 