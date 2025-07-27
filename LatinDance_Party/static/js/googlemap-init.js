// 구글맵 지도 및 장소 검색 초기화 스크립트
// (테크)손진호 - 라틴댄스 파티 프로젝트

let map, marker, geocoder, infowindow, autocomplete;

function initMap() {
    // 기본 위치(서울 시청)로 지도 초기화
    const defaultLatLng = { lat: 37.5665, lng: 126.9780 };
    map = new google.maps.Map(document.getElementById('map'), {
        center: defaultLatLng,
        zoom: 13
    });
    geocoder = new google.maps.Geocoder();
    infowindow = new google.maps.InfoWindow();

    // 마커 초기화
    marker = new google.maps.Marker({
        map: map,
        position: defaultLatLng,
        draggable: true // 마커를 드래그해서 위치 조정 가능
    });

    // 장소 검색 자동완성
    const input = document.getElementById('map-search');
    autocomplete = new google.maps.places.Autocomplete(input);
    autocomplete.bindTo('bounds', map);

    // 장소 검색 결과 선택 시
    autocomplete.addListener('place_changed', function() {
        infowindow.close();
        const place = autocomplete.getPlace();
        if (!place.geometry) {
            alert('검색 결과에 위치 정보가 없습니다.');
            return;
        }
        // 지도와 마커 이동
        map.setCenter(place.geometry.location);
        map.setZoom(16);
        marker.setPosition(place.geometry.location);
        marker.setVisible(true);
        // 주소 입력란에 주소 자동 입력
        document.getElementById('party-location').value = place.formatted_address || place.name;
    });

    // 지도 클릭 시 마커 이동 및 주소 입력
    map.addListener('click', function(event) {
        marker.setPosition(event.latLng);
        map.panTo(event.latLng);
        // 좌표로 주소 변환
        geocoder.geocode({ location: event.latLng }, function(results, status) {
            if (status === 'OK' && results[0]) {
                document.getElementById('party-location').value = results[0].formatted_address;
                infowindow.setContent(results[0].formatted_address);
                infowindow.open(map, marker);
            } else {
                document.getElementById('party-location').value = '';
            }
        });
    });

    // 마커 드래그 종료 시 주소 입력
    marker.addListener('dragend', function(event) {
        geocoder.geocode({ location: event.latLng }, function(results, status) {
            if (status === 'OK' && results[0]) {
                document.getElementById('party-location').value = results[0].formatted_address;
                infowindow.setContent(results[0].formatted_address);
                infowindow.open(map, marker);
            } else {
                document.getElementById('party-location').value = '';
            }
        });
    });
}

// 페이지 로드 시 지도 초기화
window.addEventListener('DOMContentLoaded', function() {
    // 지도 div가 있을 때만 실행
    if (document.getElementById('map')) {
        // 구글맵 API가 로드된 후 initMap 실행
        if (window.google && window.google.maps) {
            initMap();
        } else {
            // 혹시 API가 늦게 로드될 경우 대비
            setTimeout(() => {
                if (window.google && window.google.maps) initMap();
            }, 1000);
        }
    }
}); 