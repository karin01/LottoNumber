// 학습 노트 공유 앱 프론트엔드
// WHY: 같은 출처(Flask)에서 API를 호출해 CORS 없이 동작하게 함

const API_BASE = ''; // 같은 서버에서 서빙하므로 상대 경로 사용

document.addEventListener('DOMContentLoaded', () => {
    const uploadForm = document.getElementById('uploadForm');
    const uploadResult = document.getElementById('uploadResult');
    const searchBtn = document.getElementById('searchBtn');
    const searchTags = document.getElementById('searchTags');
    const notesList = document.getElementById('notesList');

    let adminToken = null;

    // 모달 표시/숨김 헬퍼
    function showModal(el) {
        if (!el) return;
        el.hidden = false;
    }

    function hideModal(el) {
        if (!el) return;
        el.hidden = true;
    }

    // ---------- 업로드 ----------
    uploadForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const formData = new FormData(uploadForm);
        uploadResult.textContent = '업로드 중...';
        try {
            const res = await fetch(`${API_BASE}/upload`, {
                method: 'POST',
                body: formData,
            });
            const data = await res.json();
            if (res.ok) {
                uploadResult.textContent = '업로드 성공!';
                uploadForm.reset();
                loadNotes();
            } else {
                uploadResult.textContent = data.error || '업로드 실패';
            }
        } catch (err) {
            uploadResult.textContent = '네트워크 오류';
        }
    });

    searchBtn.addEventListener('click', loadNotes);
    searchTags.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
            event.preventDefault();
            loadNotes();
        }
    });
    loadNotes();

    // ---------- 목록 ----------
    async function loadNotes() {
        const tags = searchTags.value.trim();
        let url = `${API_BASE}/notes`;
        if (tags) url += `?tags=${encodeURIComponent(tags)}`;
        notesList.innerHTML = '불러오는 중...';
        try {
            const res = await fetch(url);
            const data = await res.json();
            if (!res.ok) {
                notesList.innerHTML = `<p>${data.error || '목록 불러오기 실패'}</p>`;
                return;
            }
            if (!data.notes || data.notes.length === 0) {
                notesList.innerHTML = '<p>노트가 없습니다.</p>';
                return;
            }
            notesList.innerHTML = data.notes.map(renderNoteCard).join('');
            bindNoteActions();
        } catch (err) {
            notesList.innerHTML = '<p>네트워크 오류</p>';
        }
    }

    function escapeHtml(text) {
        // XSS 방지: 제목/태그 등 사용자 입력 이스케이프
        return String(text ?? '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    function renderNoteCard(note) {
        const isPdf = note.filename && note.filename.toLowerCase().endsWith('.pdf');
        const uploadedDate = note.uploaded_at ? String(note.uploaded_at).split('T')[0] : '';
        const tagsText = note.tags && note.tags.length ? note.tags.join(', ') : '';
        return `
        <div class="note-card" data-id="${escapeHtml(note.id)}" data-file-url="${escapeHtml(note.file_url || '')}" data-filename="${escapeHtml(note.filename || '')}">
            <div class="note-title">${escapeHtml(note.title)}</div>
            <div class="note-meta">작성자: ${escapeHtml(note.uploader || '익명')} | 태그: ${escapeHtml(tagsText)}<br>업로드: ${escapeHtml(uploadedDate)}</div>
            <div class="note-actions">
                ${isPdf ? '<button class="view-pdf" type="button">공부하기</button>' : ''}
                ${isPdf ? '<button class="summarize-pdf" type="button">정리하기</button>' : ''}
                ${isPdf ? '<button class="generate-question" type="button">질문 생성</button>' : ''}
                <button class="download" type="button">다운로드</button>
                <button class="delete" type="button">삭제</button>
            </div>
        </div>`;
    }

    function bindNoteActions() {
        document.querySelectorAll('.note-card').forEach((card) => {
            const noteId = card.getAttribute('data-id');
            const fileUrl = card.getAttribute('data-file-url');
            const filename = card.getAttribute('data-filename') || '';

            card.querySelector('.download').onclick = () => {
                window.open(`${API_BASE}/download/${noteId}`, '_blank');
            };

            card.querySelector('.delete').onclick = async () => {
                const password = prompt('이 노트를 삭제하려면 업로드 시 입력한 암호를 입력하세요:');
                if (!password) return;
                try {
                    const res = await fetch(`${API_BASE}/delete/${noteId}`, {
                        method: 'DELETE',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ password }),
                    });
                    const data = await res.json();
                    if (res.ok) {
                        alert('삭제 성공');
                        loadNotes();
                    } else {
                        alert(data.error || '삭제 실패');
                    }
                } catch (err) {
                    alert('네트워크 오류');
                }
            };

            const generateBtn = card.querySelector('.generate-question');
            if (generateBtn) {
                generateBtn.onclick = async () => {
                    generateBtn.textContent = '생성 중...';
                    generateBtn.disabled = true;
                    try {
                        const res = await fetch(`${API_BASE}/generate-question`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ note_id: noteId }),
                        });
                        const data = await res.json();
                        if (res.ok) {
                            document.getElementById('questionResult').innerText = data.questions;
                            showModal(document.getElementById('questionModal'));
                        } else {
                            alert(data.error || '질문 생성 실패');
                        }
                    } catch (err) {
                        alert('네트워크 오류');
                    } finally {
                        generateBtn.textContent = '질문 생성';
                        generateBtn.disabled = false;
                    }
                };
            }

            const viewPdfBtn = card.querySelector('.view-pdf');
            if (viewPdfBtn && fileUrl && filename.toLowerCase().endsWith('.pdf')) {
                viewPdfBtn.onclick = () => {
                    window.open(fileUrl, '_blank');
                };
            }

            const summarizeBtn = card.querySelector('.summarize-pdf');
            if (summarizeBtn) {
                summarizeBtn.onclick = async () => {
                    summarizeBtn.textContent = '정리 중...';
                    summarizeBtn.disabled = true;
                    try {
                        const res = await fetch(`${API_BASE}/summarize-pdf`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ note_id: noteId }),
                        });
                        const data = await res.json();
                        if (res.ok) {
                            document.getElementById('questionResult').innerText = data.summary;
                            showModal(document.getElementById('questionModal'));
                        } else {
                            alert(data.error || '정리 실패');
                        }
                    } catch (err) {
                        alert('네트워크 오류');
                    } finally {
                        summarizeBtn.textContent = '정리하기';
                        summarizeBtn.disabled = false;
                    }
                };
            }
        });
    }

    // ---------- 결과 저장 ----------
    document.getElementById('downloadTxtBtn').onclick = () => {
        const text = document.getElementById('questionResult').innerText;
        const blob = new Blob([text], { type: 'text/plain' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = '질문_생성_결과.txt';
        link.click();
    };

    document.getElementById('downloadPdfBtn').onclick = () => {
        const text = document.getElementById('questionResult').innerText;
        if (window.jspdf && window.jspdf.jsPDF) {
            const doc = new window.jspdf.jsPDF();
            const lines = doc.splitTextToSize(text, 180);
            doc.text(lines, 10, 10);
            doc.save('질문_생성_결과.pdf');
        } else {
            alert('PDF 저장 라이브러리가 로드되지 않았습니다.');
        }
    };

    document.getElementById('downloadMdBtn').onclick = () => {
        const text = document.getElementById('questionResult').innerText;
        const blob = new Blob([text], { type: 'text/markdown' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = '질문_생성_결과.md';
        link.click();
    };

    document.getElementById('closeModalBtn').onclick = () => {
        hideModal(document.getElementById('questionModal'));
    };

    // ---------- 관리자 ----------
    const adminBtn = document.getElementById('adminBtn');
    const adminModal = document.getElementById('adminModal');
    const adminPasswordInput = document.getElementById('adminPasswordInput');
    const adminLoginBtn = document.getElementById('adminLoginBtn');
    const adminCancelBtn = document.getElementById('adminCancelBtn');
    const adminLoginMsg = document.getElementById('adminLoginMsg');
    const adminMenuModal = document.getElementById('adminMenuModal');
    const adminMenuCloseBtn = document.getElementById('adminMenuCloseBtn');
    const deleteAllNotesBtn = document.getElementById('deleteAllNotesBtn');
    const resetDbBtn = document.getElementById('resetDbBtn');
    const adminMenuMsg = document.getElementById('adminMenuMsg');
    const adminChangePwBtn = document.getElementById('adminChangePwBtn');
    const adminChangePwModal = document.getElementById('adminChangePwModal');
    const adminNewPwInput = document.getElementById('adminNewPwInput');
    const adminChangePwSubmit = document.getElementById('adminChangePwSubmit');
    const adminChangePwCancel = document.getElementById('adminChangePwCancel');
    const adminChangePwMsg = document.getElementById('adminChangePwMsg');
    const adminNotesList = document.getElementById('adminNotesList');

    adminBtn.onclick = () => {
        adminPasswordInput.value = '';
        adminLoginMsg.textContent = '';
        showModal(adminModal);
    };

    adminCancelBtn.onclick = () => hideModal(adminModal);

    adminLoginBtn.onclick = async () => {
        const password = adminPasswordInput.value;
        if (!password) {
            adminLoginMsg.textContent = '비밀번호를 입력하세요.';
            return;
        }
        try {
            const res = await fetch(`${API_BASE}/admin/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ password }),
            });
            const data = await res.json();
            if (res.ok && data.token) {
                adminToken = data.token;
                hideModal(adminModal);
                adminMenuMsg.textContent = '';
                showModal(adminMenuModal);
                loadAdminNotes();
            } else {
                adminLoginMsg.textContent = data.error || '로그인 실패';
            }
        } catch (err) {
            adminLoginMsg.textContent = '네트워크 오류';
        }
    };

    adminMenuCloseBtn.onclick = () => hideModal(adminMenuModal);

    deleteAllNotesBtn.onclick = async () => {
        if (!confirm('정말 전체 노트를 삭제하시겠습니까?')) return;
        try {
            const res = await fetch(`${API_BASE}/admin/delete-all-notes`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${adminToken}`,
                },
            });
            const data = await res.json();
            if (res.ok) {
                adminMenuMsg.textContent = '전체 노트 삭제 성공!';
                loadNotes();
                loadAdminNotes();
            } else {
                adminMenuMsg.textContent = data.error || '삭제 실패';
            }
        } catch (err) {
            adminMenuMsg.textContent = '네트워크 오류';
        }
    };

    resetDbBtn.onclick = async () => {
        if (!confirm('정말 DB를 초기화하시겠습니까? 관리자 비밀번호도 초기값으로 돌아갑니다.')) return;
        try {
            const res = await fetch(`${API_BASE}/admin/reset-db`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${adminToken}`,
                },
            });
            const data = await res.json();
            if (res.ok) {
                adminToken = null;
                adminMenuMsg.textContent = 'DB 초기화 성공! 다시 로그인해 주세요.';
                hideModal(adminMenuModal);
                loadNotes();
            } else {
                adminMenuMsg.textContent = data.error || '초기화 실패';
            }
        } catch (err) {
            adminMenuMsg.textContent = '네트워크 오류';
        }
    };

    adminChangePwBtn.onclick = () => {
        adminNewPwInput.value = '';
        adminChangePwMsg.textContent = '';
        showModal(adminChangePwModal);
    };

    adminChangePwCancel.onclick = () => hideModal(adminChangePwModal);

    adminChangePwSubmit.onclick = async () => {
        const newPassword = adminNewPwInput.value;
        if (!newPassword || newPassword.length < 4) {
            adminChangePwMsg.textContent = '4자 이상 입력하세요.';
            return;
        }
        try {
            const res = await fetch(`${API_BASE}/admin/change-password`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${adminToken}`,
                },
                body: JSON.stringify({ new_password: newPassword }),
            });
            const data = await res.json();
            if (res.ok) {
                adminChangePwMsg.textContent = '비밀번호 변경 성공!';
                setTimeout(() => hideModal(adminChangePwModal), 1000);
            } else {
                adminChangePwMsg.textContent = data.error || '변경 실패';
            }
        } catch (err) {
            adminChangePwMsg.textContent = '네트워크 오류';
        }
    };

    async function loadAdminNotes() {
        if (!adminNotesList) return;
        adminNotesList.innerHTML = '불러오는 중...';
        try {
            const res = await fetch(`${API_BASE}/notes`);
            const data = await res.json();
            if (!res.ok || !data.notes) {
                adminNotesList.innerHTML = '<div class="error-msg">노트 목록 불러오기 실패</div>';
                return;
            }
            if (data.notes.length === 0) {
                adminNotesList.innerHTML = '<div style="color:#888;">노트가 없습니다.</div>';
                return;
            }
            adminNotesList.innerHTML = data.notes.map((note) => `
                <div class="admin-note-row">
                    <span>${escapeHtml(note.title)} (${escapeHtml(note.filename)})</span>
                    <button class="admin-delete-note btn-danger" data-id="${escapeHtml(note.id)}" type="button">삭제</button>
                </div>
            `).join('');

            adminNotesList.querySelectorAll('.admin-delete-note').forEach((btn) => {
                btn.onclick = async () => {
                    if (!confirm('정말 이 노트를 삭제하시겠습니까?')) return;
                    const noteId = btn.getAttribute('data-id');
                    try {
                        const res = await fetch(`${API_BASE}/admin/delete-note/${noteId}`, {
                            method: 'DELETE',
                            headers: { Authorization: `Bearer ${adminToken}` },
                        });
                        const data = await res.json();
                        if (res.ok) {
                            btn.parentElement.remove();
                            loadNotes();
                        } else {
                            alert(data.error || '삭제 실패');
                        }
                    } catch (err) {
                        alert('네트워크 오류');
                    }
                };
            });
        } catch (err) {
            adminNotesList.innerHTML = '<div class="error-msg">네트워크 오류</div>';
        }
    }
});
