from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import yt_dlp
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
    # static/index.html 반환
    return FileResponse("static/index.html")

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
                'noplaylist': True,
            }
        else:  # mp4
            ydl_opts = {
                'format': 'best[ext=mp4]/best',
                'outtmpl': f'{downloads_path}/%(title)s.%(ext)s',
                'no_warnings': True,
                'ignoreerrors': True,
                'noplaylist': True,
            }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Unknown')
            duration = info.get('duration', 0)
            ext = 'mp3' if format_type == 'mp3' else 'mp4'
            filename = f"{title}.{ext}"
            filepath = downloads_dir / filename

            if duration and duration > 1800:
                raise HTTPException(status_code=400, detail="30분 이상의 영상은 다운로드할 수 없습니다")
            
            ydl.download([url])
            
        return JSONResponse({
            "success": True, 
            "title": title,
            "format": format_type,
            "filename": filename,
            "download_url": f"/downloads/{filename}",
            "message": "다운로드가 완료되었습니다"
        })
    
    except yt_dlp.utils.DownloadError as e:
        raise HTTPException(status_code=400, detail=f"다운로드 오류: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")

@app.get("/downloads/{filename}")
async def serve_file(filename: str):
    file_path = downloads_dir / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다")
    return FileResponse(str(file_path), filename=filename)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "YouTube Downloader API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
