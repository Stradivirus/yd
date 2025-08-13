# YouTube Downloader

FastAPI와 yt-dlp를 사용한 간단한 YouTube 다운로더입니다.

## 기능
- YouTube 동영상을 MP3 또는 MP4로 다운로드
- 웹 인터페이스 제공
- Docker 지원

## 설치 및 실행

### Docker 사용 (권장)

1. **Docker 이미지 빌드**
```bash
docker build -t youtube-downloader .
```

2. **컨테이너 실행**
```bash
docker run -p 8000:8000 -v $(pwd)/downloads:/app/downloads youtube-downloader
```

3. **브라우저에서 접속**
```
http://localhost:8000
```

### 로컬 실행

1. **의존성 설치**
```bash
pip install -r requirements.txt
```

2. **애플리케이션 실행**
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## 사용법

1. 웹 브라우저에서 `http://localhost:8000` 접속
2. YouTube URL 입력
3. 다운로드 형식 선택 (MP3/MP4)
4. 다운로드 버튼 클릭
5. `downloads` 폴더에서 파일 확인

## 주의사항

- 저작권이 있는 콘텐츠의 다운로드는 법적 문제가 될 수 있습니다
- 30분 이상의 긴 영상은 다운로드가 제한됩니다
- FFmpeg가 설치되어 있어야 MP3 변환이 가능합니다

## API 엔드포인트

- `GET /` - 웹 인터페이스
- `POST /download` - 다운로드 요청
- `GET /health` - 헬스 체크
