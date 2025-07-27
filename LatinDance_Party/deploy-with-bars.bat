@echo off
echo ========================================
echo 라틴댄스 파티 웹앱 배포 (바 데이터 포함)
echo ========================================

REM 현재 디렉토리 확인
cd /d "%~dp0"

echo.
echo 1. Firebase CLI 설치 확인...
firebase --version >nul 2>&1
if errorlevel 1 (
    echo Firebase CLI가 설치되지 않았습니다.
    echo npm install -g firebase-tools 를 실행해주세요.
    pause
    exit /b 1
)

echo Firebase CLI 버전 확인 완료.

echo.
echo 2. Firebase 로그인 상태 확인...
firebase projects:list >nul 2>&1
if errorlevel 1 (
    echo Firebase 로그인이 필요합니다.
    firebase login
    if errorlevel 1 (
        echo 로그인 실패. 배포를 중단합니다.
        pause
        exit /b 1
    )
)

echo Firebase 로그인 확인 완료.

echo.
echo 3. 프로젝트 설정 확인...
echo 현재 Firebase 프로젝트: share-note-ef791

echo.
echo 4. 배포 실행...
echo Firebase Hosting에 배포를 시작합니다...
firebase deploy --only hosting --project share-note-ef791

if errorlevel 1 (
    echo 배포 실패!
    pause
    exit /b 1
)

echo.
echo ========================================
echo 배포 완료!
echo ========================================
echo.
echo 다음 단계:
echo 1. https://latinmat.co.kr 에서 사이트 확인
echo 2. 브라우저 F12 → Console에서 다음 명령어 실행:
echo    await migrateCSVToFirestore();
echo    await getBarsStats();
echo.
echo 3. 빠 이름 검색 기능 테스트
echo 4. 새 빠 추가 기능 테스트
echo.
echo ========================================

pause 