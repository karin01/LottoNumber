# 🖥️ 개인 PC 서버 배포 가이드

## 📋 개인 서버 배포 방법

### 1단계: 포트포워딩 설정

#### 공유기 관리자 페이지 접속
1. 브라우저에서 `192.168.0.1` 또는 `192.168.1.1` 접속
2. 관리자 계정으로 로그인
3. 포트포워딩 또는 포트 매핑 메뉴 찾기

#### 포트포워딩 규칙 추가
```
외부 포트: 80 → 내부 IP: [PC IP] → 내부 포트: 8000
외부 포트: 443 → 내부 IP: [PC IP] → 내부 포트: 8000
```

### 2단계: 고정 IP 설정

#### Windows에서 고정 IP 설정
1. 제어판 → 네트워크 및 인터넷 → 네트워크 및 공유 센터
2. 현재 연결된 네트워크 클릭 → 속성
3. 인터넷 프로토콜 버전 4(TCP/IPv4) → 속성
4. "다음 IP 주소 사용" 선택
5. IP 주소: `192.168.1.100` (공유기 범위 내에서 설정)
6. 서브넷 마스크: `255.255.255.0`
7. 기본 게이트웨이: `192.168.1.1` (공유기 IP)

### 3단계: 방화벽 설정

#### Windows 방화벽 설정
1. 제어판 → 시스템 및 보안 → Windows 방화벽
2. 고급 설정 → 인바운드 규칙
3. 새 규칙 → 포트 선택
4. TCP, 특정 포트: 8000
5. 연결 허용 선택
6. 모든 프로필 선택
7. 이름: "라틴댄스 파티 서버"

### 4단계: 서버 실행

#### 방법 1: 배치 파일 사용 (권장)
```bash
# server-start.bat 파일을 더블클릭
```

#### 방법 2: 명령 프롬프트 사용
```bash
cd static
python -m http.server 8000
```

### 5단계: 외부 IP 확인

#### 외부 IP 확인 방법
1. https://whatismyipaddress.com 접속
2. 또는 명령 프롬프트에서: `nslookup myip.opendns.com resolver1.opendns.com`

### 6단계: 도메인 설정 (선택사항)

#### 무료 도메인 서비스 사용
1. **No-IP**: https://www.noip.com
2. **Dynu**: https://www.dynu.com
3. **DuckDNS**: https://www.duckdns.org

#### 도메인 설정 예시
- 도메인: `latin-dance-party.duckdns.org`
- IP: `[외부IP]`
- 포트: 80

### 7단계: SSL 인증서 설정 (선택사항)

#### Let's Encrypt 사용
```bash
# Certbot 설치
pip install certbot

# 인증서 발급
certbot certonly --standalone -d your-domain.com
```

## 🔧 서버 관리

### 서버 자동 시작 설정

#### Windows 작업 스케줄러 사용
1. 작업 스케줄러 열기
2. 기본 작업 만들기
3. 프로그램 시작: `python -m http.server 8000`
4. 시작 위치: `[프로젝트경로]/static`
5. 로그온 시 시작 설정

### 서버 모니터링

#### 간단한 모니터링 스크립트
```python
import requests
import time
import subprocess

def check_server():
    try:
        response = requests.get('http://localhost:8000', timeout=5)
        if response.status_code == 200:
            print("서버 정상 동작 중")
        else:
            print("서버 오류 발생")
    except:
        print("서버 연결 실패")
        # 서버 재시작
        subprocess.Popen(['python', '-m', 'http.server', '8000'], cwd='static')

# 5분마다 체크
while True:
    check_server()
    time.sleep(300)
```

## 🌐 접속 테스트

### 로컬 접속 테스트
```
http://localhost:8000
http://192.168.1.100:8000
```

### 외부 접속 테스트
```
http://[외부IP]:8000
http://your-domain.com
```

## 🔒 보안 설정

### 기본 보안 조치
1. **방화벽 설정**: 필요한 포트만 열기
2. **정기 업데이트**: Windows 및 Python 업데이트
3. **백업**: 정기적인 데이터 백업
4. **모니터링**: 서버 상태 모니터링

### 고급 보안 설정
```python
# HTTPS 서버 설정 (선택사항)
import ssl
import http.server
import socketserver

class HTTPServer(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain('cert.pem', 'key.pem')

with socketserver.TCPServer(("", 8000), HTTPServer) as httpd:
    httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
    httpd.serve_forever()
```

## 📱 모바일 접속

### 모바일에서 접속
- 같은 Wi-Fi 네트워크: `http://192.168.1.100:8000`
- 외부 네트워크: `http://[외부IP]:8000`

### PWA 설정 (선택사항)
```html
<!-- manifest.json -->
{
  "name": "라틴댄스 파티",
  "short_name": "라틴댄스",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#ff6b6b"
}
```

## 🆘 문제 해결

### 자주 발생하는 문제

1. **포트포워딩이 안 될 때**
   - 공유기 재부팅
   - 포트 번호 변경 (8080 등)
   - ISP에서 포트 차단 여부 확인

2. **외부에서 접속이 안 될 때**
   - 방화벽 설정 확인
   - 포트포워딩 설정 확인
   - 외부 IP 변경 확인

3. **서버가 자주 끊어질 때**
   - PC 전원 설정 확인
   - 자동 재시작 스크립트 설정
   - 네트워크 안정성 확인

## 📊 성능 최적화

### 서버 성능 개선
1. **정적 파일 캐싱**: 브라우저 캐싱 설정
2. **이미지 최적화**: WebP 형식 사용
3. **코드 압축**: CSS/JS 파일 압축
4. **CDN 사용**: 정적 파일 CDN 배포

---

**개인 PC 서버로 라틴댄스 파티 홍보 웹앱을 운영할 수 있습니다! 🎉** 