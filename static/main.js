/* filepath: /home/work/YD/static/main.js */
class YouTubeDownloader {
    constructor() {
        this.selectedFormat = 'mp3';
        this.init();
    }

    init() {
        this.bindEvents();
        this.fetchFileList();
        setInterval(() => this.fetchFileList(), 1800000);
    }

    bindEvents() {
        // Format 선택
        document.querySelectorAll('.format-option').forEach(option => {
            option.addEventListener('click', (e) => this.selectFormat(e.target));
        });

        // Enter 키 이벤트
        document.getElementById('url').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.downloadVideo();
        });
    }

    selectFormat(element) {
        document.querySelectorAll('.format-option').forEach(opt => 
            opt.classList.remove('selected'));
        element.classList.add('selected');
        this.selectedFormat = element.dataset.format;
    }

    showStatus(message, type) {
        const status = document.getElementById('status');
        status.innerHTML = message;
        status.className = `status ${type}`;
        status.style.display = 'block';
    }

    updateProgress(percent) {
        const bar = document.getElementById('progressBar');
        const progress = bar.querySelector('.progress');
        bar.style.display = 'block';
        progress.style.width = `${percent}%`;
    }

    hideProgress() {
        const bar = document.getElementById('progressBar');
        bar.style.display = 'none';
        bar.querySelector('.progress').style.width = '0%';
    }

    validateUrl(url) {
        if (!url) {
            this.showStatus('❌ YouTube URL을 입력해주세요!', 'error');
            return false;
        }
        if (!url.includes('youtube.com') && !url.includes('youtu.be')) {
            this.showStatus('❌ 올바른 YouTube URL을 입력해주세요!', 'error');
            return false;
        }
        return true;
    }

    async downloadVideo() {
        const url = document.getElementById('url').value.trim();
        const button = document.getElementById('downloadBtn');
        
        if (!this.validateUrl(url)) return;

        // UI 상태 업데이트
        button.disabled = true;
        button.textContent = '변환 중...';
        this.showStatus('🔄 변환을 시작합니다...', 'loading');
        this.updateProgress(30);

        try {
            const response = await fetch('/download', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url, format: this.selectedFormat })
            });

            this.updateProgress(80);
            const result = await response.json();

            if (response.ok && result.success) {
                this.updateProgress(100);
                this.showStatus(`✅ "${result.title}" 변환 완료!`, 'success');
                this.fetchFileList();
                setTimeout(() => this.hideProgress(), 2000); // 2초 후 숨김
            } else {
                this.showStatus(`❌ 오류: ${result.detail || result.error || '알 수 없는 오류'}`, 'error');
                this.hideProgress();
            }
        } catch (error) {
            this.showStatus(`❌ 네트워크 오류: ${error.message}`, 'error');
            this.hideProgress();
        } finally {
            button.disabled = false;
            button.textContent = '변환 시작';
        }
    }

    async deleteFile(filename) {
        if (!confirm('정말 삭제하시겠습니까?')) return;
        
        try {
            const response = await fetch(`/files/${encodeURIComponent(filename)}`, { 
                method: 'DELETE' 
            });
            
            if (response.ok) {
                this.fetchFileList();
            } else {
                alert('삭제 실패');
            }
        } catch (error) {
            alert('삭제 중 오류 발생');
        }
    }

    async fetchFileList() {
        try {
            const response = await fetch('/files');
            const data = await response.json();
            this.renderFileList(data.files || []);
        } catch (error) {
            console.error('파일 목록 로드 실패:', error);
        }
    }

    renderFileList(files) {
        const fileList = document.getElementById('fileList');
        
        if (files.length === 0) {
            fileList.innerHTML = '<li>저장된 파일 없음</li>';
            return;
        }

        fileList.innerHTML = files.map(file => `
            <li>
                <span class="filename">${this.escapeHtml(file.filename)}</span>
                <div class="file-actions">
                    <span class="remain">남은 시간: ${this.formatRemain(file.remain)}</span>
                    <button type="button" class="btn download-btn" onclick="downloader.downloadFile('${this.escapeJs(file.filename)}')">다운로드</button>
                    <button class="btn delete-btn" onclick="downloader.deleteFile('${this.escapeJs(file.filename)}')">삭제</button>
                </div>
            </li>
        `).join('');
    }

    formatRemain(sec) {
        if (sec < 60) return `${sec}초`;
        if (sec < 3600) return `${Math.floor(sec/60)}분`;
        return `${Math.floor(sec/3600)}시간`;
    }

    downloadFile(filename) {
        const a = document.createElement('a');
        a.href = `/downloads/${encodeURIComponent(filename)}`;
        a.download = filename;
        a.style.display = 'none';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    }

    // XSS 방지
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    escapeJs(text) {
        return text.replace(/'/g, "\\'").replace(/"/g, '\\"');
    }
}

// 전역 인스턴스 생성
const downloader = new YouTubeDownloader();

// 전역 함수들 (HTML에서 호출용)
function downloadVideo() { downloader.downloadVideo(); }