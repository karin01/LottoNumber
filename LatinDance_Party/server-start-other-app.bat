@echo off
echo 다른 앱 서버 시작 중...
echo.
echo 현재 IP 주소 확인:
ipconfig | findstr "IPv4"
echo.
echo 서버가 시작됩니다. 브라우저에서 다음 주소로 접속하세요:
echo http://localhost:8001
echo.
echo 외부에서 접속하려면:
echo http://[외부IP]:8001
echo.
echo 서버를 중지하려면 Ctrl+C를 누르세요.
echo.
cd /d "%~dp0other-app-folder"
python -m http.server 8001
pause 