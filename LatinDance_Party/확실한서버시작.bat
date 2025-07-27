@echo off
title 라틴댄스 파티 서버 - 확실한 버전
echo ==========================================
echo 라틴댄스 파티 서버 확실한 시작!
echo ==========================================
echo.
echo 현재 배치파일 위치 확인중...
echo %~dp0
echo.
cd /d "%~dp0"
echo 이동 후 현재 폴더: %CD%
echo.
echo index.html 파일 확인:
dir index.html
echo.
echo 서버 시작! (포트: 6666)
echo ==========================================
python -m http.server 6666
pause 