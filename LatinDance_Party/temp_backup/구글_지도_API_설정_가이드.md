# 🗺️ 구글 지도 API 설정 가이드

## 📋 **필요한 설정**

라틴 바 지도 기능을 사용하려면 구글 지도 API 키가 필요합니다.

### **1. 구글 클라우드 콘솔에서 API 키 생성**

1. [Google Cloud Console](https://console.cloud.google.com/)에 접속
2. 새 프로젝트 생성 또는 기존 프로젝트 선택
3. **API 및 서비스** > **라이브러리**로 이동
4. 다음 API들을 활성화:
   - **Maps JavaScript API**
   - **Geocoding API**
   - **Places API**

### **2. API 키 생성**

1. **API 및 서비스** > **사용자 인증 정보**로 이동
2. **사용자 인증 정보 만들기** > **API 키** 클릭
3. 생성된 API 키를 복사

### **3. API 키 제한 설정 (보안)**

1. 생성된 API 키 클릭
2. **애플리케이션 제한사항**에서 **HTTP 리퍼러(웹사이트)** 선택
3. **웹사이트 제한사항**에 다음 도메인 추가:
   - `https://share-note-ef791.web.app/*`
   - `http://localhost:5000/*` (개발용)

### **4. 코드에 API 키 적용**

`LatinDance_Party/index.html` 파일에서 다음 줄을 찾아 API 키를 교체:

```html
<script src="https://maps.googleapis.com/maps/api/js?key=YOUR_GOOGLE_MAPS_API_KEY&libraries=places"></script>
```

`YOUR_GOOGLE_MAPS_API_KEY` 부분을 실제 API 키로 교체:

```html
<script src="https://maps.googleapis.com/maps/api/js?key=AIzaSyCk9bdA2phT6IBvqnEEx8oMqyoTnNFq69U&libraries=places"></script>
```

### **✅ API 키 설정 완료!**

현재 다음 API들이 활성화되어 있습니다:
- **Maps JavaScript API** ✅
- **Geocoding API** ✅
- **Places API** ✅
- **Geolocation API** ✅

## 🚀 **기능 설명**

### **라틴 바 지도 기능**

1. **자동 바 정보 추출**: 파티 등록 시 입력된 바 정보를 자동으로 추출
2. **지도 표시**: 구글 지도에 라틴 바 위치를 마커로 표시
3. **필터링**: 지역별, 검색어별로 바 목록 필터링
4. **상세 정보**: 바 클릭 시 상세 정보 모달 표시
5. **길찾기**: 구글 맵스로 길찾기 기능
6. **공유 기능**: 바 정보를 카카오톡 등으로 공유

### **데이터 구조**

```javascript
{
  id: "바이름_주소",
  name: "바 이름",
  address: "상세주소",
  region: "지역",
  location: "상세 위치",
  contact: "연락처",
  createdAt: "생성일",
  partyCount: "등록된 파티 수",
  parties: ["파티ID 배열"]
}
```

## 💡 **주의사항**

1. **API 키 보안**: API 키를 공개 저장소에 올리지 마세요
2. **사용량 제한**: 무료 사용량을 초과하면 요금이 발생할 수 있습니다
3. **도메인 제한**: 보안을 위해 허용된 도메인에서만 API를 사용하세요

## 🔧 **문제 해결**

### **지도가 표시되지 않는 경우**
1. API 키가 올바르게 설정되었는지 확인
2. 브라우저 콘솔에서 오류 메시지 확인
3. API가 활성화되었는지 확인

### **마커가 표시되지 않는 경우**
1. 파티 데이터에 바 이름과 주소가 있는지 확인
2. 주소가 정확한지 확인
3. Geocoding API가 활성화되었는지 확인 