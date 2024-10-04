from typing import Dict, Any
from functools import lru_cache

class Cache:
    def __init__(self, maxsize=100):
        self.cache = lru_cache(maxsize=maxsize)(self._cache_func)

    def _cache_func(self, user_id: str, code_context: str) -> Any:
        # This function is never actually called, it's just used for the lru_cache decorator
        pass

    def get(self, user_id: str, code_context: str) -> Any:
        return self.cache(user_id, code_context)

    def set(self, user_id: str, code_context: str, value: Any):
        # Clear the cache for this user and code context
        self.cache.cache_clear()
        # Set the new value
        self.cache(user_id, code_context)
        return value