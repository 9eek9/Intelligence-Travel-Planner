from functools import lru_cache
import hashlib
import json

# Cache for 5 minutes (300 seconds)
@lru_cache(maxsize=100)
def cache_key(origin, destination, depart_date, return_date):
    """Generate cache key from search params"""
    data = f"{origin}_{destination}_{depart_date}_{return_date}"
    return hashlib.md5(data.encode()).hexdigest()
