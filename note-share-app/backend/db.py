# SQLite 초기화 및 노트 CRUD
# WHY: Firebase 없이 로컬에서 노트 메타데이터와 관리자 설정을 한곳에 보관하기 위함

import hashlib
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

# 프로젝트 루트 기준 data 폴더
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_DIR = os.path.join(ROOT_DIR, 'data')
UPLOADS_DIR = os.path.join(DATA_DIR, 'uploads')
DB_PATH = os.path.join(DATA_DIR, 'notes.db')


def hash_password(password: str) -> str:
    """비밀번호를 SHA-256 해시로 변환 (평문 저장 방지)"""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def _connect() -> sqlite3.Connection:
    """SQLite 연결 (행을 dict처럼 사용)"""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(default_admin_password: str = 'admin1234') -> None:
    """테이블 생성 + 관리자 비밀번호 초기값 설정"""
    conn = _connect()
    try:
        conn.executescript(
            '''
            CREATE TABLE IF NOT EXISTS notes (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                tags TEXT NOT NULL DEFAULT '',
                uploader TEXT NOT NULL DEFAULT '',
                filename TEXT NOT NULL,
                stored_name TEXT NOT NULL,
                delete_password_hash TEXT NOT NULL,
                uploaded_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            '''
        )
        row = conn.execute(
            "SELECT value FROM settings WHERE key = 'admin_password_hash'"
        ).fetchone()
        if row is None:
            conn.execute(
                "INSERT INTO settings (key, value) VALUES (?, ?)",
                ('admin_password_hash', hash_password(default_admin_password)),
            )
        conn.commit()
    finally:
        conn.close()


def _parse_tags(tags_raw: str) -> list[str]:
    """콤마 구분 태그 문자열 → 정리된 리스트"""
    if not tags_raw:
        return []
    return [t.strip() for t in tags_raw.split(',') if t.strip()]


def _note_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    """DB 행을 API 응답용 dict로 변환"""
    note_id = row['id']
    return {
        'id': note_id,
        'title': row['title'],
        'tags': _parse_tags(row['tags']),
        'uploader': row['uploader'] or '익명',
        'filename': row['filename'],
        'file_url': f'/files/{note_id}',
        'uploaded_at': row['uploaded_at'],
    }


