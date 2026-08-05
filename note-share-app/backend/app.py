# 학습 노트 공유 앱 - Flask API + 정적 파일 서빙
# WHY: Firebase/Railway 없이 로컬 SQLite+파일로 업로드/검색/삭제/AI 기능을 제공

import os
import secrets
import uuid
from functools import wraps

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_file, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

import db as note_db

# backend/.env 로드
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, '..'))
FRONTEND_DIR = os.path.join(ROOT_DIR, 'frontend')
load_dotenv(os.path.join(BASE_DIR, '.env'))

GEMINI_API_KEY = (os.getenv('GEMINI_API_KEY') or '').strip()
DEFAULT_ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin1234')

ALLOWED_EXTENSIONS = {'pdf', 'mp3', 'png', 'jpg', 'jpeg', 'gif'}
admin_tokens: set[str] = set()

# Gemini는 키가 있을 때만 초기화
genai = None
if GEMINI_API_KEY:
    try:
        import google.generativeai as genai_module

        genai_module.configure(api_key=GEMINI_API_KEY)
        genai = genai_module
        print('Gemini API 활성화')
    except Exception as exc:
        print('Gemini 초기화 실패:', exc)
        genai = None
else:
    print('GEMINI_API_KEY 없음 → AI 기능은 안내 메시지로 응답')

app = Flask(__name__, static_folder=None)
CORS(app)

# DB 초기화 (관리자 해시 포함)
note_db.init_db(DEFAULT_ADMIN_PASSWORD)


def allowed_file(filename: str) -> bool:
    """허용 확장자인지 확인"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def admin_required(func):
    """Bearer 토큰으로 관리자 인증"""

    @wraps(func)
    def decorated(*args, **kwargs):
        auth = request.headers.get('Authorization', '')
        if not auth.startswith('Bearer '):
            return jsonify({'error': '인증 필요'}), 401
        token = auth.split(' ', 1)[1]
        if token not in admin_tokens:
            return jsonify({'error': '인증 실패'}), 403
        return func(*args, **kwargs)

    return decorated


def gemini_unavailable_message():
    """키가 없을 때 프론트에 보여줄 안내"""
    return (
        'Gemini API 키가 설정되지 않았습니다. '
        'backend/.env 에 GEMINI_API_KEY 를 넣은 뒤 서버를 다시 시작해 주세요.'
    )


def extract_pdf_text(file_path: str) -> str:
    """PDF에서 텍스트 추출"""
    import PyPDF2

    text_parts = []
    with open(file_path, 'rb') as pdf_file:
        reader = PyPDF2.PdfReader(pdf_file)
        for page in reader.pages:
            text_parts.append(page.extract_text() or '')
    return '\n'.join(text_parts).strip()


def pick_gemini_model() -> str | None:
    """사용 가능한 Gemini 모델명 선택"""
    if genai is None:
        return None
    preferred = [
        'gemini-2.0-flash',
        'gemini-1.5-flash',
        'gemini-1.5-pro',
        'gemini-pro',
    ]
    try:
        models = list(genai.list_models())
        available = {
            m.name.replace('models/', '')
            for m in models
            if 'generateContent' in getattr(m, 'supported_generation_methods', [])
        }
        for name in preferred:
            if name in available:
                return name
        return next(iter(available), None)
    except Exception:
        # 목록 조회 실패 시 기본 모델 시도
        return 'gemini-1.5-flash'


def call_gemini(prompt: str) -> str:
    """Gemini에 프롬프트 전송"""
    if genai is None:
        raise RuntimeError(gemini_unavailable_message())
    model_name = pick_gemini_model()
    if not model_name:
        raise RuntimeError('사용 가능한 Gemini 모델을 찾을 수 없습니다.')
    model = genai.GenerativeModel(model_name)
    response = model.generate_content(prompt)
    return (response.text or '').strip()


# ---------- 정적 / 헬스 ----------


@app.route('/')
def index():
    return send_from_directory(FRONTEND_DIR, 'index.html')


@app.route('/style.css')
def serve_css():
    return send_from_directory(FRONTEND_DIR, 'style.css')


@app.route('/main.js')
def serve_js():
    return send_from_directory(FRONTEND_DIR, 'main.js')


@app.route('/health')
def health():
    return jsonify({
        'status': 'ok',
        'gemini': bool(genai),
    })


# ---------- 노트 CRUD ----------


@app.route('/upload', methods=['POST'])
def upload_note():
    """노트 파일 업로드"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': '파일이 없습니다.'}), 400
        file = request.files['file']
        title = (request.form.get('title') or '').strip()
        tags = (request.form.get('tags') or '').strip()
        uploader = (request.form.get('uploader') or '').strip()
        delete_password = request.form.get('delete_password') or ''

        if not title:
            return jsonify({'error': '제목을 입력하세요.'}), 400
        if not tags:
            return jsonify({'error': '태그를 입력하세요.'}), 400
        if not delete_password:
            return jsonify({'error': '삭제 암호를 입력하세요.'}), 400
        if not file or not file.filename:
            return jsonify({'error': '파일을 선택하세요.'}), 400
        if not allowed_file(file.filename):
            return jsonify({'error': '허용되지 않는 파일 형식입니다. (pdf/mp3/이미지)'}), 400

        original_name = secure_filename(file.filename)
        if not original_name:
            return jsonify({'error': '파일 이름이 올바르지 않습니다.'}), 400

        ext = original_name.rsplit('.', 1)[1].lower()
        stored_name = f'{uuid.uuid4().hex}.{ext}'
        save_path = os.path.join(note_db.UPLOADS_DIR, stored_name)
        file.save(save_path)

        note = note_db.create_note(
            title=title,
            tags=tags,
            uploader=uploader,
            filename=original_name,
            stored_name=stored_name,
            delete_password=delete_password,
        )
        return jsonify({'message': '업로드 성공', 'note': note}), 201
    except Exception as exc:
        return jsonify({'error': f'업로드 오류: {exc}'}), 500


