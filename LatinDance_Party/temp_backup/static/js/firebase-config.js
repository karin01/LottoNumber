// Firebase 설정 파일
// 실제 사용 시 본인의 Firebase 프로젝트 설정값으로 변경해야 합니다.

// Firebase 설정 객체 (실제 Firebase 프로젝트 설정으로 업데이트)
const firebaseConfig = {
    // 여기에 본인의 Firebase 프로젝트 설정을 입력하세요
    // Firebase 콘솔에서 "프로젝트 설정" > "일반" 탭에서 확인할 수 있습니다
    apiKey: "AIzaSyANAoSBtvO4yUBQi-ljSzK-d0IYSMSbACA",
    authDomain: "share-note-ef791.firebaseapp.com",
    projectId: "share-note-ef791",
    storageBucket: "share-note-ef791.firebasestorage.app",
    messagingSenderId: "649016781496",
    appId: "1:649016781496:web:95e10d4c29ecdaf8d3e24d",
    measurementId: "G-P4TKC300N1"
};

// Firebase 초기화 상태 추적
let isFirebaseInitialized = false;
let initializationInProgress = false;

// Firebase 초기화 함수
function initializeFirebase() {
    // 이미 초기화된 경우 중복 실행 방지
    if (isFirebaseInitialized) {
        console.log('Firebase가 이미 초기화되어 있습니다.');
        return true;
    }
    
    // 초기화 진행 중인 경우 중복 실행 방지
    if (initializationInProgress) {
        console.log('Firebase 초기화가 이미 진행 중입니다.');
        return false;
    }
    
    initializationInProgress = true;
    
    try {
        console.log('Firebase 초기화 시작...');
        
        // Firebase SDK가 로드되었는지 확인
        if (typeof firebase === 'undefined') {
            console.error('Firebase SDK가 로드되지 않았습니다.');
            initializationInProgress = false;
            return false;
        }
        
        // Firebase 앱 초기화
        if (!firebase.apps.length) {
            firebase.initializeApp(firebaseConfig);
            console.log('Firebase 앱 초기화 완료');
        }
        
        // Firestore 데이터베이스 초기화
        window.db = firebase.firestore();
        
        // Firebase Storage 초기화
        window.storage = firebase.storage();
        
        // Firebase Auth 초기화
        window.auth = firebase.auth();
        
        // Firestore 함수들 전역으로 설정
        window.addDoc = firebase.firestore().collection('dummy').add;
        window.getDocs = firebase.firestore().collection('dummy').get;
        window.collection = firebase.firestore().collection;
        
        // 주요 함수들을 전역으로 노출
        window.loadPartyData = loadPartyData;
        window.savePartyData = savePartyData;
        window.updatePartyData = updatePartyData;
        window.deletePartyData = deletePartyData;
        window.uploadImage = uploadImage;
        
        // 초기화 완료 표시
        isFirebaseInitialized = true;
        initializationInProgress = false;
        console.log('Firebase가 성공적으로 초기화되었습니다.');
        return true;
    } catch (error) {
        console.error('Firebase 초기화 중 오류 발생:', error);
        initializationInProgress = false;
        
        // 개발 모드에서는 로컬 스토리지 사용 (테스트용)
        if (!firebaseConfig.apiKey || firebaseConfig.apiKey === "YOUR_API_KEY") {
            console.warn('Firebase 설정이 없습니다. 로컬 스토리지 모드로 전환합니다.');
            window.useLocalStorage = true;
            isFirebaseInitialized = true;
            return true;
        }
        
        return false;
    }
}

// 파티 데이터 저장 함수
async function savePartyData(partyData) {
    try {
        if (window.useLocalStorage) {
            // 로컬 스토리지 사용 (개발/테스트용)
            const parties = getLocalParties();
            partyData.id = Date.now().toString();
            partyData.createdAt = new Date().toISOString();
            partyData.likes = 0;
            partyData.likedBy = [];
            partyData.comments = [];
            partyData.gallery = [];
            parties.push(partyData);
            localStorage.setItem('latinDanceParties', JSON.stringify(parties));
            return partyData.id;
        } else {
            // Firestore에 데이터 저장
            const docRef = await db.collection('parties').add({
                ...partyData,
                createdAt: firebase.firestore.FieldValue.serverTimestamp(),
                likes: 0,
                likedBy: [],
                comments: [],
                gallery: []
            });
            return docRef.id;
        }
    } catch (error) {
        console.error('파티 데이터 저장 중 오류:', error);
        throw error;
    }
}

