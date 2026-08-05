@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo  학습 노트 공유 앱 시작
echo ========================================

REM 데이터 폴더 준비
if not exist "data\uploads" mkdir "data\uploads"

REM WHY: Google Drive 위 .venv는 생성/설치가 매우 느려 로컬 AppData 사용
set "VENV_DIR=%LOCALAPPDATA%\note-share-app-venv"
set "PYTHON_EXE=%VENV_DIR%\Scripts\python.exe"

if not exist "%PYTHON_EXE%" (
  echo [1/3] 로컬 가상환경 생성 중... (%VENV_DIR%)
  python -m venv "%VENV_DIR%"
  if errorlevel 1 (
    echo Python이 설치되어 있지 않거나 PATH에 없습니다.
    pause
    exit /b 1
  )
) else (
  echo [1/3] 가상환경 확인 완료
)

echo [2/3] 패키지 확인/설치 중...
"%PYTHON_EXE%" -m pip install -q -r "backend\requirements.txt"
if errorlevel 1 (
  echo 패키지 설치 실패
  pause
  exit /b 1
)

if not exist "backend\.env" (
  if exist "backend\.env.example" (
    copy /Y "backend\.env.example" "backend\.env" >nul
    echo backend\.env 를 예시에서 생성했습니다. Gemini 키가 필요하면 편집하세요.
  )
)

echo [3/3] 서버 기동: http://localhost:5000
echo 종료하려면 이 창에서 Ctrl+C
echo.

start "" "http://localhost:5000"
"%PYTHON_EXE%" "backend\app.py"
pause
