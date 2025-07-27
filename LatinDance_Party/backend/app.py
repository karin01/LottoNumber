# 필요한 라이브러리 임포트
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore
import os
import csv
import requests

# static 폴더의 절대경로를 backend 상위로 지정 (index.html이 있는 루트 폴더)
static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
app = Flask(__name__, static_folder=static_dir, static_url_path="")
CORS(app)

# 서비스 계정 키 파일 경로 지정 (파일이 없으면 에러 발생)
SERVICE_ACCOUNT_PATH = os.path.join(
    os.path.dirname(__file__),
    "share-note-ef791-firebase-adminsdk-fbsvc-36ee9ed360.json"
)
if not os.path.exists(SERVICE_ACCOUNT_PATH):
    raise FileNotFoundError(f"서비스 계정 키 파일이 없습니다: {SERVICE_ACCOUNT_PATH}")

# Firebase Admin SDK 초기화
cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
firebase_admin.initialize_app(cred)

# Firestore 클라이언트 생성
db = firestore.client()

# 루트(/)로 접속하면 static 폴더의 index.html을 보여줌
@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

# 파티 ID가 포함된 URL에서 메타 태그를 동적으로 생성
@app.route('/party/<party_id>')
def serve_party_page(party_id):
    try:
        # Firebase에서 파티 정보 가져오기
        doc = db.collection('parties').document(party_id).get()
        if doc.exists:
            party = doc.to_dict()
            
            # HTML 템플릿 생성
            html_content = generate_party_html(party, party_id)
            return html_content
        else:
            # 파티가 없으면 기본 페이지로 리다이렉트
            return send_from_directory(app.static_folder, 'index.html')
    except Exception as e:
        print(f"파티 페이지 생성 오류: {e}")
        return send_from_directory(app.static_folder, 'index.html')

def generate_party_html(party, party_id):
    """파티 정보를 포함한 HTML 페이지 생성"""
    
    # 이미지 URL 설정 (카카오톡 권장 크기: 400x400px)
    image_url = 'https://via.placeholder.com/400x400/FF6B6B/FFFFFF?text=라틴댄스+파티&font-size=24'
    
    # 파티 정보에 따라 동적 기본 이미지 생성
    if not party.get('posterUrl') or party['posterUrl'] == '':
        party_title = party.get('title', '라틴댄스 파티').replace(' ', '+')
        location = party.get('location', '').replace(' ', '+')
        image_url = f"https://via.placeholder.com/400x400/FF6B6B/FFFFFF?text={party_title}+{location}&font-size=20"
    
    print(f"파티 이미지 정보: {party.get('posterUrl')}")
    
    if party.get('posterUrl'):
        image_url = party['posterUrl']
        print(f"원본 이미지 URL: {image_url}")
        
        # 상대 경로인 경우 절대 경로로 변환
        if not image_url.startswith('http'):
            # Firebase Storage URL인지 확인
            if 'firebasestorage.googleapis.com' in image_url:
                image_url = image_url
            else:
                image_url = f"http://localhost:5000{image_url}"
        
        print(f"변환된 이미지 URL: {image_url}")
    else:
        print("포스터 URL이 없어 기본 이미지 사용")
    
    # 갤러리 이미지가 있으면 첫 번째 이미지 사용
    if not party.get('posterUrl') and party.get('gallery') and len(party['gallery']) > 0:
        image_url = party['gallery'][0]
        print(f"갤러리 이미지 사용: {image_url}")
    
    # 설명 텍스트 생성 (장소 정보 포함)
    description = party.get('description', '라틴댄스 파티에 초대합니다!')
    
    # 장소 정보 조합
    location_info = ''
    if party.get('region') and party.get('location'):
        location_info = f"{party['region']} {party['location']}"
    elif party.get('region'):
        location_info = party['region']
    elif party.get('location'):
        location_info = party['location']
    
    if description and location_info:
        description += f" 📍 장소: {location_info}"
    elif location_info:
        description = f"{location_info}에서 열리는 라틴댄스 파티입니다!"
    
    # 날짜 정보 추가
    if party.get('date'):
        date = party['date']
        formatted_date = date
        
        # 이미 한국어 형식인지 확인
        if isinstance(date, str) and '년' in date:
            # 이미 한국어 형식이면 그대로 사용
            formatted_date = date
        else:
            # ISO 형식이면 파싱 시도
            try:
                from datetime import datetime
                if isinstance(date, str):
                    # ISO 형식 문자열을 파싱
                    date_obj = datetime.fromisoformat(date.replace('Z', '+00:00'))
                    formatted_date = date_obj.strftime('%Y년 %m월 %d일')
                else:
                    # 다른 형식이면 원본 그대로 사용
                    formatted_date = str(date)
            except Exception as e:
                print(f"날짜 파싱 오류: {e}")
                formatted_date = str(date)  # 원본 그대로 사용
        
        description += f" 📅 날짜: {formatted_date}"
    
    # 시간 정보 추가
    if party.get('time'):
        description += f" ⏰ 시간: {party['time'][:5]}"
    
    # 제목에 장소 정보 추가
    title = party.get('title', '라틴댄스 파티')
    if party.get('location'):
        title += f" - {party['location']}"
    
    # 현재 URL
    current_url = f"http://localhost:5000/?party={party_id}"
    
    html_template = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    
    <!-- Open Graph 메타 태그 (카카오톡 공유용) -->
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{description}">
    <meta property="og:image" content="{image_url}">
    <meta property="og:url" content="{current_url}">
    <meta property="og:type" content="website">
    <meta property="og:site_name" content="라틴댄스 파티 커뮤니티">
    
    <!-- Twitter Card 메타 태그 -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{title}">
    <meta name="twitter:description" content="{description}">
    <meta name="twitter:image" content="{image_url}">
    
    <link rel="stylesheet" href="static/css/style.css">
    <script src="https://developers.kakao.com/sdk/js/kakao.js"></script>
