// 라틴바 데이터 관리자
// Firebase Firestore를 사용하여 빠 데이터를 동적으로 관리

class LatinBarsManager {
    constructor() {
        this.barsCollection = 'latinBars';
        this.initializeFirebase();
    }

    // Firebase 초기화
    initializeFirebase() {
        if (typeof firebase === 'undefined') {
            console.error('Firebase가 로드되지 않았습니다.');
            return false;
        }
        
        if (!window.db) {
            console.error('Firestore가 초기화되지 않았습니다.');
            return false;
        }
        
        this.db = window.db;
        return true;
    }

    // CSV 데이터를 Firestore로 마이그레이션
    async migrateFromCSV() {
        try {
            console.log('CSV 데이터를 Firestore로 마이그레이션 시작...');
            
            // CSV 파일 읽기
            const response = await fetch('/Latin_Bar_LIST.csv');
            const csvText = await response.text();
            
            // CSV 파싱
            const bars = this.parseCSV(csvText);
            
            // Firestore에 저장
            let successCount = 0;
            for (const bar of bars) {
                try {
                    await this.addBar(bar);
                    successCount++;
                } catch (error) {
                    console.error(`바 추가 실패: ${bar.name}`, error);
                }
            }
            
            console.log(`마이그레이션 완료: ${successCount}/${bars.length}개 성공`);
            return successCount;
            
        } catch (error) {
            console.error('CSV 마이그레이션 실패:', error);
            throw error;
        }
    }

    // CSV 파싱
    parseCSV(csvText) {
        const lines = csvText.trim().split('\n');
        const headers = lines[0].split(',');
        const bars = [];
        
        for (let i = 1; i < lines.length; i++) {
            const values = lines[i].split(',');
            if (values.length >= 3) {
                bars.push({
                    region: values[0].trim(),
                    name: values[1].trim(),
                    address: values[2].trim(),
                    note: values[3] ? values[3].trim() : '',
                    createdAt: new Date().toISOString(),
                    updatedAt: new Date().toISOString()
                });
            }
        }
        
        return bars;
    }

    // 새로운 바 추가
    async addBar(barData) {
        try {
            // 중복 검사
            const existingBar = await this.findBarByName(barData.name);
            if (existingBar) {
                console.log(`이미 존재하는 바: ${barData.name}`);
                return existingBar;
            }
            
            // Firestore에 저장
            const docRef = await this.db.collection(this.barsCollection).add({
                ...barData,
                createdAt: firebase.firestore.FieldValue.serverTimestamp(),
                updatedAt: firebase.firestore.FieldValue.serverTimestamp()
            });
            
            console.log(`새 바 추가됨: ${barData.name} (ID: ${docRef.id})`);
            return { id: docRef.id, ...barData };
            
        } catch (error) {
            console.error('바 추가 실패:', error);
            throw error;
        }
    }

    // 바 이름으로 검색
    async findBarByName(barName) {
        try {
            const snapshot = await this.db.collection(this.barsCollection)
                .where('name', '==', barName)
                .limit(1)
                .get();
            
            if (!snapshot.empty) {
                const doc = snapshot.docs[0];
                return { id: doc.id, ...doc.data() };
            }
            
            return null;
        } catch (error) {
            console.error('바 검색 실패:', error);
            throw error;
        }
    }

    // 지역별 바 목록 조회
    async getBarsByRegion(region) {
        try {
            const snapshot = await this.db.collection(this.barsCollection)
                .where('region', '==', region)
                .orderBy('name')
                .get();
            
            const bars = [];
            snapshot.forEach(doc => {
                bars.push({ id: doc.id, ...doc.data() });
            });
            
            return bars;
        } catch (error) {
            console.error('지역별 바 조회 실패:', error);
            throw error;
        }
    }

    // 모든 바 목록 조회
    async getAllBars() {
        try {
            const snapshot = await this.db.collection(this.barsCollection)
                .orderBy('region')
                .orderBy('name')
                .get();
            
            const bars = [];
            snapshot.forEach(doc => {
                bars.push({ id: doc.id, ...doc.data() });
            });
            
            return bars;
        } catch (error) {
            console.error('전체 바 조회 실패:', error);
            throw error;
        }
    }

    // 바 정보 업데이트
    async updateBar(barId, updateData) {
        try {
            await this.db.collection(this.barsCollection).doc(barId).update({
                ...updateData,
                updatedAt: firebase.firestore.FieldValue.serverTimestamp()
            });
            
            console.log(`바 정보 업데이트됨: ${barId}`);
            return true;
        } catch (error) {
            console.error('바 업데이트 실패:', error);
            throw error;
        }
    }

    // 바 삭제
    async deleteBar(barId) {
        try {
            await this.db.collection(this.barsCollection).doc(barId).delete();
            console.log(`바 삭제됨: ${barId}`);
            return true;
        } catch (error) {
            console.error('바 삭제 실패:', error);
            throw error;
        }
    }

    // 빠 이름 자동완성 검색
    async searchBars(query) {
        try {
            if (!query || query.length < 2) {
                return [];
            }
            
            const snapshot = await this.db.collection(this.barsCollection)
                .where('name', '>=', query)
                .where('name', '<=', query + '\uf8ff')
                .limit(10)
                .get();
            
            const bars = [];
            snapshot.forEach(doc => {
                bars.push({ id: doc.id, ...doc.data() });
            });
            
            return bars;
        } catch (error) {
            console.error('바 검색 실패:', error);
            throw error;
        }
    }

    // 지역별 빠 이름 검색
    async searchBarsByRegion(query, region) {
        try {
            if (!query || query.length < 2) {
                return [];
            }
            
            const snapshot = await this.db.collection(this.barsCollection)
                .where('region', '==', region)
                .where('name', '>=', query)
                .where('name', '<=', query + '\uf8ff')
                .limit(10)
                .get();
            
            const bars = [];
            snapshot.forEach(doc => {
                bars.push({ id: doc.id, ...doc.data() });
            });
            
            return bars;
        } catch (error) {
            console.error('지역별 바 검색 실패:', error);
            throw error;
        }
    }

    // 통계 정보 조회
    async getStats() {
        try {
            const snapshot = await this.db.collection(this.barsCollection).get();
            const totalBars = snapshot.size;
            
            // 지역별 통계
            const regionStats = {};
            snapshot.forEach(doc => {
                const region = doc.data().region;
                regionStats[region] = (regionStats[region] || 0) + 1;
            });
            
            return {
                totalBars,
                regionStats,
                lastUpdated: new Date().toISOString()
            };
        } catch (error) {
            console.error('통계 조회 실패:', error);
            throw error;
        }
    }
}

// 전역 인스턴스 생성
window.latinBarsManager = new LatinBarsManager();

// 개발자용 마이그레이션 함수 (콘솔에서 실행 가능)
window.migrateCSVToFirestore = async function() {
    try {
        const result = await window.latinBarsManager.migrateFromCSV();
        console.log(`마이그레이션 완료: ${result}개 바 추가됨`);
        return result;
    } catch (error) {
        console.error('마이그레이션 실패:', error);
        throw error;
    }
};

// 개발자용 통계 조회 함수
window.getBarsStats = async function() {
    try {
        const stats = await window.latinBarsManager.getStats();
        console.log('바 통계:', stats);
        return stats;
    } catch (error) {
        console.error('통계 조회 실패:', error);
        throw error;
    }
}; 