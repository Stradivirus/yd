from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import yt_dlp
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
import re
import threading
import os
import unicodedata
from redis_connect import get_redis_connection, save_file_info, delete_file_info

app = FastAPI(title="YouTube Downloader")

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Create downloads directory
downloads_dir = Path("downloads")
downloads_dir.mkdir(exist_ok=True)

# Redis 연결
r = get_redis_connection()

class DownloadRequest(BaseModel):
    url: str
    format: str  # mp3 or mp4

@app.get("/", response_class=HTMLResponse)
async def read_root():
    # static/index.html 반환
    return FileResponse("static/index.html")

def safe_filename(name, maxlen=80):
    import unicodedata
    name = unicodedata.normalize('NFKD', name)
    name = re.sub(r'[^\w\u3131-\u3163\uac00-\ud7a3 ._-]', '_', name)
    if len(name) > maxlen:
        name = name[:maxlen-3] + '...'
    return name

@app.post("/download")
async def download_video(request: DownloadRequest):
    try:
        import urllib.parse
        url = request.url.strip()
        # 유튜브 URL에서 &list= 등 플레이리스트 파라미터 자동 제거
        parsed = urllib.parse.urlparse(url)
        query = urllib.parse.parse_qs(parsed.query)
        # list, index, start_radio, playlist 등 플레이리스트 관련 파라미터 제거
        for key in ["list", "index", "start_radio", "playlist", "playnext"]:
            if key in query:
                del query[key]
        new_query = urllib.parse.urlencode(query, doseq=True)
        url = urllib.parse.urlunparse(parsed._replace(query=new_query))
        format_type = request.format
        
        if not url:
            raise HTTPException(status_code=400, detail="YouTube URL을 입력해주세요")
        
        # URL 유효성 검사
        if not ("youtube.com" in url or "youtu.be" in url):
            raise HTTPException(status_code=400, detail="올바른 YouTube URL을 입력해주세요")
        
        downloads_path = str(downloads_dir.absolute())
        
        # 제목 미리 추출 및 safe_filename 적용
        info = yt_dlp.YoutubeDL().extract_info(url, download=False)
        title = info.get('title', 'Unknown')
        duration = info.get('duration', 0)
        ext = 'mp3' if format_type == 'mp3' else 'mp4'
        safe_title = safe_filename(title)
        filename = f"{safe_title}.{ext}"

        # duration 체크
        if duration and duration > 1800:
            raise HTTPException(status_code=400, detail="30분 이상의 영상은 다운로드할 수 없습니다")

        if format_type == 'mp3':
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': f'{downloads_path}/{safe_title}.%(ext)s',
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
                'playlist_items': '1',  # 무조건 첫 번째 영상만 다운로드
            }
        else:  # mp4
            ydl_opts = {
                'format': 'best[ext=mp4]/best',
                'outtmpl': f'{downloads_path}/{safe_title}.%(ext)s',
                'no_warnings': True,
                'ignoreerrors': True,
                'noplaylist': True,
                'playlist_items': '1',  # 무조건 첫 번째 영상만 다운로드
            }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Redis에 파일 정보 저장
        save_file_info(r, filename, title, format_type)
        
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
    # filename은 이미 safe_filename을 거쳐 저장된 값이므로 추가 변환 없이 사용
    file_path = downloads_dir / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다")
    return FileResponse(str(file_path), filename=filename)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "YouTube Downloader API is running"}

@app.get("/files")
async def list_files():
    keys = r.keys("file:*")
    now = int(time.time())
    files = []
    for key in keys:
        data = r.get(key)
        if data:
            info = json.loads(data)
            remain = info["expire"] - now
            if remain > 0:
                info["remain"] = remain
                files.append(info)
    # 남은 시간 오름차순 정렬
    files.sort(key=lambda x: x["remain"])
    return {"files": files}

def delete_expired_files():
    while True:
        now = int(time.time())
        keys = r.keys("file:*")
        for key in keys:
            data = r.get(key)
            if data:
                info = json.loads(data)
                if info["expire"] < now:
                    # 파일 삭제
                    file_path = downloads_dir / info["filename"]
                    try:
                        if file_path.exists():
                            os.remove(file_path)
                    except Exception:
                        pass
                    r.delete(key)
        time.sleep(3600)  # 1시간마다 실행

@app.on_event("startup")
def start_file_cleaner():
    t = threading.Thread(target=delete_expired_files, daemon=True)
    t.start()

@app.delete("/files/{filename}")
def delete_file(filename: str):
    safe_name = safe_filename(filename)
    delete_file_info(r, safe_name)
    file_path = downloads_dir / safe_name
    try:
        if file_path.exists():
            file_path.unlink()
    except Exception:
        pass
    return Response(status_code=204)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)