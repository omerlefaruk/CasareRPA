import os
import pickle
from dataclasses import dataclass
from typing import Any, Optional

import lz4.frame
from aiocache import Cache
from diskcache import Cache as DiskCache
from loguru import logger


@dataclass
class CacheConfig:
    enabled: bool = True
    l1_enabled: bool = True
    l2_enabled: bool = True
    l1_ttl: int = 300  # 5 minutes
    l2_ttl: int = 3600  # 1 hour
    disk_path: str = os.path.join(os.environ.get("LOCALAPPDATA", "."), "CasareRPA", "cache")
    compression_threshold: int = 1024  # Compress if > 1KB


class TieredCacheManager:
    """
    Tiered caching system:
    L1: In-memory (aiocache) - Fast, volatile.
    L2: Disk-based (diskcache) - Slower, persistent, compressed.
    """

    def __init__(self, config: CacheConfig | None = None):
        self.config = config or CacheConfig()

        # Initialize L1 (Memory)
        self.l1 = Cache(Cache.MEMORY, ttl=self.config.l1_ttl) if self.config.l1_enabled else None

        # Initialize L2 (Disk)
        self.l2 = None
        if self.config.l2_enabled:
            try:
                os.makedirs(self.config.disk_path, exist_ok=True)
                self.l2 = DiskCache(self.config.disk_path)
            except Exception as e:
                logger.error(f"Failed to initialize DiskCache at {self.config.disk_path}: {e}")
                self.config.l2_enabled = False

    async def get(self, key: str) -> Any | None:
        """Get value from cache (L1 then L2)."""
        if not self.config.enabled:
            return None

        # Try L1
        if self.l1 is not None:
            val = await self.l1.get(key)
            if val is not None:
                return val

        # Try L2
        if self.l2 is not None:
            try:
                raw_data = self.l2.get(key)
                if raw_data is not None:
                    # If it's bytes, it might be compressed/pickled by us
                    if isinstance(raw_data, bytes):
                        data = self._decompress(raw_data)
                    else:
                        data = raw_data

                    # Promote to L1
                    if self.l1 is not None:
                        await self.l1.set(key, data)
                    return data
            except Exception as e:
                logger.error(f"Error reading from L2 cache for key {key}: {e}")

        return None

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set value in cache (L1 and L2)."""
        if not self.config.enabled:
            return

        # Set L1
        if self.l1 is not None:
            await self.l1.set(key, value, ttl=ttl or self.config.l1_ttl)

        # Set L2
        if self.l2 is not None:
            try:
                # We compress/pickle ourselves to have full control over the format
                # and to support LZ4 compression for large objects.
                compressed_data = self._compress(value)
                self.l2.set(key, compressed_data, expire=ttl or self.config.l2_ttl)
            except Exception as e:
                logger.error(f"Error writing to L2 cache for key {key}: {e}")

    async def delete(self, key: str) -> None:
        """Delete value from all cache tiers."""
        if self.l1 is not None:
            await self.l1.delete(key)
        if self.l2 is not None:
            self.l2.delete(key)

    async def delete_by_prefix(self, prefix: str) -> None:
        """Delete all keys starting with prefix from all cache tiers."""
        if self.l1 is not None:
            # aiocache.Cache.MEMORY is a dict internally in aiocache 0.12+
            # We access the internal storage to filter keys
            try:
                keys_to_delete = [
                    k for k in self.l1._cache if isinstance(k, str) and k.startswith(prefix)
                ]
                for k in keys_to_delete:
                    await self.l1.delete(k)
            except Exception as e:
                logger.warning(f"Failed to delete by prefix in L1: {e}")

        if self.l2 is not None:
            try:
                keys_to_delete = [k for k in self.l2 if isinstance(k, str) and k.startswith(prefix)]
                for k in keys_to_delete:
                    self.l2.delete(k)
            except Exception as e:
                logger.warning(f"Failed to delete by prefix in L2: {e}")

    async def clear(self) -> None:
        """Clear all cache tiers."""
        if self.l1 is not None:
            await self.l1.clear()
        if self.l2 is not None:
            self.l2.clear()

    def _compress(self, value: Any) -> bytes:
        """Pickle and optionally compress data."""
        data = pickle.dumps(value)
        if len(data) > self.config.compression_threshold:
            return lz4.frame.compress(data)
        return data

    def _decompress(self, data: bytes) -> Any:
        """Decompress and unpickle data."""
        try:
            # LZ4 frame starts with a specific magic number
            # We try decompressing; if it fails, it's likely raw pickle
            try:
                decompressed = lz4.frame.decompress(data)
                return pickle.loads(decompressed)
            except Exception:
                return pickle.loads(data)
        except Exception as e:
            logger.error(f"Decompression/Unpickling failed: {e}")
            return None
