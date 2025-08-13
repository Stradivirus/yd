from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import yt_dlp
import os
import tempfile
import asyncio
from pathlib import Path

app = FastAPI(title="YouTube Downloader")

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Create downloads directory
downloads_dir = Path("downloads")
downloads_dir.mkdir(exist_ok=True)

class DownloadRequest(BaseModel):
    url: str
    format: str  # mp3 or mp4

@app.get("/", response_class=HTMLResponse)
async def read_root():
    html_content = """
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>YouTube 다운로더</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Arial', sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 20px;
            }
            
            .container {
                background: white;
                padding: 2.5rem;
                border-radius: 20px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                width: 100%;
                max-width: 500px;
                transition: transform 0.3s ease;
            }
            
            .container:hover {
                transform: translateY(-5px);
            }
            
            h1 {
                text-align: center;
                margin-bottom: 2rem;
                color: #333;
                font-size: 2rem;
            }
            
            .input-group {
                margin-bottom: 2rem;
            }
            
            label {
                display: block;
                margin-bottom: 0.8rem;
                font-weight: bold;
                color: #555;
                font-size: 1.1rem;
            }
            
            input[type="url"] {
                width: 100%;
                padding: 1.2rem;
                border: 2px solid #ddd;
                border-radius: 12px;
                font-size: 1rem;
                transition: border-color 0.3s ease;
            }
            
            input[type="url"]:focus {
                outline: none;
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }
            
            .format-group {
                display: flex;
                gap: 1rem;
                margin-bottom: 2rem;
            }
            
            .format-option {
                flex: 1;
                padding: 1.2rem;
                border: 2px solid #ddd;
                border-radius: 12px;
                cursor: pointer;
                text-align: center;
                transition: all 0.3s ease;
                font-weight: bold;
                font-size: 1rem;
            }
            
            .format-option:hover {
                border-color: #667eea;
                transform: translateY(-2px);
            }
            
            .format-option.selected {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border-color: #667eea;
            }
            
            button {
                width: 100%;
                padding: 1.2rem;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 1.2rem;
                font-weight: bold;
                cursor: pointer;
                transition: all 0.3s ease;
            }
            
            button:hover:not(:disabled) {
                transform: translateY(-3px);
                box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
            }
            
            button:disabled {
                opacity: 0.6;
                cursor: not-allowed;
                transform: none;
            }
            
            .status {
                margin-top: 1.5rem;
                padding: 1.2rem;
                border-radius: 12px;
                display: none;
                font-weight: bold;
            }
            
            .status.success {
                background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
                color: #155724;
                border: 2px solid #c3e6cb;
            }
            
            .status.error {
                background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
                color: #721c24;
                border: 2px solid #f5c6cb;
            }
            
            .status.loading {
                background: linear-gradient(135deg, #cce7ff 0%, #b3d9ff 100%);
                color: #004085;
                border: 2px solid #b3d9ff;
            }
            
            .spinner {
                display: inline-block;
                width: 20px;
                height: 20px;
                border: 3px solid #f3f3f3;
                border-top: 3px solid #667eea;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin-right: 10px;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎵 YouTube 다운로더</h1>
            
            <div class="input-group">
                <label for="url">YouTube URL:</label>
                <input type="url" id="url" placeholder="https://youtube.com/watch?v=..." required>
            </div>
            
            <div class="format-group">
                <div class="format-option selected" data-format="mp3">
                    🎵 MP3 (음성)
                </div>
                <div class="format-option" data-format="mp4">
                    🎬 MP4 (동영상)
                </div>
            </div>
            
            <button id="downloadBtn" onclick="downloadVideo()">다운로드 시작</button>
            
            <div id="status" class="status"></div>
        </div>

        <script>
            let selectedFormat = 'mp3';
            
            // 포맷 선택
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
            
            async function downloadVideo() {
                const url = document.getElementById('url').value;
                const button = document.getElementById('downloadBtn');
                
                if (!url) {
                    showStatus('❌ YouTube URL을 입력해주세요!', 'error');
                    return;
                }
                
                // URL 유효성 검사
                if (!url.includes('youtube.com') && !url.includes('youtu.be')) {
                    showStatus('❌ 올바른 YouTube URL을 입력해주세요!', 'error');
                    return;
                }
                
                button.disabled = true;
                button.textContent = '다운로드 중...';
                showStatus('<span class="spinner"></span>다운로드를 시작합니다...', 'loading');
                
                try {
                    const response = await fetch('/download', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            url: url,
                            format: selectedFormat
                        })
                    });
                    
                    const result = await response.json();
                    
                    if (response.ok && result.success) {
                        showStatus(`✅ "${result.title}" 다운로드 완료!<br>📁 downloads 폴더를 확인해주세요.`, 'success');
                    } else {
                        showStatus(`❌ 오류: ${result.error || '알 수 없는 오류가 발생했습니다.'}`, 'error');
                    }
                    
                } catch (error) {
                    showStatus(`❌ 네트워크 오류: ${error.message}`, 'error');
                } finally {
                    button.disabled = false;
                    button.textContent = '다운로드 시작';
                }
            }
            
            // Enter 키로 다운로드
            document.getElementById('url').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    downloadVideo();
                }
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/download")
async def download_video(request: DownloadRequest):
    try:
        url = request.url.strip()
        format_type = request.format
        
        if not url:
            raise HTTPException(status_code=400, detail="YouTube URL을 입력해주세요")
        
        # URL 유효성 검사
        if not ("youtube.com" in url or "youtu.be" in url):
            raise HTTPException(status_code=400, detail="올바른 YouTube URL을 입력해주세요")
        
        downloads_path = str(downloads_dir.absolute())
        
        if format_type == 'mp3':
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': f'{downloads_path}/%(title)s.%(ext)s',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'extractaudio': True,
                'audioformat': 'mp3',
                'no_warnings': True,
                'ignoreerrors': True,
                'noplaylist': True,  # 플레이리스트 방지
            }
        else:  # mp4
            ydl_opts = {
                'format': 'best[ext=mp4]/best',
                'outtmpl': f'{downloads_path}/%(title)s.%(ext)s',
                'no_warnings': True,
                'ignoreerrors': True,
                'noplaylist': True,  # 플레이리스트 방지
            }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # 정보 추출
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Unknown')
            duration = info.get('duration', 0)
            
            # 너무 긴 영상 체크 (30분 이상)
            if duration and duration > 1800:
                raise HTTPException(status_code=400, detail="30분 이상의 영상은 다운로드할 수 없습니다")
            
            # 다운로드 실행
            ydl.download([url])
            
        return JSONResponse({
            "success": True, 
            "title": title,
            "format": format_type,
            "message": "다운로드가 완료되었습니다"
        })
    
    except yt_dlp.utils.DownloadError as e:
        raise HTTPException(status_code=400, detail=f"다운로드 오류: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "YouTube Downloader API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
