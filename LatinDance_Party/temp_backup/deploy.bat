@echo off
echo 라틴댄스 파티 웹앱 배포 스크립트
echo ================================

echo 1. Git 초기화 및 커밋...
if not exist .git (
    git init
    echo Git 저장소 초기화 완료
)

git add .
git commit -m "Update: 갤러리 업로드 버튼 개선 및 호스팅 준비"

echo.
echo 2. GitHub 저장소 연결 확인...
git remote -v

echo.
echo 3. 배포 준비 완료!
echo.
echo 다음 단계를 따라주세요:
echo.
echo [GitHub 설정]
echo 1. GitHub에서 새 저장소 생성: latin-dance-party
echo 2. 아래 명령어로 원격 저장소 연결:
echo    git remote add origin https://github.com/사용자명/latin-dance-party.git
echo 3. 코드 업로드:
echo    git push -u origin main
echo.
echo [Netlify 배포]
echo 1. https://netlify.com 접속
echo 2. GitHub 계정으로 로그인
echo 3. "New site from Git" 클릭
echo 4. latin-dance-party 저장소 선택
echo 5. Publish directory: static
echo 6. "Deploy site" 클릭
echo.
echo [Firebase 설정]
echo 1. Firebase 콘솔에서 Authorized domains에 도메인 추가
echo 2. latinmat.co.kr 및 배포된 도메인 추가
echo.
pause 