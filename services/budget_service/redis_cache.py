import redis
import json
from datetime import timedelta

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cache_get(key: str):
    """Get cached data"""
    data = redis_client.get(key)
    return json.loads(data) if data else None

def cache_set(key: str, value: dict, ttl: int = 300):
    """Cache data for TTL seconds (default 5 min)"""
    redis_client.setex(key, ttl, json.dumps(value))
