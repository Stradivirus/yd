import redis
import json
import os
import time

def get_redis_connection():
    """Redis 연결 반환"""
    host = os.getenv("REDIS_HOST", "redis")
    port = int(os.getenv("REDIS_PORT", 6379))
    return redis.Redis(host=host, port=port, db=0, decode_responses=True)

# Redis 만료 시간 상수
REDIS_EXPIRE = 60 * 60 * 24 * 3  # 3일

def save_file_info(r, filename, title, format_type):
    """파일 정보를 Redis에 저장"""
    now = int(time.time())
    file_info = {
        "filename": filename,
        "title": title,
        "format": format_type,
        "created": now,
        "expire": now + REDIS_EXPIRE
    }
    r.setex(f"file:{filename}", REDIS_EXPIRE, json.dumps(file_info))
    return file_info

def get_file_info(r, filename):
    """Redis에서 파일 정보 조회"""
    data = r.get(f"file:{filename}")
    if data:
        return json.loads(data)
    return None

def delete_file_info(r, filename):
    """Redis에서 파일 정보 삭제"""
    return r.delete(f"file:{filename}")