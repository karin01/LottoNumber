# Firebase 바 데이터 마이그레이션 가이드

## 1. 마이그레이션 준비

### Firebase 프로젝트 확인
- 프로젝트 ID: `share-note-ef791`
- Firestore 데이터베이스 활성화 필요

### Firestore 보안 규칙 설정
Firebase Console → Firestore Database → Rules에서 다음 규칙 설정:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // 라틴바 컬렉션 - 읽기/쓰기 모두 허용
    match /latinBars/{document} {
      allow read, write: if true;
    }
    
    // 기존 파티 컬렉션 규칙
    match /parties/{document} {
      allow read, write: if true;
    }
  }
}
```

## 2. 마이그레이션 실행

### 브라우저 콘솔에서 실행
1. 웹사이트 접속
2. F12 → Console 탭
3. 다음 명령어 실행:

```javascript
// CSV 데이터를 Firebase로 마이그레이션
await migrateCSVToFirestore();

// 마이그레이션 결과 확인
await getBarsStats();
```

### 예상 결과
```
마이그레이션 완료: 28개 바 추가됨
바 통계: {
  totalBars: 28,
  regionStats: {
    "홍대": 12,
    "강남": 12,
    "강동": 1,
    "광주": 1,
    "포항": 1
  },
  lastUpdated: "2025-01-XX..."
}
```

## 3. 기능 테스트

### 빠 이름 검색 테스트
1. 파티 등록 폼에서 "빠 이름" 필드 클릭
2. "보니따" 입력
3. 자동완성 목록에서 "보니따" 선택
4. 주소가 자동으로 채워지는지 확인

### 새 빠 추가 테스트
1. 존재하지 않는 빠 이름 입력 (예: "테스트바")
2. "➕ 새 빠 추가" 옵션 클릭
3. 주소와 지역 입력
4. Firebase에 저장되는지 확인

### 지역별 검색 테스트
```javascript
// 콘솔에서 테스트
const hongdaeBars = await window.latinBarsManager.getBarsByRegion('홍대');
console.log('홍대 바 목록:', hongdaeBars);

const gangnamBars = await window.latinBarsManager.getBarsByRegion('강남');
console.log('강남 바 목록:', gangnamBars);
```

## 4. 데이터 관리

### 바 정보 수정
```javascript
// 바 정보 업데이트
await window.latinBarsManager.updateBar('바ID', {
    address: '새로운 주소',
    note: '수정된 메모'
});
```

### 바 삭제
```javascript
// 바 삭제
await window.latinBarsManager.deleteBar('바ID');
```

### 전체 바 목록 조회
```javascript
// 모든 바 조회
const allBars = await window.latinBarsManager.getAllBars();
console.log('전체 바 목록:', allBars);
```

## 5. 장점

### ✅ Firebase 기반 장점
- **실시간 동기화**: 여러 사용자가 동시에 새 빠 추가 가능
- **자동 백업**: Firebase가 자동으로 데이터 백업
- **확장성**: 사용자가 늘어나도 안정적
- **검색 성능**: Firestore 인덱스로 빠른 검색
- **중복 방지**: 같은 이름의 바 중복 등록 방지

### ✅ 폴백 시스템
- Firebase 실패 시 로컬 CSV 데이터로 자동 폴백
- 네트워크 문제나 Firebase 장애 시에도 정상 동작

## 6. 문제 해결

### 마이그레이션 실패 시
```javascript
// 에러 확인
console.error('마이그레이션 에러:', error);

// 수동으로 개별 바 추가
await window.latinBarsManager.addBar({
    region: '홍대',
    name: '테스트바',
    address: '테스트 주소',
    note: '테스트 메모'
});
```

### 검색이 안 될 때
1. Firebase 연결 상태 확인
2. 브라우저 콘솔에서 에러 메시지 확인
3. 로컬 데이터로 폴백되는지 확인

### 새 바 추가가 안 될 때
1. Firebase 권한 확인
2. 네트워크 연결 상태 확인
3. 로컬 폴백으로 동작하는지 확인 