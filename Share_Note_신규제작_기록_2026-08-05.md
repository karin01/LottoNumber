# Share Note 신규 제작 기록 (2026-08-05)

## 결론

기존 `share_note` 복구는 Firebase 키 부재 + Railway 백엔드 장애 + Google Drive 복사 실패로 어려웠다.  
`note-share-app`에 Flask + SQLite 기반으로 **새로 제작**했다.

## 경로

`G:\내 드라이브\KNOU\Somoim\Jungwon_Drive_Obsidian_Vault\note-share-app`

## 실행

1. `start.bat` 실행
2. 브라우저: http://localhost:5000
3. 관리자 기본 비밀번호: `admin1234`
4. AI 기능: `backend/.env`에 `GEMINI_API_KEY` 설정

## 구조

- `backend/app.py` — API + 프론트 서빙
- `backend/db.py` — SQLite CRUD
- `frontend/` — 웹 UI
- `data/` — DB/업로드 (gitignore)

## 참고

- GitHub `karin01/share_note` 저장소는 비어 있었음
- 옛 호스팅 UI: https://share-note-47f16.web.app (백엔드 죽음)
- Cursor 오류 `Failed to move agent root` 는 IDE 내부 이슈였고, 루트 재이동으로 해결
