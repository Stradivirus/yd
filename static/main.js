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
            downloadLink.innerHTML = `<a href="${result.download_url}" download="${result.filename}" class="download-btn">👉 파일 다운로드</a>`;
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