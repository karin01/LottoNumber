// 라틴 바 지도 관련 변수들
let googleMap = null;
let mapMarkers = [];
let allBars = [];

// 라틴 바 지도 초기화
async function initializeLatinBarsMap() {
    console.log('=== 라틴 바 지도 초기화 시작 ===');
    
    try {
        // 기존 파티 데이터에서 바 정보 추출
        await extractBarsFromParties();
        
        // 구글 지도 초기화
        initializeGoogleMap();
        
        // 바 목록 표시
        displayBarsList();
        
        console.log('라틴 바 지도 초기화 완료');
    } catch (error) {
        console.error('라틴 바 지도 초기화 실패:', error);
    }
}

// 파티 데이터에서 바 정보 추출
async function extractBarsFromParties() {
    console.log('파티 데이터에서 바 정보 추출 중...');
    
    try {
        // Firebase에서 파티 데이터 가져오기
        const partiesSnapshot = await db.collection('parties').get();
        const bars = new Map(); // 중복 제거를 위해 Map 사용
        
        partiesSnapshot.forEach(doc => {
            const party = doc.data();
            
            // 바 이름과 주소가 있는 경우만 추가
            if (party.barName && party.address) {
                const barKey = `${party.barName}_${party.address}`;
                
                if (!bars.has(barKey)) {
                    bars.set(barKey, {
                        id: barKey,
                        name: party.barName,
                        address: party.address,
                        region: party.region || '기타',
                        location: party.location || '',
                        contact: party.contact || '',
                        createdAt: party.createdAt,
                        partyCount: 1,
                        parties: [party.id]
                    });
                } else {
                    // 이미 존재하는 바인 경우 파티 수 증가
                    const existingBar = bars.get(barKey);
                    existingBar.partyCount++;
                    existingBar.parties.push(party.id);
                }
            }
        });
        
        allBars = Array.from(bars.values());
        console.log('추출된 바 정보:', allBars);
        
    } catch (error) {
        console.error('바 정보 추출 실패:', error);
        allBars = [];
    }
}

// 구글 지도 초기화
function initializeGoogleMap() {
    console.log('구글 지도 초기화 중...');
    
    const mapElement = document.getElementById('google-map');
    if (!mapElement) {
        console.error('지도 요소를 찾을 수 없습니다.');
        return;
    }
    
    try {
        // 한국 중심 좌표
        const koreaCenter = { lat: 36.5, lng: 127.5 };
        
        googleMap = new google.maps.Map(mapElement, {
            zoom: 7,
            center: koreaCenter,
            mapTypeId: google.maps.MapTypeId.ROADMAP,
            styles: [
                {
                    featureType: 'poi.business',
                    stylers: [{ visibility: 'on' }]
                }
            ]
        });
        
        // 바 마커 추가
        addBarMarkersToMap();
        
    } catch (error) {
        console.error('구글 지도 초기화 실패:', error);
        showMapError();
    }
}

// 지도 오류 표시
function showMapError() {
    const mapElement = document.getElementById('google-map');
    if (mapElement) {
        mapElement.innerHTML = `
            <div class="map-error">
                <div class="map-error-icon">🗺️</div>
                <h3>지도 로딩 중...</h3>
                <p>구글 지도 API 설정을 확인하고 있습니다.</p>
                <div class="map-error-details">
                    <p><strong>개발자용 정보:</strong></p>
                    <p>• API 키가 올바르게 설정되었는지 확인</p>
                    <p>• Google Cloud Console에서 도메인 허용 설정</p>
                    <p>• Maps JavaScript API가 활성화되었는지 확인</p>
                </div>
                <button onclick="retryMapLoad()" class="retry-btn">다시 시도</button>
            </div>
        `;
    }
}

// 지도 다시 로드
function retryMapLoad() {
    console.log('지도 다시 로드 시도...');
    if (googleMap) {
        google.maps.event.trigger(googleMap, 'resize');
    } else {
        initializeGoogleMap();
    }
}