// 파티 데이터 불러오기 함수
async function loadPartyData(filters = {}) {
    try {
        if (window.useLocalStorage) {
            // 로컬 스토리지에서 데이터 불러오기
            let parties = getLocalParties();
            
            // 필터 적용
            if (filters.region) {
                parties = parties.filter(party => party.region === filters.region);
            }
            if (filters.date) {
                parties = parties.filter(party => party.date === filters.date);
            }
            
            // 날짜순 정렬 (최신순)
            parties.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
            
            return parties;
        } else {
            // Firestore에서 데이터 불러오기 (성능 최적화)
            console.log('Firestore에서 파티 데이터 로드 시작');
            const startTime = Date.now();
            
            let query = db.collection('parties');
            
            // 필터 적용 (복합 인덱스 활용)
            if (filters.region && filters.date) {
                query = query.where('region', '==', filters.region)
                           .where('date', '==', filters.date);
            } else if (filters.region) {
                query = query.where('region', '==', filters.region);
            } else if (filters.date) {
                query = query.where('date', '==', filters.date);
            }
            
            // 날짜순 정렬 및 제한 (최대 50개)
            query = query.orderBy('createdAt', 'desc').limit(50);
            
            const snapshot = await query.get();
            const parties = [];
            
            snapshot.forEach(doc => {
                parties.push({
                    id: doc.id,
                    ...doc.data()
                });
            });
            
            const endTime = Date.now();
            console.log(`Firestore 쿼리 완료: ${endTime - startTime}ms, ${parties.length}개 파티 로드`);
            
            return parties;
        }
    } catch (error) {
        console.error('파티 데이터 불러오기 중 오류:', error);
        throw error;
    }
}

// 이미지 업로드 함수
async function uploadImage(file) {
    try {
        if (window.useLocalStorage) {
            // 로컬 스토리지 모드에서는 base64로 변환
            return new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.onload = (e) => resolve(e.target.result);
                reader.onerror = reject;
                reader.readAsDataURL(file);
            });
        } else {
            // Firebase Storage에 업로드
            const storageRef = storage.ref();
            const imageRef = storageRef.child(`party-posters/${Date.now()}_${file.name}`);
            
            const snapshot = await imageRef.put(file);
            const downloadURL = await snapshot.ref.getDownloadURL();
            
            return downloadURL;
        }
    } catch (error) {
        console.error('이미지 업로드 중 오류:', error);
        throw error;
    }
}

// 파티 데이터 업데이트 함수
async function updatePartyData(partyId, updateData) {
    try {
        if (window.useLocalStorage) {
            // 로컬 스토리지 업데이트
            const parties = getLocalParties();
            const partyIndex = parties.findIndex(party => party.id === partyId);
            
            if (partyIndex !== -1) {
                parties[partyIndex] = { ...parties[partyIndex], ...updateData };
                localStorage.setItem('latinDanceParties', JSON.stringify(parties));
                return true;
            }
            return false;
        } else {
            // Firestore 업데이트
            await db.collection('parties').doc(partyId).update(updateData);
            return true;
        }
    } catch (error) {
        console.error('파티 데이터 업데이트 중 오류:', error);
        throw error;
    }
}

// 파티 데이터 삭제 함수
async function deletePartyData(partyId) {
    try {
        if (window.useLocalStorage) {
            // 로컬 스토리지에서 삭제
            const parties = getLocalParties();
            const filteredParties = parties.filter(party => party.id !== partyId);
            localStorage.setItem('latinDanceParties', JSON.stringify(filteredParties));
            return true;
        } else {
            // Firestore에서 삭제
            await db.collection('parties').doc(partyId).delete();
            return true;
        }
    } catch (error) {
        console.error('파티 데이터 삭제 중 오류:', error);
        throw error;
    }
}

// 좋아요 토글 함수
async function toggleLike(partyId, userId = 'anonymous') {
    try {
        if (window.useLocalStorage) {
            // 로컬 스토리지에서 좋아요 토글
            const parties = getLocalParties();
            const partyIndex = parties.findIndex(party => party.id === partyId);
            
            if (partyIndex !== -1) {
                const party = parties[partyIndex];
                if (!party.likedBy) party.likedBy = [];
                
                const likedIndex = party.likedBy.indexOf(userId);
                if (likedIndex === -1) {
                    // 좋아요 추가
                    party.likedBy.push(userId);
                    party.likes = party.likedBy.length;
                } else {
                    // 좋아요 취소
                    party.likedBy.splice(likedIndex, 1);
                    party.likes = party.likedBy.length;
                }
                
                localStorage.setItem('latinDanceParties', JSON.stringify(parties));
                return { liked: likedIndex === -1, likes: party.likes };
            }
            return null;
        } else {
            // Firestore에서 좋아요 토글
            const partyRef = db.collection('parties').doc(partyId);
            const partyDoc = await partyRef.get();
            
            if (partyDoc.exists) {
                const party = partyDoc.data();
                const likedBy = party.likedBy || [];
                const likedIndex = likedBy.indexOf(userId);
                
                if (likedIndex === -1) {
                    // 좋아요 추가
                    await partyRef.update({
                        likedBy: firebase.firestore.FieldValue.arrayUnion(userId),
                        likes: firebase.firestore.FieldValue.increment(1)
                    });
                    return { liked: true, likes: (party.likes || 0) + 1 };
                } else {
                    // 좋아요 취소
                    await partyRef.update({
                        likedBy: firebase.firestore.FieldValue.arrayRemove(userId),
                        likes: firebase.firestore.FieldValue.increment(-1)
                    });
                    return { liked: false, likes: Math.max((party.likes || 0) - 1, 0) };
                }
            }
            return null;
        }
    } catch (error) {
        console.error('좋아요 토글 중 오류:', error);
        throw error;
    }
}

