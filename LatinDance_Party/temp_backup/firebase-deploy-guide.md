# Firebase Hosting 배포 가이드

## 1. 사전 준비

### Firebase CLI 설치
```bash
npm install -g firebase-tools
```

### Firebase 로그인
```bash
firebase login
```

## 2. 프로젝트 설정

### 현재 프로젝트 확인
```bash
firebase projects:list
```

### 프로젝트 설정 (이미 설정됨)
```bash
firebase use share-note-ef791
```

## 3. 배포 실행

### 전체 배포
```bash
firebase deploy
```

### 호스팅만 배포
```bash
firebase deploy --only hosting
```

## 4. 도메인 연결

### Firebase Console에서 도메인 추가
1. Firebase Console → Hosting → Custom domains
2. "Add custom domain" 클릭
3. `latinmat.co.kr` 입력
4. DNS 설정 안내에 따라 가비아에서 설정

### 가비아 DNS 설정
가비아 관리자 페이지에서 다음 레코드 추가:

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

## 5. SSL 인증서
Firebase가 자동으로 SSL 인증서를 발급해줍니다.

## 6. 배포 확인
배포 완료 후 `https://latinmat.co.kr`에서 사이트 확인 