// 지도에 바 마커 추가
function addBarMarkersToMap() {
    console.log('바 마커 추가 중...');
    
    // 기존 마커 제거
    mapMarkers.forEach(marker => marker.setMap(null));
    mapMarkers = [];
    
    allBars.forEach(bar => {
        // 주소를 좌표로 변환
        const geocoder = new google.maps.Geocoder();
        geocoder.geocode({ address: bar.address }, (results, status) => {
            if (status === 'OK') {
                const position = results[0].geometry.location;
                
                // 마커 생성
                const marker = new google.maps.Marker({
                    position: position,
                    map: googleMap,
                    title: bar.name,
                    icon: {
                        url: 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(`
                            <svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
                                <circle cx="16" cy="16" r="14" fill="#ff6b6b" stroke="#fff" stroke-width="2"/>
                                <text x="16" y="20" text-anchor="middle" fill="white" font-size="12" font-weight="bold">🎵</text>
                            </svg>
                        `),
                        scaledSize: new google.maps.Size(32, 32)
                    }
                });
                
                // 마커에 barId 저장 (강조 표시용)
                marker.barId = bar.id;
                
                // 정보창 생성
                const infoWindow = new google.maps.InfoWindow({
                    content: `
                        <div style="padding: 10px; max-width: 200px;">
                            <h3 style="margin: 0 0 5px 0; color: #e74c3c;">${bar.name}</h3>
                            <p style="margin: 5px 0; font-size: 12px;">📍 ${bar.address}</p>
                            <p style="margin: 5px 0; font-size: 12px;">🏢 ${bar.location || '상세 위치 미정'}</p>
                            <p style="margin: 5px 0; font-size: 12px;">📅 파티 ${bar.partyCount}개</p>
                            <button onclick="showBarDetail('${bar.id}')" style="background: #ff6b6b; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer; font-size: 11px;">상세보기</button>
                        </div>
                    `
                });
                
                // 마커에 정보창 저장
                marker.infoWindow = infoWindow;
                
                // 마커 클릭 이벤트
                marker.addListener('click', () => {
                    // 마커 클릭 시에도 지도 확대
                    focusMapOnBar(bar);
                    infoWindow.open(googleMap, marker);
                });
                
                mapMarkers.push(marker);
            }
        });
    });
}

// 바 목록 표시
function displayBarsList() {
    console.log('바 목록 표시 중...');
    
    const barsListElement = document.getElementById('bars-list');
    if (!barsListElement) {
        console.error('바 목록 요소를 찾을 수 없습니다.');
        return;
    }
    
    barsListElement.innerHTML = '';
    
    if (allBars.length === 0) {
        barsListElement.innerHTML = '<p style="text-align: center; color: #666;">등록된 라틴 바가 없습니다.</p>';
        return;
    }
    
    allBars.forEach(bar => {
        const barElement = document.createElement('div');
        barElement.className = 'bar-item';
        
        // 바 클릭 시 지도 확대 + 상세 정보 표시
        barElement.onclick = () => {
            focusMapOnBar(bar);
            showBarDetail(bar.id);
        };
        
        barElement.innerHTML = `
            <h4>${bar.name}</h4>
            <p>📍 ${bar.address}</p>
            <p>🏢 ${bar.location || '상세 위치 미정'}</p>
            <p>📅 파티 ${bar.partyCount}개</p>
            <span class="bar-region">${bar.region}</span>
        `;
        
        barsListElement.appendChild(barElement);
    });
}

