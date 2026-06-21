import redis
import os
import json
from dotenv import load_dotenv
load_dotenv()
REDIS_URL=os.getenv("REDIS_URL","redis://localhost:6379")
#Create Redis client - connect to Redis Server
redis_client=redis.from_url(REDIS_URL,decode_responses=True)
CACHE_EXPIRY=300
def get_cached(key: str):
    """Get value from cache. Returns None if not found"""
    try:
        value = redis_client.get(key)
        if(value):
            return json.loads(value) #convert string back to dict
        return None
    except Exception:
        return None #if Redis is down , don't crash the app
def set_cached(key:str , value:dict):
    """Store value in cache with expiry"""
    try:
        redis_client.setex(key,CACHE_EXPIRY,
                           json.dumps(value) #convert dict to string for storage
                           )
    except Exception:
        pass # if Redis is down, just skip caching
def deleted_cached(key:str):
    """Delete a key from cache (call this when data changes)."""
    try:
        redis_client.delete(key)
    except Exception:
        pass