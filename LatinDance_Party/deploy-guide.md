# 🚀 라틴댄스 파티 홍보 웹앱 - 가비아 호스팅 배포 가이드

## 📋 배포 전 준비사항

### 1. 가비아 호스팅 계정 준비
- 가비아 호스팅 계정 생성 (https://www.gabia.com)
- 웹호스팅 서비스 신청 (PHP 지원 호스팅 권장)
- FTP 접속 정보 확인

### 2. Firebase 프로젝트 설정
- Firebase Console에서 프로젝트 생성
- 웹 앱 등록 및 설정
- Authentication, Firestore, Storage 활성화
- 보안 규칙 설정

## 📁 배포용 파일 구조

```
latin-dance-party/
├── index.html              # 메인 페이지
├── css/
│   └── style.css           # 스타일시트
├── js/
│   ├── firebase-config.js  # Firebase 설정
│   ├── main.js            # 메인 JavaScript
│   └── googlemap-init.js  # 구글맵 초기화
├── images/                 # 이미지 파일들
├── Seoul_Latin_Bar.csv    # 서울 라틴바 데이터
└── README.md              # 프로젝트 설명
```

## 🔧 배포 단계

### 1단계: Firebase 설정 업데이트

#### Firebase Console에서:
1. 프로젝트 생성
2. 웹 앱 추가
3. Authentication → Sign-in method → Google 활성화
4. Firestore Database 생성
5. Storage 생성
6. 보안 규칙 설정

#### firebase-config.js 업데이트:
```javascript
// Firebase 설정 정보 (실제 프로젝트 정보로 교체)
const firebaseConfig = {
  apiKey: "your-api-key",
  authDomain: "your-project.firebaseapp.com",
  projectId: "your-project-id",
  storageBucket: "your-project.appspot.com",
  messagingSenderId: "123456789",
  appId: "your-app-id"
};
```

### 2단계: 구글맵 API 키 설정

#### Google Cloud Console에서:
1. 프로젝트 생성
2. Maps JavaScript API 활성화
3. API 키 생성 및 제한 설정

#### googlemap-init.js 업데이트:
```javascript
// 구글맵 API 키 (실제 API 키로 교체)
<script src="https://maps.googleapis.com/maps/api/js?key=YOUR_GOOGLE_MAPS_API_KEY&libraries=places"></script>
```

### 3단계: 파일 업로드

#### FTP 클라이언트 사용:
1. FileZilla 또는 다른 FTP 클라이언트 설치
2. 가비아 호스팅 FTP 정보로 연결
3. public_html 폴더에 파일 업로드

#### 업로드할 파일들:
- `index.html` → `public_html/index.html`
- `css/` 폴더 전체 → `public_html/css/`
- `js/` 폴더 전체 → `public_html/js/`
- `images/` 폴더 전체 → `public_html/images/`
- `Seoul_Latin_Bar.csv` → `public_html/Seoul_Latin_Bar.csv`

### 4단계: 도메인 설정

#### 가비아 호스팅 관리자에서:
1. 도메인 연결 설정
2. SSL 인증서 설치 (HTTPS 활성화)
3. DNS 설정 확인

## 🔒 보안 설정

### Firebase 보안 규칙

#### Firestore 보안 규칙:
```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // 파티 데이터 읽기 (모든 사용자)
    match /parties/{partyId} {
      allow read: if true;
      allow write: if request.auth != null;
    }
    
    // 사용자별 데이터
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
  }
}
```

#### Storage 보안 규칙:
```javascript
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    // 이미지 파일 업로드 (인증된 사용자만)
    match /images/{allPaths=**} {
      allow read: if true;
      allow write: if request.auth != null;
    }
  }
}
```

## 🌐 배포 후 확인사항

### 1. 기능 테스트
- [ ] 메인 페이지 로딩 확인
- [ ] 구글 로그인 기능 테스트
- [ ] 파티 등록/수정/삭제 기능 테스트
- [ ] 이미지 업로드 기능 테스트
- [ ] 모바일 반응형 확인

### 2. 성능 최적화
- [ ] 이미지 압축 및 최적화
- [ ] CSS/JS 파일 압축
- [ ] 캐싱 설정
- [ ] 로딩 속도 확인

### 3. 보안 확인
- [ ] HTTPS 연결 확인
- [ ] Firebase 보안 규칙 테스트
- [ ] API 키 노출 여부 확인

## 📱 추가 최적화

### 1. PWA (Progressive Web App) 설정
- manifest.json 파일 생성
- 서비스 워커 등록
- 오프라인 기능 추가

### 2. SEO 최적화
- 메타 태그 추가
- Open Graph 태그 설정
- 사이트맵 생성

### 3. 분석 도구 추가
- Google Analytics 설정
- Firebase Analytics 설정

## 🆘 문제 해결

### 자주 발생하는 문제들:

1. **Firebase 초기화 오류**
   - API 키와 도메인 설정 확인
   - Firebase 프로젝트 설정 재확인

2. **구글맵 로딩 실패**
   - API 키 유효성 확인
   - 도메인 제한 설정 확인

3. **이미지 업로드 실패**
   - Storage 보안 규칙 확인
   - 파일 크기 제한 확인

4. **로그인 기능 오류**
   - Authentication 설정 확인
   - 도메인 허용 목록 확인

## 📞 지원

배포 과정에서 문제가 발생하면:
1. 브라우저 개발자 도구 콘솔 확인
2. Firebase Console 로그 확인
3. 가비아 호스팅 고객센터 문의

---

**배포 완료 후 URL을 공유하여 다른 사람들이 라틴댄스 파티를 등록하고 확인할 수 있습니다! 🎉** 