// 바 상세 정보 표시
function showBarDetail(barId) {
    console.log('바 상세 정보 표시:', barId);
    
    const bar = allBars.find(b => b.id === barId);
    if (!bar) {
        console.error('바를 찾을 수 없습니다:', barId);
        return;
    }
    
    try {
        // 모달 제목 설정
        const barNameElement = document.getElementById('modal-bar-name');
        if (barNameElement) {
            barNameElement.textContent = bar.name;
        } else {
            console.error('modal-bar-name 요소를 찾을 수 없습니다.');
            return;
        }
        
        // 모달 내용 설정
        const modalInfo = document.getElementById('modal-bar-info');
        if (modalInfo) {
            modalInfo.innerHTML = `
                <div class="bar-detail-info">
                    <p><strong>📍 주소:</strong> ${bar.address || '정보 없음'}</p>
                    <p><strong>🏢 상세 위치:</strong> ${bar.location || '상세 위치 미정'}</p>
                    <p><strong>🌍 지역:</strong> ${bar.region || '정보 없음'}</p>
                    <p><strong>📅 등록된 파티:</strong> ${bar.partyCount || 0}개</p>
                    ${bar.contact ? `<p><strong>📞 연락처:</strong> ${bar.contact}</p>` : ''}
                    <p><strong>📅 등록일:</strong> ${bar.createdAt ? new Date(bar.createdAt).toLocaleDateString() : '정보 없음'}</p>
                </div>
            `;
        } else {
            console.error('modal-bar-info 요소를 찾을 수 없습니다.');
            return;
        }
        
        // 현재 바 정보를 전역 변수에 저장 (길찾기용)
        window.currentBarInfo = bar;
        
        // 모달 표시
        const modal = document.getElementById('bar-detail-modal');
        if (modal) {
            modal.classList.remove('hidden');
        } else {
            console.error('bar-detail-modal 요소를 찾을 수 없습니다.');
            return;
        }
        
        console.log('바 상세 정보 표시 완료:', bar.name);
        
    } catch (error) {
        console.error('바 상세 정보 표시 중 오류:', error);
    }
}

// 바 상세 모달 닫기
function closeBarDetailModal() {
    document.getElementById('bar-detail-modal').classList.add('hidden');
    window.currentBarInfo = null;
}

// 바 위치로 지도 확대
function focusMapOnBar(bar) {
    console.log('지도를 바 위치로 확대:', bar.name);
    
    if (!googleMap) {
        console.error('구글 지도가 초기화되지 않았습니다.');
        return;
    }
    
    // 주소를 좌표로 변환
    const geocoder = new google.maps.Geocoder();
    geocoder.geocode({ address: bar.address }, (results, status) => {
        if (status === 'OK' && results[0]) {
            const position = results[0].geometry.location;
            
            // 지도 중심을 바 위치로 이동하고 확대
            googleMap.setCenter(position);
            googleMap.setZoom(16); // 상세 확대
            
            // 해당 바의 마커를 강조 표시
            highlightBarMarker(bar.id);
            
            // 부드러운 애니메이션을 위한 패닝
            googleMap.panTo(position);
            
            console.log('지도 확대 완료:', bar.name);
        } else {
            console.error('주소를 좌표로 변환할 수 없습니다:', bar.address);
            // 실패 시 기본 확대
            googleMap.setZoom(12);
        }
    });
}

// 바 마커 강조 표시
function highlightBarMarker(barId) {
    // 모든 마커의 기본 스타일로 복원
    if (window.mapMarkers) {
        window.mapMarkers.forEach(marker => {
            marker.setIcon({
                url: 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(`
                    <svg width="30" height="30" viewBox="0 0 30 30" xmlns="http://www.w3.org/2000/svg">
                        <circle cx="15" cy="15" r="12" fill="#ff6b6b" stroke="white" stroke-width="2"/>
                        <text x="15" y="20" text-anchor="middle" fill="white" font-size="12" font-weight="bold">🎵</text>
                    </svg>
                `),
                scaledSize: new google.maps.Size(30, 30)
            });
        });
    }
    
    // 선택된 바의 마커를 강조
    const selectedMarker = window.mapMarkers?.find(marker => marker.barId === barId);
    if (selectedMarker) {
        selectedMarker.setIcon({
            url: 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(`
                <svg width="40" height="40" viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="20" cy="20" r="16" fill="#ff6b6b" stroke="#ff4757" stroke-width="3"/>
                    <circle cx="20" cy="20" r="8" fill="#ff4757"/>
                    <text x="20" y="26" text-anchor="middle" fill="white" font-size="14" font-weight="bold">🎵</text>
                </svg>
            `),
            scaledSize: new google.maps.Size(40, 40)
        });
        
        // 강조된 마커에 정보창 표시
        if (selectedMarker.infoWindow) {
            selectedMarker.infoWindow.open(googleMap, selectedMarker);
        }
    }
}

// 길찾기 열기
function openBarInMaps() {
    if (!window.currentBarInfo) return;
    
    const bar = window.currentBarInfo;
    const address = encodeURIComponent(bar.address);
    const url = `https://www.google.com/maps/search/?api=1&query=${address}`;
    
    window.open(url, '_blank');
}

