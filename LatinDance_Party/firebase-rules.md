# Firebase 보안 규칙 설정

## Firestore 보안 규칙

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
    
    // 갤러리 이미지 데이터
    match /galleries/{galleryId} {
      allow read: if true;
      allow write: if request.auth != null;
    }
    
    // 댓글 데이터
    match /comments/{commentId} {
      allow read: if true;
      allow write: if request.auth != null;
    }
  }
}
```

## Storage 보안 규칙

```javascript
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    // 이미지 파일 업로드 (인증된 사용자만)
    match /images/{allPaths=**} {
      allow read: if true;
      allow write: if request.auth != null 
        && request.resource.size < 5 * 1024 * 1024  // 5MB 제한
        && request.resource.contentType.matches('image/.*');
    }
    
    // 포스터 이미지
    match /posters/{allPaths=**} {
      allow read: if true;
      allow write: if request.auth != null 
        && request.resource.size < 5 * 1024 * 1024  // 5MB 제한
        && request.resource.contentType.matches('image/.*');
    }
  }
}
```

## 설정 방법

1. Firebase Console → Firestore Database → Rules 탭
2. 위의 Firestore 규칙을 복사하여 붙여넣기
3. Firebase Console → Storage → Rules 탭
4. 위의 Storage 규칙을 복사하여 붙여넣기
5. "Publish" 버튼 클릭

## 보안 규칙 설명

### Firestore 규칙
- **파티 데이터**: 모든 사용자가 읽기 가능, 로그인한 사용자만 쓰기 가능
- **사용자 데이터**: 본인만 읽기/쓰기 가능
- **갤러리/댓글**: 모든 사용자가 읽기 가능, 로그인한 사용자만 쓰기 가능

### Storage 규칙
- **이미지 파일**: 모든 사용자가 읽기 가능
- **업로드 제한**: 로그인한 사용자만, 5MB 이하, 이미지 파일만
- **파일 타입 검증**: 이미지 파일만 허용 