"""Simple in-memory cache with TTL for performance optimization."""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import hashlib


class SimpleCache:
    """Thread-safe in-memory cache with TTL support."""
    
    def __init__(self):
        self._cache: Dict[str, tuple[Any, datetime]] = {}
    
    def get(self, key: str, default: Optional[Any] = None) -> Optional[Any]:
        """Get value from cache if not expired."""
        if key not in self._cache:
            return default
        
        value, expiry = self._cache[key]
        if datetime.utcnow() > expiry:
            del self._cache[key]
            return default
        
        return value
    
    def set(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        """Set value in cache with TTL."""
        expiry = datetime.utcnow() + timedelta(seconds=ttl_seconds)
        self._cache[key] = (value, expiry)
    
    def delete(self, key: str) -> None:
        """Delete key from cache."""
        if key in self._cache:
            del self._cache[key]
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
    
    def _cleanup_expired(self) -> None:
        """Remove expired entries (call periodically if needed)."""
        now = datetime.utcnow()
        expired_keys = [
            key for key, (_, expiry) in self._cache.items()
            if now > expiry
        ]
        for key in expired_keys:
            del self._cache[key]


# Global cache instance
_cache = SimpleCache()


def get_cache() -> SimpleCache:
    """Get the global cache instance."""
    return _cache


def cache_key(prefix: str, *args: Any) -> str:
    """Generate a cache key from prefix and arguments."""
    key_str = f"{prefix}:{':'.join(str(arg) for arg in args)}"
    return hashlib.md5(key_str.encode()).hexdigest()