// 댓글 추가 함수
async function addComment(partyId, commentData) {
    try {
        const comment = {
            id: Date.now().toString(),
            text: commentData.text,
            author: commentData.author || 'Anonymous',
            createdAt: new Date().toISOString(),
            likes: 0,
            likedBy: []
        };
        
        if (window.useLocalStorage) {
            // 로컬 스토리지에 댓글 추가
            const parties = getLocalParties();
            const partyIndex = parties.findIndex(party => party.id === partyId);
            
            if (partyIndex !== -1) {
                if (!parties[partyIndex].comments) parties[partyIndex].comments = [];
                parties[partyIndex].comments.push(comment);
                localStorage.setItem('latinDanceParties', JSON.stringify(parties));
                return comment;
            }
            return null;
        } else {
            // Firestore에 댓글 추가
            await db.collection('parties').doc(partyId).update({
                comments: firebase.firestore.FieldValue.arrayUnion(comment)
            });
            return comment;
        }
    } catch (error) {
        console.error('댓글 추가 중 오류:', error);
        throw error;
    }
}

// 갤러리 이미지 추가 함수
async function addGalleryImage(partyId, imageFile) {
    try {
        // 이미지 업로드
        const imageUrl = await uploadImage(imageFile);
        
        const galleryItem = {
            id: Date.now().toString(),
            url: imageUrl,
            caption: '',
            uploadedAt: new Date().toISOString()
        };
        
        if (window.useLocalStorage) {
            // 로컬 스토리지에 갤러리 이미지 추가
            const parties = getLocalParties();
            const partyIndex = parties.findIndex(party => party.id === partyId);
            
            if (partyIndex !== -1) {
                if (!parties[partyIndex].gallery) parties[partyIndex].gallery = [];
                parties[partyIndex].gallery.push(galleryItem);
                localStorage.setItem('latinDanceParties', JSON.stringify(parties));
                return galleryItem;
            }
            return null;
        } else {
            // Firestore에 갤러리 이미지 추가
            await db.collection('parties').doc(partyId).update({
                gallery: firebase.firestore.FieldValue.arrayUnion(galleryItem)
            });
            return galleryItem;
        }
    } catch (error) {
        console.error('갤러리 이미지 추가 중 오류:', error);
        throw error;
    }
}

// 로컬 스토리지 헬퍼 함수들
function getLocalParties() {
    const parties = localStorage.getItem('latinDanceParties');
    return parties ? JSON.parse(parties) : [];
}

// 에러 처리 함수
function handleFirebaseError(error) {
    console.error('Firebase 에러:', error);
    
    let errorMessage = '알 수 없는 오류가 발생했습니다.';
    
    if (error.code) {
        switch (error.code) {
            case 'permission-denied':
                errorMessage = '권한이 없습니다. 다시 시도해주세요.';
                break;
            case 'unavailable':
                errorMessage = '서비스를 사용할 수 없습니다. 잠시 후 다시 시도해주세요.';
                break;
            case 'deadline-exceeded':
                errorMessage = '요청 시간이 초과되었습니다. 다시 시도해주세요.';
                break;
            default:
                errorMessage = `오류: ${error.message}`;
        }
    }
    
    return errorMessage;
}

// Firebase 연결 상태 확인
function checkFirebaseConnection() {
    if (window.useLocalStorage) {
        return { connected: true, mode: 'local' };
    }
    
    try {
        return { 
            connected: !!window.db && !!window.storage, 
            mode: 'firebase' 
        };
    } catch (error) {
        return { connected: false, mode: 'error', error: error.message };
    }
}

// 페이지 로드 시 Firebase 초기화
document.addEventListener('DOMContentLoaded', function() {
    const initialized = initializeFirebase();
    
    if (initialized) {
        console.log('Firebase 초기화 완료');
        
        // 연결 상태 표시
        const connectionStatus = checkFirebaseConnection();
        console.log('연결 상태:', connectionStatus);
        
        // 개발 모드 알림
        if (connectionStatus.mode === 'local') {
            console.warn('⚠️ 개발 모드: 로컬 스토리지를 사용하고 있습니다.');
            console.warn('실제 배포 시 firebase-config.js에서 Firebase 설정을 업데이트하세요.');
        }
    } else {
        console.error('Firebase 초기화 실패');
    }
});

// 전역 함수들을 window 객체에 추가 (main.js에서 사용하기 위해)
window.initializeFirebase = initializeFirebase;
window.savePartyData = savePartyData;
window.loadPartyData = loadPartyData;
window.uploadImage = uploadImage;
window.updatePartyData = updatePartyData;
window.deletePartyData = deletePartyData;
window.toggleLike = toggleLike;
window.addComment = addComment;
window.addGalleryImage = addGalleryImage;
window.getLocalParties = getLocalParties;
window.handleFirebaseError = handleFirebaseError;
window.checkFirebaseConnection = checkFirebaseConnection;

console.log('Firebase 설정 파일이 로드되었습니다.'); 