</head>
<body>
    <script>
        // 페이지 로드 시 파티 ID를 localStorage에 저장하고 메인 페이지로 리다이렉트
        localStorage.setItem('pendingPartyId', '{party_id}');
        window.location.href = '/';
    </script>
</body>
</html>
"""
    return html_template

# 1. 파티 등록
@app.route('/add_party', methods=['POST'])
def add_party():
    try:
        data = request.json
        
        # posterUrl 필드 검증 (Base64 데이터 방지)
        if 'posterUrl' in data and data['posterUrl']:
            poster_url = data['posterUrl']
            # Base64 데이터인지 확인
            if poster_url.startswith('data:image'):
                return jsonify({
                    "result": "error", 
                    "message": "이미지는 Firebase Storage에 업로드 후 URL만 저장해야 합니다. Base64 데이터는 저장할 수 없습니다."
                }), 400
            
            # URL 길이 체크 (1MB 제한)
            if len(poster_url.encode('utf-8')) > 1048487:
                return jsonify({
                    "result": "error", 
                    "message": "포스터 URL이 너무 깁니다. 이미지를 다시 업로드해주세요."
                }), 400
        
        doc_ref = db.collection('parties').add(data)
        return jsonify({"result": "success", "party_id": doc_ref[1].id}), 200
    except Exception as e:
        return jsonify({"result": "error", "message": str(e)}), 400

# 2. 파티 목록 조회 (필터: 지역, 날짜)
@app.route('/get_parties', methods=['GET'])
def get_parties():
    try:
        region = request.args.get('region')
        date = request.args.get('date')
        parties_ref = db.collection('parties')
        query = parties_ref
        if region:
            query = query.where('party-region', '==', region)
        if date:
            query = query.where('party-date', '==', date)
        docs = query.stream()
        parties = []
        for doc in docs:
            party = doc.to_dict()
            party['id'] = doc.id
            parties.append(party)
        return jsonify({"result": "success", "parties": parties}), 200
    except Exception as e:
        return jsonify({"result": "error", "message": str(e)}), 400

# 3. 파티 상세 조회
@app.route('/get_party/<party_id>', methods=['GET'])
def get_party(party_id):
    try:
        doc = db.collection('parties').document(party_id).get()
        if doc.exists:
            party = doc.to_dict()
            party['id'] = doc.id
            return jsonify({"result": "success", "party": party}), 200
        else:
            return jsonify({"result": "error", "message": "파티를 찾을 수 없습니다."}), 404
    except Exception as e:
        return jsonify({"result": "error", "message": str(e)}), 400

# 4. 파티 정보 수정
@app.route('/update_party/<party_id>', methods=['PUT'])
def update_party(party_id):
    try:
        data = request.json
        
        # posterUrl 필드 검증 (Base64 데이터 방지)
        if 'posterUrl' in data and data['posterUrl']:
            poster_url = data['posterUrl']
            # Base64 데이터인지 확인
            if poster_url.startswith('data:image'):
                return jsonify({
                    "result": "error", 
                    "message": "이미지는 Firebase Storage에 업로드 후 URL만 저장해야 합니다. Base64 데이터는 저장할 수 없습니다."
                }), 400
            
            # URL 길이 체크 (1MB 제한)
            if len(poster_url.encode('utf-8')) > 1048487:
                return jsonify({
                    "result": "error", 
                    "message": "포스터 URL이 너무 깁니다. 이미지를 다시 업로드해주세요."
                }), 400
        
        db.collection('parties').document(party_id).update(data)
        return jsonify({"result": "success"}), 200
    except Exception as e:
        return jsonify({"result": "error", "message": str(e)}), 400

# 5. 파티 삭제
@app.route('/delete_party/<party_id>', methods=['DELETE'])
def delete_party(party_id):
    try:
        db.collection('parties').document(party_id).delete()
        return jsonify({"result": "success"}), 200
    except Exception as e:
        return jsonify({"result": "error", "message": str(e)}), 400

# 6. 파티별 댓글 등록
@app.route('/add_comment/<party_id>', methods=['POST'])
def add_comment(party_id):
    try:
        data = request.json
        db.collection('parties').document(party_id).collection('comments').add(data)
        return jsonify({"result": "success"}), 200
    except Exception as e:
        return jsonify({"result": "error", "message": str(e)}), 400

# 7. 파티별 댓글 목록 조회
@app.route('/get_comments/<party_id>', methods=['GET'])
def get_comments(party_id):
    try:
        comments_ref = db.collection('parties').document(party_id).collection('comments')
        docs = comments_ref.stream()
        comments = []
        for doc in docs:
            comment = doc.to_dict()
            comment['id'] = doc.id
            comments.append(comment)
        return jsonify({"result": "success", "comments": comments}), 200
    except Exception as e:
        return jsonify({"result": "error", "message": str(e)}), 400

# 8. 파티별 댓글 삭제
@app.route('/delete_comment/<party_id>/<comment_id>', methods=['DELETE'])
def delete_comment(party_id, comment_id):
    try:
        db.collection('parties').document(party_id).collection('comments').document(comment_id).delete()
        return jsonify({"result": "success"}), 200
    except Exception as e:
        return jsonify({"result": "error", "message": str(e)}), 400

# 9. 새 빠 추가 (CSV 파일에 저장)
@app.route('/add-bar', methods=['POST'])
def add_bar():
    try:
        data = request.json
        if not data:
            return jsonify({"result": "error", "message": "데이터가 없습니다."}), 400
            
        region = data.get('region', '')
        name = data.get('name', '')
        address = data.get('address', '')
        extra = data.get('extra', '')
        
        if not all([region, name, address]):
            return jsonify({"result": "error", "message": "지역, 빠 이름, 주소는 필수입니다."}), 400
        
        # CSV 파일 경로
        csv_path = os.path.join(static_dir, 'Latin_Bar_LIST.csv')
        
        # CSV 파일에 새 빠 추가
        with open(csv_path, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([region, name, address, extra])
        
        return jsonify({"result": "success", "message": f"{name}이(가) 성공적으로 추가되었습니다."}), 200
        
    except Exception as e:
        return jsonify({"result": "error", "message": str(e)}), 400

# 10. (설명) 이미지 업로드는 프론트엔드에서 Firebase Storage로 직접 업로드하는 것이 일반적입니다.
#    서버에서 Storage로 업로드하려면 별도 코드가 필요하며, 보통은 프론트엔드에서 처리합니다.

# 구글 번역 API 키 (보안상 실제 서비스에서는 환경변수로 관리 권장)
GOOGLE_API_KEY = 'AIzaSyANAoSBtvO4yUBQi-ljSzK-d0IYSMSbACA'

# 번역 엔드포인트 추가
@app.route('/translate', methods=['POST'])
def translate_text():
    """구글 번역 API를 이용해 텍스트를 번역하는 엔드포인트"""
    data = request.json
    text = data.get('text')
    target = data.get('target', 'ko')
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    url = 'https://translation.googleapis.com/language/translate/v2'
    params = {
        'q': text,
        'target': target,
        'key': GOOGLE_API_KEY
    }
    response = requests.post(url, data=params)
    result = response.json()
    if 'data' in result and 'translations' in result['data']:
        translated = result['data']['translations'][0]['translatedText']
        return jsonify({'translated': translated})
    else:
        return jsonify({'error': 'Translation failed', 'detail': result}), 500

if __name__ == '__main__':
    app.run(debug=True) 