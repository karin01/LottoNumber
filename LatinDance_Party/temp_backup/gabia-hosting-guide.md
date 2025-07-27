# 가비아 웹호스팅 배포 가이드

## 1. 가비아 웹호스팅 준비

### 호스팅 상품 선택
- **Linux 호스팅** (Python 지원)
- **Python 3.8+** 지원 확인
- **SSH 접속** 권한 필요

### 도메인 연결
- `latinmat.co.kr` 도메인을 호스팅에 연결

## 2. 파일 업로드

### FTP 접속 정보
- 호스트: 가비아에서 제공
- 사용자명: 가비아에서 제공  
- 비밀번호: 가비아에서 제공
- 포트: 21 (FTP) 또는 22 (SFTP)

### 업로드할 파일들
```
public_html/
├── index.html (static/index.html 복사)
├── css/
│   └── style.css
├── js/
│   ├── main.js
│   ├── firebase-config.js
│   └── googlemap-init.js
├── backend/
│   ├── app.py
│   ├── requirements.txt
│   └── share-note-ef791-firebase-adminsdk-fbsvc-36ee9ed360.json
└── Latin_Bar_LIST.csv
```

## 3. Python 환경 설정

### SSH 접속
```bash
ssh 사용자명@호스트명
```

### Python 가상환경 생성
```bash
cd public_html/backend
python3 -m venv venv
source venv/bin/activate  # Linux
# 또는
venv\Scripts\activate     # Windows
```

### 패키지 설치
```bash
pip install -r requirements.txt
```

## 4. WSGI 설정

### passenger_wsgi.py 생성
```python
import sys
import os

# 가상환경 경로 설정
INTERP = os.path.expanduser("/home/사용자명/public_html/backend/venv/bin/python")
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

# Flask 앱 import
from app import app as application
```

## 5. 환경 변수 설정

### .env 파일 생성
```
FLASK_ENV=production
FLASK_DEBUG=0
```

## 6. 도메인 설정

### DNS 레코드
가비아 관리자 페이지에서:
```
Type: A
Name: @
Value: [가비아 서버 IP]

Type: CNAME
Name: www
Value: latinmat.co.kr
```

## 7. SSL 인증서

### Let's Encrypt 무료 SSL
가비아에서 Let's Encrypt SSL 인증서 발급

## 8. 테스트

### 사이트 접속
- `https://latinmat.co.kr` 접속 확인
- 파티 등록/조회 기능 테스트

## 9. 문제 해결

### 로그 확인
```bash
tail -f /home/사용자명/logs/error.log
```

### 권한 설정
```bash
chmod 755 public_html
chmod 644 public_html/*.html
chmod 644 public_html/css/*
chmod 644 public_html/js/*
``` 