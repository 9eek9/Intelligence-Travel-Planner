"""
Simple in-memory cache for API responses
"""
import time
from typing import Any, Optional
import hashlib
import json

class SimpleCache:
    def __init__(self, ttl_seconds=300):  # 5 minute cache
        self.cache = {}
        self.ttl = ttl_seconds
    
    def _make_key(self, *args, **kwargs):
        """Create a hash key from arguments"""
        data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
        return hashlib.md5(data.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value if not expired"""
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                print(f"Cache HIT for {key[:8]}...")
                return value
            else:
                # Expired, remove it
                del self.cache[key]
        return None
    
    def set(self, key: str, value: Any):
        """Cache a value with timestamp"""
        self.cache[key] = (value, time.time())
        print(f"📦 Cached {key[:8]}...")
    
    def clear_expired(self):
        """Remove expired entries"""
        current_time = time.time()
        expired = [k for k, (_, ts) in self.cache.items() if current_time - ts >= self.ttl]
        for k in expired:
            del self.cache[key]

# Global cache instance
api_cache = SimpleCache(ttl_seconds=300)
