import redis
import pickle
from typing import Any, Optional, cast


class RedisStore:
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        default_ttl: Optional[int] = None,
        prefix: str = "video:"
    ) -> None:
        self.r: redis.Redis = redis.from_url(redis_url, decode_responses=False)
        self.default_ttl = default_ttl
        self.prefix = prefix

    def _key(self, key: str) -> str:
        return f"{self.prefix}{key}"

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        k = self._key(key)
        serialized: bytes = pickle.dumps(value)
        effective_ttl = ttl if ttl is not None else self.default_ttl
        if effective_ttl is not None:
            self.r.setex(k, int(effective_ttl), serialized)
        else:
            self.r.set(k, serialized)

    def get(self, key: str) -> Any | None:
        k = self._key(key)
        data = self.r.get(k)
        if data is None:
            return None
        if not isinstance(data, (bytes, bytearray)):
            return None
        return pickle.loads(cast(bytes, data))

    def exists(self, key: str) -> bool:
        k = self._key(key)
        return bool(self.r.exists(k))

    def delete(self, key: str) -> None:
        k = self._key(key)
        self.r.delete(k)

    def ttl(self, key: str) -> int:
        """Return remaining TTL in seconds (-1 no expiry, -2 key not found)."""
        k = self._key(key)
        return cast(int, self.r.ttl(k))

    def clear_prefix(self) -> None:
        """Delete all keys with current prefix (use carefully)."""
        pattern = f"{self.prefix}*"
        for key in self.r.scan_iter(pattern):
            self.r.delete(key)

def configure_redis(url:str=""):
    if not url:
        raise ValueError("Please Provide Redis url")
    redis_instance = RedisStore(url)
    return redis_instance
