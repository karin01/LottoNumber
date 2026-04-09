# NEON REQUIEM 2087 — 받아서 플레이하기

**AI 1인 MUD 게임** 프론트엔드(Vite)와 Flask 백엔드가 포함되어 있습니다.

> **공개 다운로드 저장소:** [github.com/karin01/TEXT-Mud-Game](https://github.com/karin01/TEXT-Mud-Game) — 여기서 받으면 아래 폴더가 저장소 **루트**입니다.  
> 상위 옵시디언 볼트 저장소만 클론했다면 `AI 1인 MUD Game NEON REQUIEM` 폴더로 들어온 뒤, 실행 방법은 동일합니다.

---

## 받기

| 방법 | 설명 |
|------|------|
| **Git** | `git clone https://github.com/karin01/TEXT-Mud-Game.git` |
| **ZIP** | [main 브랜치 ZIP](https://github.com/karin01/TEXT-Mud-Game/archive/refs/heads/main.zip) |

클론 후 기본 폴더 이름은 `TEXT-Mud-Game` 입니다. **그 폴더를 게임 루트**로 두고 진행합니다.

---

## 필요한 것

- **Node.js** (LTS 권장) — [https://nodejs.org/](https://nodejs.org/)
- **Python 3** — Flask 백엔드용 — [https://www.python.org/downloads/](https://www.python.org/downloads/)

```bash
node -v
npm -v
python --version
```

---

## Windows — 가장 쉬운 실행

1. ZIP을 풀었거나 클론한 **게임 루트**로 이동합니다.
2. **`게임시작.bat`** 을 더블클릭합니다.

백엔드(Flask, 포트 5000)가 새 창에서 뜨고, `frontend`에서 `npm install` 후 `npm run dev`(기본 5173)가 실행됩니다.  
브라우저가 안 열리면 `http://localhost:5173` 을 입력합니다.

PowerShell: `.\게임시작.ps1`

---

## macOS / Linux

**터미널 1 — 백엔드**

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

**터미널 2 — 프론트** (게임 루트에서)

```bash
cd frontend
npm install
npm run dev
```

브라우저에서 `http://localhost:5173` 접속.

---

## 더 보기

- 동작 순서·주의사항: [`docs/게임시작-가이드.md`](docs/게임시작-가이드.md)

---

## 문제 해결

- Node/Python 설치 직후에는 터미널을 **다시 연 뒤** 실행합니다.
- 포트 **5173** / **5000**이 사용 중이면 다른 프로그램을 종료하거나 설정에서 포트를 바꿉니다.
