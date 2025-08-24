"""
Redis-based caching service for Beacon Commercial Register API
"""
import json
import asyncio
from typing import Optional, Any, Union
from datetime import timedelta
import logging

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

from .config import REDIS_URL, CACHE_TTL
from .exceptions import ServiceUnavailableError

logger = logging.getLogger(__name__)


class CacheService:
    """Redis-based caching service with fallback to in-memory"""
    
    def __init__(self):
        self.redis_client = None
        self._fallback_cache = {}
        self._fallback_timestamps = {}
        
        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.from_url(REDIS_URL)
                logger.info("Redis cache initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Redis cache: {e}. Using fallback.")
                self.redis_client = None
        else:
            logger.warning("Redis not available. Using in-memory fallback cache.")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            if self.redis_client:
                value = await self.redis_client.get(key)
                if value:
                    return json.loads(value)
            else:
                return self._get_fallback(key)
        except Exception as e:
            logger.warning(f"Cache get failed for key {key}: {e}")
            return self._get_fallback(key)
        
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with TTL"""
        try:
            if self.redis_client:
                ttl = ttl or CACHE_TTL * 3600
                await self.redis_client.setex(key, ttl, json.dumps(value))
                return True
            else:
                return self._set_fallback(key, value, ttl)
        except Exception as e:
            logger.warning(f"Cache set failed for key {key}: {e}")
            return self._set_fallback(key, value, ttl)
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            if self.redis_client:
                await self.redis_client.delete(key)
                return True
            else:
                return self._delete_fallback(key)
        except Exception as e:
            logger.warning(f"Cache delete failed for key {key}: {e}")
            return self._delete_fallback(key)
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        try:
            if self.redis_client:
                return bool(await self.redis_client.exists(key))
            else:
                return key in self._fallback_cache
        except Exception as e:
            logger.warning(f"Cache exists check failed for key {key}: {e}")
            return key in self._fallback_cache
    
    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment counter in cache"""
        try:
            if self.redis_client:
                return await self.redis_client.incr(key, amount)
            else:
                current = self._fallback_cache.get(key, 0)
                if isinstance(current, (int, float)):
                    new_value = current + amount
                    self._fallback_cache[key] = new_value
                    return new_value
                return None
        except Exception as e:
            logger.warning(f"Cache increment failed for key {key}: {e}")
            return None
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration for key"""
        try:
            if self.redis_client:
                return bool(await self.redis_client.expire(key, ttl))
            else:
                return True
        except Exception as e:
            logger.warning(f"Cache expire failed for key {key}: {e}")
            return False
    
    async def health_check(self) -> bool:
        """Check if cache service is healthy"""
        try:
            if self.redis_client:
                await self.redis_client.ping()
                return True
            else:
                return True
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return False
    
    def _get_fallback(self, key: str) -> Optional[Any]:
        """Get value from fallback in-memory cache"""
        if key in self._fallback_cache:
            timestamp = self._fallback_timestamps.get(key, 0)
            if asyncio.get_event_loop().time() - timestamp < CACHE_TTL * 3600:
                return self._fallback_cache[key]
            else:
                del self._fallback_cache[key]
                del self._fallback_timestamps[key]
        return None
    
    def _set_fallback(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in fallback in-memory cache"""
        try:
            self._fallback_cache[key] = value
            self._fallback_timestamps[key] = asyncio.get_event_loop().time()
            
            if len(self._fallback_cache) > 1000:
                self._cleanup_fallback_cache()
            
            return True
        except Exception as e:
            logger.error(f"Fallback cache set failed: {e}")
            return False
    
    def _delete_fallback(self, key: str) -> bool:
        """Delete key from fallback cache"""
        try:
            if key in self._fallback_cache:
                del self._fallback_cache[key]
                del self._fallback_timestamps[key]
            return True
        except Exception as e:
            logger.error(f"Fallback cache delete failed: {e}")
            return False
    
    def _cleanup_fallback_cache(self):
        """Clean up expired entries from fallback cache"""
        current_time = asyncio.get_event_loop().time()
        expired_keys = [
            key for key, timestamp in self._fallback_timestamps.items()
            if current_time - timestamp > CACHE_TTL * 3600
        ]
        
        for key in expired_keys:
            del self._fallback_cache[key]
            del self._fallback_timestamps[key]
        
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired fallback cache entries")
    
    async def close(self):
        """Close cache connections"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis cache connections closed")


cache_service = CacheService()


async def get_cache() -> CacheService:
    """Dependency to get cache service"""
    return cache_service