// 바 정보 공유
function shareBarInfo() {
    if (!window.currentBarInfo) return;
    
    const bar = window.currentBarInfo;
    const shareText = `🎵 라틴댄스 바 정보\n\n🏢 ${bar.name}\n📍 ${bar.address}\n🌍 ${bar.region}\n\n라틴댄스 파티 커뮤니티에서 확인하세요!`;
    
    if (navigator.share) {
        navigator.share({
            title: `${bar.name} - 라틴댄스 바`,
            text: shareText,
            url: window.location.href
        });
    } else {
        // 클립보드에 복사
        navigator.clipboard.writeText(shareText).then(() => {
            showToast('바 정보가 클립보드에 복사되었습니다!', 'success');
        });
    }
}

// 지도에서 바 필터링
function filterBarsOnMap() {
    const regionFilter = document.getElementById('map-region-filter').value;
    const searchFilter = document.getElementById('map-search').value.toLowerCase();
    
    console.log('바 필터링:', { regionFilter, searchFilter });
    
    // 필터링된 바 목록 생성
    const filteredBars = allBars.filter(bar => {
        const matchesRegion = !regionFilter || bar.region === regionFilter;
        const matchesSearch = !searchFilter || 
            bar.name.toLowerCase().includes(searchFilter) ||
            bar.address.toLowerCase().includes(searchFilter);
        
        return matchesRegion && matchesSearch;
    });
    
    // 지도 마커 업데이트
    updateMapMarkers(filteredBars);
    
    // 사이드바 목록 업데이트
    updateBarsList(filteredBars);
}

// 검색 기능
function searchBarsOnMap() {
    filterBarsOnMap(); // 필터링 함수 재사용
}

// 지도 마커 업데이트
function updateMapMarkers(bars) {
    // 기존 마커 숨기기
    mapMarkers.forEach(marker => marker.setMap(null));
    
    // 필터링된 바들만 마커 표시
    bars.forEach(bar => {
        const marker = mapMarkers.find(m => m.title === bar.name);
        if (marker) {
            marker.setMap(googleMap);
        }
    });
}

// 바 목록 업데이트
function updateBarsList(bars) {
    const barsListElement = document.getElementById('bars-list');
    if (!barsListElement) return;
    
    barsListElement.innerHTML = '';
    
    if (bars.length === 0) {
        barsListElement.innerHTML = '<p style="text-align: center; color: #666;">검색 결과가 없습니다.</p>';
        return;
    }
    
    bars.forEach(bar => {
        const barElement = document.createElement('div');
        barElement.className = 'bar-item';
        barElement.onclick = () => showBarDetail(bar.id);
        
        barElement.innerHTML = `
            <h4>${bar.name}</h4>
            <p>📍 ${bar.address}</p>
            <p>🏢 ${bar.location || '상세 위치 미정'}</p>
            <p>📅 파티 ${bar.partyCount}개</p>
            <span class="bar-region">${bar.region}</span>
        `;
        
        barsListElement.appendChild(barElement);
    });
}

// 페이지 로드 시 라틴 바 지도 초기화 (IntersectionObserver 사용)
document.addEventListener('DOMContentLoaded', () => {
    // 지도 섹션이 화면에 보일 때만 초기화
    const mapSection = document.getElementById('latin-bars-map');
    if (mapSection) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting && !mapInitialized) {
                    mapInitialized = true;
                    initializeLatinBarsMap();
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1 });
        
        observer.observe(mapSection);
    }
});

// 지도 초기화 상태 변수
let mapInitialized = false;
let fullscreenMap = null;
let fullscreenMapMarkers = [];

// 지도/목록 토글 기능
function toggleMapView() {
    const mapContainer = document.querySelector('.map-container');
    const toggleBtn = document.getElementById('toggle-view-btn');
    const toggleIcon = toggleBtn.querySelector('.toggle-icon');
    const toggleText = toggleBtn.querySelector('.toggle-text');
    
    if (mapContainer.classList.contains('list-only')) {
        // 지도 보기로 전환
        mapContainer.classList.remove('list-only');
        toggleIcon.textContent = '🗺️';
        toggleText.textContent = '지도 보기';
    } else {
        // 목록만 보기로 전환
        mapContainer.classList.add('list-only');
        toggleIcon.textContent = '📋';
        toggleText.textContent = '목록 보기';
    }
}

