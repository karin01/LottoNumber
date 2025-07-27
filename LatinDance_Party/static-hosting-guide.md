# 정적 호스팅 배포 가이드 (Firebase만 사용)

## 1. Firebase Hosting 설정

### Firebase CLI 설치
```bash
npm install -g firebase-tools
```

### 로그인 및 프로젝트 설정
```bash
firebase login
firebase use share-note-ef791
```

## 2. 정적 파일 최적화

### 불필요한 파일 제거
- `backend/` 폴더 제거 (Firebase Functions 사용)
- `server-*.bat` 파일들 제거
- `*.py` 파일들 제거

### 필수 파일만 유지
```
static/
├── index.html
├── css/
│   └── style.css
├── js/
│   ├── main.js
│   ├── firebase-config.js
│   └── googlemap-init.js
└── Latin_Bar_LIST.csv
```

## 3. Firebase Functions 설정 (선택사항)

### functions 폴더 생성
```bash
firebase init functions
```

### 백엔드 기능을 Functions로 이전
- 파티 CRUD 기능
- 댓글 기능
- 이미지 업로드 기능

## 4. 배포 실행

### 호스팅 배포
```bash
firebase deploy --only hosting
```

### Functions 배포 (선택사항)
```bash
firebase deploy --only functions
```

## 5. 도메인 연결

### Firebase Console에서 설정
1. Firebase Console → Hosting → Custom domains
2. `latinmat.co.kr` 추가
3. DNS 설정 안내 확인

### 가비아 DNS 설정
```
Type: A
Name: @
Value: 151.101.1.195

Type: A
Name: @  
Value: 151.101.65.195

Type: CNAME
Name: www
Value: latinmat.co.kr
```

## 6. 장점
- ✅ 무료 호스팅
- ✅ 자동 SSL 인증서
- ✅ 글로벌 CDN
- ✅ 빠른 로딩 속도
- ✅ 간단한 배포

## 7. 단점
- ❌ 백엔드 서버 없음 (Firebase Functions 필요)
- ❌ 복잡한 서버 로직 제한적

## 8. 추천 구성
현재 프로젝트는 Firebase 기반으로 잘 구성되어 있어서, 
Firebase Hosting + Firestore + Storage 조합을 추천합니다. 