@app.route('/notes', methods=['GET'])
def list_notes():
    """태그 검색 또는 전체 목록"""
    try:
        tags = request.args.get('tags', '')
        notes = note_db.list_notes(tags)
        return jsonify({'notes': notes}), 200
    except Exception as exc:
        return jsonify({'error': f'목록 조회 오류: {exc}'}), 500


@app.route('/download/<note_id>', methods=['GET'])
def download_note(note_id):
    """첨부 파일 다운로드"""
    note = note_db.get_note(note_id)
    if not note:
        return jsonify({'error': '노트를 찾을 수 없습니다.'}), 404
    file_path = note_db.get_file_path(note_id)
    if not file_path:
        return jsonify({'error': '파일이 존재하지 않습니다.'}), 404
    return send_file(file_path, as_attachment=True, download_name=note['filename'])


@app.route('/files/<note_id>', methods=['GET'])
def view_file(note_id):
    """브라우저에서 바로 보기 (PDF 공부하기용)"""
    note = note_db.get_note(note_id)
    if not note:
        return jsonify({'error': '노트를 찾을 수 없습니다.'}), 404
    file_path = note_db.get_file_path(note_id)
    if not file_path:
        return jsonify({'error': '파일이 존재하지 않습니다.'}), 404
    return send_file(file_path, as_attachment=False, download_name=note['filename'])


@app.route('/delete/<note_id>', methods=['DELETE'])
def delete_note(note_id):
    """삭제 암호 기반 단건 삭제"""
    try:
        req_data = request.get_json(silent=True) or {}
        password = req_data.get('password', '')
        if not password:
            return jsonify({'error': '삭제 암호를 입력하세요.'}), 400
        ok, message = note_db.delete_note_by_password(note_id, password)
        if not ok:
            status = 404 if '찾을 수 없습니다' in message else 403
            return jsonify({'error': message}), status
        return jsonify({'message': message}), 200
    except Exception as exc:
        return jsonify({'error': f'삭제 중 오류 발생: {exc}'}), 500


# ---------- Gemini AI ----------


