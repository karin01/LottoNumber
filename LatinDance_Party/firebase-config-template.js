// Firebase 설정 템플릿
// 실제 Firebase 프로젝트 정보로 교체하여 사용하세요

const firebaseConfig = {
  apiKey: "your-api-key-here",
  authDomain: "your-project-id.firebaseapp.com",
  projectId: "your-project-id",
  storageBucket: "your-project-id.appspot.com",
  messagingSenderId: "123456789",
  appId: "your-app-id-here"
};

// Firebase 초기화
function initializeFirebase() {
    try {
        // Firebase 앱 초기화
        if (!firebase.apps.length) {
            firebase.initializeApp(firebaseConfig);
        }
        
        // Firestore 데이터베이스 초기화
        window.db = firebase.firestore();
        
        // Firebase Storage 초기화
        window.storage = firebase.storage();
        
        // Firebase Auth 초기화
        window.auth = firebase.auth();
        
        console.log('Firebase가 성공적으로 초기화되었습니다.');
        console.log('Firebase Auth 초기화 완료');
        
        return true;
    } catch (error) {
        console.error('Firebase 초기화 중 오류 발생:', error);
        return false;
    }
}

// 개발 모드 확인 (로컬에서 실행 중인지 확인)
function checkDevelopmentMode() {
    const isLocalhost = window.location.hostname === 'localhost' || 
                       window.location.hostname === '127.0.0.1' ||
                       window.location.protocol === 'file:';
    
    if (isLocalhost) {
        console.log('개발 모드 감지: 로컬 스토리지를 사용합니다.');
        window.useLocalStorage = true;
        return true;
    }
    
    return false;
}

// Firebase 초기화 실행
if (typeof firebase !== 'undefined') {
    initializeFirebase();
} else {
    console.error('Firebase SDK가 로드되지 않았습니다.');
}

// 설정 완료 후 이 파일을 firebase-config.js로 이름 변경하세요 