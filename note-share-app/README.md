# Share Note (학습 노트 공유)

로컬에서 바로 쓰는 학습 노트 공유 웹앱입니다.  
Firebase/Railway 없이 **Flask + SQLite** 로 동작합니다.

## 실행 방법

1. `start.bat` 더블클릭
2. 브라우저에서 [http://localhost:5000](http://localhost:5000) 접속

또는:

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r backend\requirements.txt
cd backend
python app.py
```

## 기능

- PDF / MP3 / 이미지 업로드
- 태그 검색
- 다운로드 / 삭제 암호로 삭제
- PDF 질문 생성 · 상세 정리 (Gemini API 키 있을 때)
- 관리자: 전체 삭제, DB 초기화 (기본 비밀번호 `admin1234`)

## AI 설정 (선택)

`backend/.env.example` 을 복사해 `backend/.env` 를 만들고:

```
GEMINI_API_KEY=여기에_키
ADMIN_PASSWORD=원하는_관리자_비번
```

## 폴더 구조

```
note-share-app/
  backend/     # Flask API
  frontend/    # 웹 UI
  data/        # SQLite + 업로드 (자동 생성, git 제외)
  start.bat
```

## 왜 이렇게 만들었나

예전 Share Note는 Firebase 키 부재 + Railway 백엔드 장애로 복구가 어려웠습니다.  
같은 핵심 기능을 **로컬 우선**으로 다시 만들어, 바로 웹에서 확인 가능하게 했습니다.
