let selectedFormat = 'mp3';

document.querySelectorAll('.format-option').forEach(option => {
    option.addEventListener('click', function() {
        document.querySelectorAll('.format-option').forEach(opt => 
            opt.classList.remove('selected'));
        this.classList.add('selected');
        selectedFormat = this.dataset.format;
    });
});

function showStatus(message, type) {
    const status = document.getElementById('status');
    status.innerHTML = message;
    status.className = `status ${type}`;
    status.style.display = 'block';
}

function setProgress(percent) {
    const bar = document.getElementById('progressBar');
    const progress = bar.querySelector('.progress');
    bar.style.display = 'block';
    progress.style.width = percent + '%';
}

function hideProgress() {
    const bar = document.getElementById('progressBar');
    bar.style.display = 'none';
    bar.querySelector('.progress').style.width = '0%';
}

async function downloadVideo() {
    const url = document.getElementById('url').value;
    const button = document.getElementById('downloadBtn');
    const downloadLink = document.getElementById('downloadLink');
    downloadLink.innerHTML = '';
    hideProgress();

    if (!url) {
        showStatus('❌ YouTube URL을 입력해주세요!', 'error');
        return;
    }
    if (!url.includes('youtube.com') && !url.includes('youtu.be')) {
        showStatus('❌ 올바른 YouTube URL을 입력해주세요!', 'error');
        return;
    }

    button.disabled = true;
    button.textContent = '변환 중...';
    showStatus('<span class="spinner"></span>변환을 시작합니다...', 'loading');
    setProgress(30);

    try {
        const response = await fetch('/download', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: url, format: selectedFormat })
        });
        setProgress(80);

        const result = await response.json();

        if (response.ok && result.success) {
            setProgress(100);
            showStatus(`✅ "${result.title}" 변환 완료!`, 'success');
            fetchFileList();
            downloadLink.innerHTML = '';
            hideProgress(); // 변환 완료 시 진행바 숨김
        } else {
            showStatus(`❌ 오류: ${result.detail || result.error || '알 수 없는 오류가 발생했습니다.'}`, 'error');
            hideProgress();
        }
    } catch (error) {
        showStatus(`❌ 네트워크 오류: ${error.message}`, 'error');
        hideProgress();
    } finally {
        button.disabled = false;
        button.textContent = '변환 시작';
    }
}

document.getElementById('url').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        downloadVideo();
    }
});

async function deleteFile(filename) {
    if (!confirm('정말 삭제하시겠습니까?')) return;
    try {
        const res = await fetch(`/files/${encodeURIComponent(filename)}`, { method: 'DELETE' });
        if (res.ok) {
            fetchFileList();
        } else {
            alert('삭제 실패');
        }
    } catch (e) {
        alert('삭제 중 오류 발생');
    }
}

async function fetchFileList() {
    try {
        const res = await fetch('/files');
        const data = await res.json();
        const fileList = document.getElementById('fileList');
        fileList.innerHTML = '';
        if (data.files && data.files.length > 0) {
            data.files.forEach(file => {
                const li = document.createElement('li');
                li.innerHTML = `
                    <span class="filename">${file.filename}</span>
                    <div class="file-actions">
                        <span class="remain">남은 시간: ${formatRemain(file.remain)}</span>
                        <button type="button" class="download-btn" onclick="downloadFile('${file.filename.replace(/'/g, "\\'")}')">다운로드</button>
                        <button class="delete-btn" onclick="deleteFile('${file.filename.replace(/'/g, "\\'")}')">삭제</button>
                    </div>
                `;
                fileList.appendChild(li);
            });
        } else {
            fileList.innerHTML = '<li>저장된 파일 없음</li>';
        }
    } catch (e) {
        // 네트워크 오류 등 무시
    }
}

function formatRemain(sec) {
    if (sec < 60) return `${sec}초`;
    if (sec < 3600) return `${Math.floor(sec/60)}분`;
    return `${Math.floor(sec/3600)}시간`;
}

function downloadFile(filename) {
    const a = document.createElement('a');
    a.href = '/downloads/' + encodeURIComponent(filename);
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}

// 5초마다 파일 목록 갱신
setInterval(fetchFileList, 1800000);
window.addEventListener('DOMContentLoaded', fetchFileList);