// 전체화면 지도 열기
function openFullscreenMap() {
    const modal = document.getElementById('fullscreen-map-modal');
    if (modal) {
        modal.classList.remove('hidden');
        initializeFullscreenMap();
    }
}

// 전체화면 지도 닫기
function closeFullscreenMap() {
    const modal = document.getElementById('fullscreen-map-modal');
    if (modal) {
        modal.classList.add('hidden');
        // 전체화면 지도 정리
        if (fullscreenMap) {
            fullscreenMap = null;
        }
        fullscreenMapMarkers.forEach(marker => marker.setMap(null));
        fullscreenMapMarkers = [];
    }
}

// 전체화면 지도 초기화
function initializeFullscreenMap() {
    const mapElement = document.getElementById('fullscreen-google-map');
    if (!mapElement) return;
    
    try {
        const koreaCenter = { lat: 36.5, lng: 127.5 };
        
        fullscreenMap = new google.maps.Map(mapElement, {
            zoom: 7,
            center: koreaCenter,
            mapTypeId: google.maps.MapTypeId.ROADMAP,
            styles: [
                {
                    featureType: 'poi.business',
                    stylers: [{ visibility: 'on' }]
                }
            ]
        });
        
        // 전체화면 지도에 바 마커 추가
        addBarsToFullscreenMap();
        
        // 전체화면 바 목록 표시
        displayFullscreenBarsList();
        
    } catch (error) {
        console.error('전체화면 지도 초기화 실패:', error);
    }
}

// 전체화면 지도에 바 마커 추가
function addBarsToFullscreenMap() {
    if (!fullscreenMap || !allBars.length) return;
    
    fullscreenMapMarkers.forEach(marker => marker.setMap(null));
    fullscreenMapMarkers = [];
    
    allBars.forEach(bar => {
        // 주소를 좌표로 변환
        const geocoder = new google.maps.Geocoder();
        geocoder.geocode({ address: bar.address }, (results, status) => {
            if (status === 'OK' && results[0]) {
                const position = results[0].geometry.location;
                
                const marker = new google.maps.Marker({
                    position: position,
                    map: fullscreenMap,
                    title: bar.name,
                    icon: {
                        url: 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(`
                            <svg width="30" height="30" viewBox="0 0 30 30" xmlns="http://www.w3.org/2000/svg">
                                <circle cx="15" cy="15" r="12" fill="#ff6b6b" stroke="white" stroke-width="2"/>
                                <text x="15" y="20" text-anchor="middle" fill="white" font-size="12" font-weight="bold">🎵</text>
                            </svg>
                        `),
                        scaledSize: new google.maps.Size(30, 30)
                    }
                });
                
                // 마커에 barId 저장 (강조 표시용)
                marker.barId = bar.id;
                
                const infoWindow = new google.maps.InfoWindow({
                    content: `
                        <div style="padding: 10px; max-width: 200px;">
                            <h4 style="margin: 0 0 5px 0; color: #e74c3c;">${bar.name}</h4>
                            <p style="margin: 5px 0; font-size: 12px;">${bar.address}</p>
                            <p style="margin: 5px 0; font-size: 12px;">파티 ${bar.partyCount}개</p>
                            <button onclick="showFullscreenBarDetail('${bar.id}')" style="background: #ff6b6b; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer; font-size: 11px;">상세보기</button>
                        </div>
                    `
                });
                
                // 마커에 정보창 저장
                marker.infoWindow = infoWindow;
                
                marker.addListener('click', () => {
                    // 마커 클릭 시에도 전체화면 지도 확대
                    focusFullscreenMapOnBar(bar);
                    infoWindow.open(fullscreenMap, marker);
                });
                
                fullscreenMapMarkers.push(marker);
            }
        });
    });
}

