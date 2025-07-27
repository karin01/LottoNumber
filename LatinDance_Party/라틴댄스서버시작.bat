@echo off
echo =======================================
echo 라틴댄스 파티 서버 시작
echo =======================================
cd /d "G:\내 드라이브\KNOU\Somoim\Jungwon_Drive_Obsidian_Vault\LatinDance_Party"
echo 현재 폴더: %CD%
echo.
echo 서버 시작 중... (포트: 8080)
python -m http.server 8080
pause 