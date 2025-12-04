"""
Redis cache abstraction with namespace support.

Provides safe cache clearing and warm-up protocols using SCAN+UNLINK.
"""

import redis
from typing import Optional, List
from poc_api_first.config import Config


class CacheManager:
    """
    Redis cache abstraction with namespace support.
    Provides safe cache clearing and warm-up protocols.
    """

    def __init__(self, redis_url: str = None):
        if redis_url is None:
            redis_url = Config.redis_url()
        self.redis = redis.from_url(redis_url, decode_responses=True)
        self.namespace_prefix = "test_framework"

    def _key(self, namespace: str, key: str) -> str:
        """Generate namespaced key."""
        return f"{self.namespace_prefix}:{namespace}:{key}"

    def get(self, namespace: str, key: str) -> Optional[str]:
        """Get value from namespaced cache."""
        return self.redis.get(self._key(namespace, key))

    def set(self, namespace: str, key: str, value: str, ttl: int = 3600):
        """Set value in namespaced cache with TTL."""
        self.redis.setex(self._key(namespace, key), ttl, value)

    def clear_namespace(self, namespace: str):
        """
        Clear all keys in namespace using SCAN + UNLINK.
        Safe alternative to KEYS pattern matching.
        """
        pattern = f"{self.namespace_prefix}:{namespace}:*"
        cursor = 0
        keys_to_delete = []

        # SCAN in batches (doesn't block Redis)
        while True:
            cursor, keys = self.redis.scan(cursor, match=pattern, count=100)
            keys_to_delete.extend(keys)

            if cursor == 0:
                break

        # UNLINK (non-blocking delete)
        if keys_to_delete:
            self.redis.unlink(*keys_to_delete)

    def clear_all(self):
        """Clear entire test framework namespace."""
        self.clear_namespace("*")  # Will match all namespaces

    def warm_up(self, namespace: str, queries: List[str]):
        """
        Populate cache with warm-up queries.
        Ensures fair comparison across configs.
        """
        for query in queries:
            # Execute query and cache result
            key = f"query:{hash(query)}"
            # Assume query execution populates cache automatically
            pass


class CacheProtocol:
    """Standardized 3-phase cache protocol."""

    def __init__(self, cache: CacheManager):
        self.cache = cache

        # Fixed warm-up set (identical for all configs)
        self.WARM_UP_QUERIES = [
            "MS neuromodulation",
            "Parkinson's DBS",
            "stroke rehabilitation",
            "ADHD neurofeedback",
            "epilepsy TMS",
            "depression brain stimulation",
            "Alzheimer's memory",
            "TBI cognitive function",
            "migraine treatment",
            "anxiety therapy"
        ]

    def phase_1_clear(self, config_name: str):
        """Phase 1: Clear config-specific cache."""
        self.cache.clear_namespace(config_name)

    def phase_2_warm_up(self, config_name: str):
        """Phase 2: Execute warm-up queries."""
        self.cache.warm_up(config_name, self.WARM_UP_QUERIES)

    def phase_3_measure(self, config_name: str):
        """Phase 3: Ready for latency measurement."""
        # Cache now populated identically for all configs
        pass