// 전체화면 바 목록 표시
function displayFullscreenBarsList() {
    const barsListElement = document.getElementById('fullscreen-bars-list');
    if (!barsListElement) return;
    
    barsListElement.innerHTML = '';
    
    if (allBars.length === 0) {
        barsListElement.innerHTML = '<p style="text-align: center; color: #666;">등록된 바가 없습니다.</p>';
        return;
    }
    
    allBars.forEach(bar => {
        const barElement = document.createElement('div');
        barElement.className = 'bar-item';
        
        // 바 클릭 시 전체화면 지도 확대 + 상세 정보 표시
        barElement.onclick = () => {
            focusFullscreenMapOnBar(bar);
            showFullscreenBarDetail(bar.id);
        };
        
        barElement.innerHTML = `
            <h4>${bar.name}</h4>
            <p>📍 ${bar.address}</p>
            <p>🏢 ${bar.location || '상세 위치 미정'}</p>
            <p>🌍 ${bar.region}</p>
            <p>🎉 파티 ${bar.partyCount}개</p>
            <span class="bar-region">${bar.region}</span>
        `;
        
        barsListElement.appendChild(barElement);
    });
}

// 전체화면 바 상세 정보 표시
function showFullscreenBarDetail(barId) {
    const bar = allBars.find(b => b.id === barId);
    if (!bar) return;
    
    // 기존 모달을 재사용하되 전체화면에서 표시
    const modal = document.getElementById('bar-detail-modal');
    const barNameElement = document.getElementById('modal-bar-name');
    const barInfoElement = document.getElementById('modal-bar-info');
    
    if (modal && barNameElement && barInfoElement) {
        barNameElement.textContent = bar.name;
        barInfoElement.innerHTML = `
            <div class="bar-detail-info">
                <p><strong>📍 주소:</strong> ${bar.address || '정보 없음'}</p>
                <p><strong>🏢 상세 위치:</strong> ${bar.location || '상세 위치 미정'}</p>
                <p><strong>🌍 지역:</strong> ${bar.region || '정보 없음'}</p>
                <p><strong>📅 등록된 파티:</strong> ${bar.partyCount || 0}개</p>
                ${bar.contact ? `<p><strong>📞 연락처:</strong> ${bar.contact}</p>` : ''}
                <p><strong>📅 등록일:</strong> ${bar.createdAt ? new Date(bar.createdAt).toLocaleDateString() : '정보 없음'}</p>
            </div>
        `;
        
        window.currentBarInfo = bar;
        modal.classList.remove('hidden');
    }
}

// 전체화면 지도 필터링
function filterBarsOnFullscreenMap() {
    const regionFilter = document.getElementById('fullscreen-map-region-filter').value;
    const searchFilter = document.getElementById('fullscreen-map-search').value.toLowerCase();
    
    const filteredBars = allBars.filter(bar => {
        const matchesRegion = !regionFilter || bar.region === regionFilter;
        const matchesSearch = !searchFilter || 
            bar.name.toLowerCase().includes(searchFilter) ||
            bar.address.toLowerCase().includes(searchFilter);
        
        return matchesRegion && matchesSearch;
    });
    
    // 전체화면 지도 마커 업데이트
    updateFullscreenMapMarkers(filteredBars);
    
    // 전체화면 바 목록 업데이트
    updateFullscreenBarsList(filteredBars);
}

// 전체화면 지도 검색
function searchBarsOnFullscreenMap() {
    filterBarsOnFullscreenMap();
}

// 전체화면 지도 마커 업데이트
function updateFullscreenMapMarkers(bars) {
    if (!fullscreenMap) return;
    
    fullscreenMapMarkers.forEach(marker => marker.setMap(null));
    fullscreenMapMarkers = [];
    
    bars.forEach(bar => {
        const geocoder = new google.maps.Geocoder();
        geocoder.geocode({ address: bar.address }, (results, status) => {
            if (status === 'OK' && results[0]) {
                const position = results[0].geometry.location;
                
                const marker = new google.maps.Marker({
                    position: position,
                    map: fullscreenMap,
                    title: bar.name,
                    icon: {
                        url: 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(`
                            <svg width="30" height="30" viewBox="0 0 30 30" xmlns="http://www.w3.org/2000/svg">
                                <circle cx="15" cy="15" r="12" fill="#ff6b6b" stroke="white" stroke-width="2"/>
                                <text x="15" y="20" text-anchor="middle" fill="white" font-size="12" font-weight="bold">🎵</text>
                            </svg>
                        `),
                        scaledSize: new google.maps.Size(30, 30)
                    }
                });
                
                fullscreenMapMarkers.push(marker);
            }
        });
    });
}