@app.route('/generate-question', methods=['POST'])
def generate_question():
    """PDF 내용 기반 퀴즈 질문 생성"""
    if genai is None:
        return jsonify({'error': gemini_unavailable_message()}), 503

    data = request.get_json(silent=True) or {}
    note_id = data.get('note_id')
    if not note_id:
        return jsonify({'error': 'note_id가 필요합니다.'}), 400

    note = note_db.get_note(note_id)
    if not note:
        return jsonify({'error': '노트를 찾을 수 없습니다.'}), 404
    if not note['filename'].lower().endswith('.pdf'):
        return jsonify({'error': '현재는 PDF 파일만 지원합니다.'}), 400

    file_path = note_db.get_file_path(note_id)
    if not file_path:
        return jsonify({'error': '파일이 존재하지 않습니다.'}), 404

    try:
        text = extract_pdf_text(file_path)
        if not text:
            return jsonify({'error': 'PDF에서 텍스트를 추출할 수 없습니다.'}), 400
        prompt = (
            '다음 학습 노트 내용을 바탕으로 5개의 퀴즈 문제(질문)와 정답을 만들어줘.\n\n'
            f'{text[:4000]}'
        )
        result = call_gemini(prompt)
        return jsonify({'questions': result}), 200
    except Exception as exc:
        return jsonify({'error': f'질문 생성 중 오류 발생: {exc}'}), 500


@app.route('/summarize-pdf', methods=['POST'])
def summarize_pdf():
    """PDF 상세 정리(요약)"""
    if genai is None:
        return jsonify({'error': gemini_unavailable_message()}), 503

    data = request.get_json(silent=True) or {}
    note_id = data.get('note_id')
    if not note_id:
        return jsonify({'error': 'note_id가 필요합니다.'}), 400

    note = note_db.get_note(note_id)
    if not note:
        return jsonify({'error': '노트를 찾을 수 없습니다.'}), 404
    if not note['filename'].lower().endswith('.pdf'):
        return jsonify({'error': '현재는 PDF 파일만 지원합니다.'}), 400

    file_path = note_db.get_file_path(note_id)
    if not file_path:
        return jsonify({'error': '파일이 존재하지 않습니다.'}), 404

    try:
        text = extract_pdf_text(file_path)
        if not text:
            return jsonify({'error': 'PDF에서 텍스트를 추출할 수 없습니다.'}), 400
        prompt = (
            '아래 학습 노트 PDF 텍스트를 한글로 상세히 정리해줘. '
            '핵심 개념, 중요 포인트, 복습 포인트를 구분해서 작성해.\n\n'
            f'{text[:6000]}'
        )
        summary = call_gemini(prompt)
        return jsonify({'summary': summary}), 200
    except Exception as exc:
        return jsonify({'error': f'요약 중 오류 발생: {exc}'}), 500


# ---------- 관리자 ----------


@app.route('/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json(silent=True) or {}
    password = data.get('password', '')
    if not password:
        return jsonify({'error': '비밀번호를 입력하세요.'}), 400
    if note_db.verify_admin_password(password):
        token = secrets.token_hex(24)
        admin_tokens.add(token)
        return jsonify({'token': token}), 200
    return jsonify({'error': '비밀번호가 틀렸습니다.'}), 403


@app.route('/admin/delete-all-notes', methods=['POST'])
@admin_required
def admin_delete_all_notes():
    try:
        count = note_db.delete_all_notes()
        return jsonify({'message': f'전체 노트 {count}개 삭제 완료'}), 200
    except Exception as exc:
        return jsonify({'error': f'전체 삭제 오류: {exc}'}), 500


@app.route('/admin/reset-db', methods=['POST'])
@admin_required
def admin_reset_db():
    try:
        note_db.reset_database(DEFAULT_ADMIN_PASSWORD)
        # 토큰 무효화 (비밀번호도 초기값으로 돌아감)
        admin_tokens.clear()
        return jsonify({'message': 'DB 초기화 완료'}), 200
    except Exception as exc:
        return jsonify({'error': f'DB 초기화 오류: {exc}'}), 500


@app.route('/admin/change-password', methods=['POST'])
@admin_required
def admin_change_password():
    data = request.get_json(silent=True) or {}
    new_password = data.get('new_password', '')
    if not new_password or len(new_password) < 4:
        return jsonify({'error': '비밀번호는 4자 이상이어야 합니다.'}), 400
    note_db.set_admin_password(new_password)
    return jsonify({'message': '비밀번호가 성공적으로 변경되었습니다.'}), 200


@app.route('/admin/delete-note/<note_id>', methods=['DELETE'])
@admin_required
def admin_delete_note(note_id):
    ok, message = note_db.delete_note_admin(note_id)
    if not ok:
        return jsonify({'error': message}), 404
    return jsonify({'message': message}), 200


if __name__ == '__main__':
    # 로컬 개발 서버
    app.run(host='0.0.0.0', port=5000, debug=True)
