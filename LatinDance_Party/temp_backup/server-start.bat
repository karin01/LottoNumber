@echo off
echo 라틴댄스 파티 서버 시작 중...
echo.
echo 현재 IP 주소 확인:
ipconfig | findstr "IPv4"
echo.
echo 서버가 시작됩니다. 브라우저에서 다음 주소로 접속하세요:
echo http://localhost:8000
echo.
echo 외부에서 접속하려면:
echo http://[외부IP]:8000
echo.
echo 서버를 중지하려면 Ctrl+C를 누르세요.
echo.
cd /d "%~dp0static"
python -m http.server 8000
pause 