// 전체화면 바 목록 업데이트
function updateFullscreenBarsList(bars) {
    const barsListElement = document.getElementById('fullscreen-bars-list');
    if (!barsListElement) return;
    
    barsListElement.innerHTML = '';
    
    if (bars.length === 0) {
        barsListElement.innerHTML = '<p style="text-align: center; color: #666;">검색 결과가 없습니다.</p>';
        return;
    }
    
    bars.forEach(bar => {
        const barElement = document.createElement('div');
        barElement.className = 'bar-item';
        
        // 바 클릭 시 전체화면 지도 확대 + 상세 정보 표시
        barElement.onclick = () => {
            focusFullscreenMapOnBar(bar);
            showFullscreenBarDetail(bar.id);
        };
        
        barElement.innerHTML = `
            <h4>${bar.name}</h4>
            <p>📍 ${bar.address}</p>
            <p>🏢 ${bar.location || '상세 위치 미정'}</p>
            <p>🌍 ${bar.region}</p>
            <p>🎉 파티 ${bar.partyCount}개</p>
            <span class="bar-region">${bar.region}</span>
        `;
        
        barsListElement.appendChild(barElement);
    });
}

// 전체화면 지도에서 바 위치로 확대
function focusFullscreenMapOnBar(bar) {
    console.log('전체화면 지도를 바 위치로 확대:', bar.name);
    
    if (!fullscreenMap) {
        console.error('전체화면 지도가 초기화되지 않았습니다.');
        return;
    }
    
    // 주소를 좌표로 변환
    const geocoder = new google.maps.Geocoder();
    geocoder.geocode({ address: bar.address }, (results, status) => {
        if (status === 'OK' && results[0]) {
            const position = results[0].geometry.location;
            
            // 지도 중심을 바 위치로 이동하고 확대
            fullscreenMap.setCenter(position);
            fullscreenMap.setZoom(16); // 상세 확대
            
            // 해당 바의 마커를 강조 표시
            highlightFullscreenBarMarker(bar.id);
            
            // 부드러운 애니메이션을 위한 패닝
            fullscreenMap.panTo(position);
            
            console.log('전체화면 지도 확대 완료:', bar.name);
        } else {
            console.error('주소를 좌표로 변환할 수 없습니다:', bar.address);
            // 실패 시 기본 확대
            fullscreenMap.setZoom(12);
        }
    });
}

// 전체화면 바 마커 강조 표시
function highlightFullscreenBarMarker(barId) {
    // 모든 마커의 기본 스타일로 복원
    fullscreenMapMarkers.forEach(marker => {
        marker.setIcon({
            url: 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(`
                <svg width="30" height="30" viewBox="0 0 30 30" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="15" cy="15" r="12" fill="#ff6b6b" stroke="white" stroke-width="2"/>
                    <text x="15" y="20" text-anchor="middle" fill="white" font-size="12" font-weight="bold">🎵</text>
                </svg>
            `),
            scaledSize: new google.maps.Size(30, 30)
        });
    });
    
    // 선택된 바의 마커를 강조
    const selectedMarker = fullscreenMapMarkers.find(marker => marker.barId === barId);
    if (selectedMarker) {
        selectedMarker.setIcon({
            url: 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(`
                <svg width="40" height="40" viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="20" cy="20" r="16" fill="#ff6b6b" stroke="#ff4757" stroke-width="3"/>
                    <circle cx="20" cy="20" r="8" fill="#ff4757"/>
                    <text x="20" y="26" text-anchor="middle" fill="white" font-size="14" font-weight="bold">🎵</text>
                </svg>
            `),
            scaledSize: new google.maps.Size(40, 40)
        });
        
        // 강조된 마커에 정보창 표시
        if (selectedMarker.infoWindow) {
            selectedMarker.infoWindow.open(fullscreenMap, selectedMarker);
        }
    }
} 