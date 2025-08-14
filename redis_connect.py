import redis
import json

# Docker Compose 환경에서는 host='redis'
r = redis.Redis(host='redis', port=6379, db=0)

# 파일 정보 저장 (3일 = 259200초)
file_info = {"filename": "test.mp3", "status": "ready"}
r.setex("file:test.mp3", 259200, json.dumps(file_info))

# 파일 정보 조회
data = r.get("file:test.mp3")
if data:
    info = json.loads(data)
    print(info)