def create_note(
    title: str,
    tags: str,
    uploader: str,
    filename: str,
    stored_name: str,
    delete_password: str,
) -> dict[str, Any]:
    """노트 메타데이터 저장 후 응답용 dict 반환"""
    note_id = uuid.uuid4().hex
    uploaded_at = datetime.now(timezone.utc).isoformat()
    conn = _connect()
    try:
        conn.execute(
            '''
            INSERT INTO notes
            (id, title, tags, uploader, filename, stored_name, delete_password_hash, uploaded_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                note_id,
                title,
                tags,
                uploader or '',
                filename,
                stored_name,
                hash_password(delete_password),
                uploaded_at,
            ),
        )
        conn.commit()
        row = conn.execute('SELECT * FROM notes WHERE id = ?', (note_id,)).fetchone()
        return _note_to_dict(row)
    finally:
        conn.close()


def list_notes(tags_query: str = '') -> list[dict[str, Any]]:
    """태그 검색(AND: 입력한 태그가 모두 포함) 또는 전체 목록"""
    conn = _connect()
    try:
        rows = conn.execute(
            'SELECT * FROM notes ORDER BY uploaded_at DESC'
        ).fetchall()
        notes = [_note_to_dict(r) for r in rows]
        query_tags = _parse_tags(tags_query)
        if not query_tags:
            return notes
        # 입력 태그가 모두 포함된 노트만 (대소문자 무시)
        filtered = []
        for note in notes:
            note_tags_lower = [t.lower() for t in note['tags']]
            if all(q.lower() in note_tags_lower for q in query_tags):
                filtered.append(note)
        return filtered
    finally:
        conn.close()


def get_note(note_id: str) -> Optional[dict[str, Any]]:
    """단건 조회 (내부용: stored_name, hash 포함)"""
    conn = _connect()
    try:
        row = conn.execute('SELECT * FROM notes WHERE id = ?', (note_id,)).fetchone()
        if row is None:
            return None
        data = _note_to_dict(row)
        data['stored_name'] = row['stored_name']
        data['delete_password_hash'] = row['delete_password_hash']
        return data
    finally:
        conn.close()


def get_file_path(note_id: str) -> Optional[str]:
    """노트의 실제 파일 경로 반환"""
    note = get_note(note_id)
    if not note:
        return None
    path = os.path.join(UPLOADS_DIR, note['stored_name'])
    if not os.path.isfile(path):
        return None
    return path


def delete_note_by_password(note_id: str, password: str) -> tuple[bool, str]:
    """삭제 암호 검증 후 노트+파일 삭제. (성공여부, 메시지)"""
    note = get_note(note_id)
    if not note:
        return False, '노트를 찾을 수 없습니다.'
    if hash_password(password) != note['delete_password_hash']:
        return False, '삭제 암호가 일치하지 않습니다.'
    _delete_note_files_and_row(note_id, note['stored_name'])
    return True, '노트가 성공적으로 삭제되었습니다.'


def delete_note_admin(note_id: str) -> tuple[bool, str]:
    """관리자용: 암호 없이 단건 삭제"""
    note = get_note(note_id)
    if not note:
        return False, '노트를 찾을 수 없습니다.'
    _delete_note_files_and_row(note_id, note['stored_name'])
    return True, '노트가 성공적으로 삭제되었습니다.'


def _delete_note_files_and_row(note_id: str, stored_name: str) -> None:
    """파일과 DB 행을 함께 제거"""
    file_path = os.path.join(UPLOADS_DIR, stored_name)
    if os.path.isfile(file_path):
        try:
            os.remove(file_path)
        except OSError:
            pass
    conn = _connect()
    try:
        conn.execute('DELETE FROM notes WHERE id = ?', (note_id,))
        conn.commit()
    finally:
        conn.close()


def delete_all_notes() -> int:
    """전체 노트와 업로드 파일 삭제. 삭제 개수 반환"""
    conn = _connect()
    try:
        rows = conn.execute('SELECT id, stored_name FROM notes').fetchall()
        count = 0
        for row in rows:
            file_path = os.path.join(UPLOADS_DIR, row['stored_name'])
            if os.path.isfile(file_path):
                try:
                    os.remove(file_path)
                except OSError:
                    pass
            conn.execute('DELETE FROM notes WHERE id = ?', (row['id'],))
            count += 1
        conn.commit()
        return count
    finally:
        conn.close()


def reset_database(default_admin_password: str = 'admin1234') -> None:
    """DB 파일과 업로드 폴더를 비운 뒤 스키마 재생성"""
    # 업로드 파일 전부 제거
    if os.path.isdir(UPLOADS_DIR):
        for name in os.listdir(UPLOADS_DIR):
            path = os.path.join(UPLOADS_DIR, name)
            if os.path.isfile(path) and name != '.gitkeep':
                try:
                    os.remove(path)
                except OSError:
                    pass
    # DB 삭제 후 재생성
    if os.path.isfile(DB_PATH):
        try:
            os.remove(DB_PATH)
        except OSError:
            pass
    init_db(default_admin_password)


def verify_admin_password(password: str) -> bool:
    """관리자 비밀번호 검증"""
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT value FROM settings WHERE key = 'admin_password_hash'"
        ).fetchone()
        if row is None:
            return False
        return row['value'] == hash_password(password)
    finally:
        conn.close()


def set_admin_password(new_password: str) -> None:
    """관리자 비밀번호 해시 갱신"""
    conn = _connect()
    try:
        conn.execute(
            '''
            INSERT INTO settings (key, value) VALUES ('admin_password_hash', ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            ''',
            (hash_password(new_password),),
        )
        conn.commit()
    finally:
        conn.close()
