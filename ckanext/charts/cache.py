from __future__ import annotations

import time
import hashlib
import logging
import os
import tempfile
from abc import ABC, abstractmethod

import pandas as pd
import pyarrow as pa
import pyarrow.orc as orc

import ckan.plugins.toolkit as tk
from ckan.lib.redis import connect_to_redis

import ckanext.charts.exception as exception
import ckanext.charts.config as config
import ckanext.charts.const as const


log = logging.getLogger(__name__)


class CacheStrategy(ABC):
    """Cache strategy interface"""

    @abstractmethod
    def get_data(self, key: str) -> pd.DataFrame | None:
        pass

    @abstractmethod
    def set_data(self, key: str, data: pd.DataFrame):
        pass

    @abstractmethod
    def invalidate(self, key: str) -> None:
        pass


class RedisCache(CacheStrategy):
    """Cache data to Redis"""

    def __init__(self):
        self.client = connect_to_redis()

    def get_data(self, key: str) -> pd.DataFrame | None:
        """Return data from cache if exists"""
        raw_data = self.client.get(key)

        if not raw_data:
            return None

        return pa.deserialize_pandas(raw_data)

    def set_data(self, key: str, data: pd.DataFrame):
        """Serialize data and save to redis"""
        cache_ttl = config.get_redis_cache_ttl()

        if cache_ttl:
            self.client.setex(key, cache_ttl, pa.serialize_pandas(data).to_pybytes())
        else:
            self.client.set(key, value=pa.serialize_pandas(data).to_pybytes())

    def invalidate(self, key: str):
        self.client.delete(key)


class FileCache(CacheStrategy):
    """Cache data as file"""

    def __init__(self):
        self.directory = get_file_cache_path()

    def get_data(self, key: str) -> pd.DataFrame | None:
        """Return data from cache if exists"""

        file_path = self.make_file_path_from_key(key)

        if os.path.exists(file_path):
            if self.is_file_cache_expired(file_path):
                return None

            with open(file_path, "rb") as f:
                return orc.ORCFile(f).read().to_pandas()

        return None

    def set_data(self, key: str, data: pd.DataFrame) -> None:
        """Save data to cache. The data will be stored as an ORC file."""
        file_path = self.make_file_path_from_key(key)

        data.to_orc(file_path)

    def invalidate(self, key: str) -> None:
        """Remove data from cache"""
        file_path = self.make_file_path_from_key(key)

        if os.path.exists(file_path):
            os.remove(file_path)

    def make_file_path_from_key(self, key: str) -> str:
        return os.path.join(
            self.directory, f"{self.generate_unique_consistent_filename(key)}.orc"
        )

    def generate_unique_consistent_filename(self, key: str) -> str:
        """Generate unique and consistent filename based on the key"""
        hash_object = hashlib.sha256()
        hash_object.update(key.encode("utf-8"))
        return hash_object.hexdigest()

    @staticmethod
    def is_file_cache_expired(file_path: str) -> bool:
        """Check if file cache is expired. If TTL is 0 then cache never expires."""
        file_ttl = config.get_file_cache_ttl()

        if not file_ttl:
            return False

        return time.time() - os.path.getmtime(file_path) > file_ttl


def get_cache_manager(cache_strategy: str | None) -> CacheStrategy:
    """Return cache manager based on the strategy"""
    active_cache = cache_strategy or config.get_cache_strategy()

    if active_cache == const.CACHE_REDIS:
        return RedisCache()
    elif active_cache == const.CACHE_FILE:
        return FileCache()

    raise exception.CacheStrategyNotImplemented(
        f"Cache strategy {active_cache} is not implemented"
    )


def invalidate_all_cache() -> None:
    """Invalidate all caches"""
    drop_file_cache()
    drop_redis_cache()

    log.info("All chart caches have been invalidated")


def invalidate_by_key(key: str) -> None:
    """Invalidate cache by key"""
    RedisCache().invalidate(key)
    FileCache().invalidate(key)

    log.info(f"Chart cache for key {key} has been invalidated")


def drop_redis_cache() -> None:
    """Drop all ckanext-charts keys from Redis cache"""
    conn = connect_to_redis()

    log.info("Dropping all ckanext-charts keys from Redis cache")

    for key in conn.scan_iter(const.REDIS_PREFIX):
        conn.delete(key)


def drop_file_cache() -> None:
    """Drop all cached files from storage"""

    log.info("Dropping all charts cached files")

    folder_path = get_file_cache_path()

    for filename in os.listdir(get_file_cache_path()):
        file_path = os.path.join(folder_path, filename)

        try:
            os.unlink(file_path)
        except Exception as e:
            log.error("Failed to delete %s. Reason: %s" % (file_path, e))


def get_file_cache_path() -> str:
    """Return path to the file cache folder"""
    storage_path: str = tk.config["ckan.storage_path"] or tempfile.gettempdir()

    cache_path = os.path.join(storage_path, "charts_cache")

    os.makedirs(cache_path, exist_ok=True)

    return cache_path


def update_redis_expiration(time: int) -> None:
    """Update TTL for existing Redis keys"""
    if not time:
        return

    redis_conn = RedisCache().client

    for key in redis_conn.scan_iter(const.REDIS_PREFIX):
        redis_conn.expire(name=key, time=time, lt=True)


def count_redis_cache_size() -> int:
    """Return the size of the Redis cache"""
    redis_conn = RedisCache().client

    total_size = 0

    for key in redis_conn.scan_iter(const.REDIS_PREFIX):
        size = redis_conn.memory_usage(key)

        if not size or not isinstance(size, int):
            continue

        total_size += size

    return total_size


def count_file_cache_size() -> int:
    """Return the size of the file cache"""
    return sum(
        os.path.getsize(os.path.join(get_file_cache_path(), f))
        for f in os.listdir(get_file_cache_path())
    )


def remove_expired_file_cache() -> None:
    """Remove expired files from the file cache"""
    for filename in os.listdir(get_file_cache_path()):
        file_path = os.path.join(get_file_cache_path(), filename)

        if FileCache.is_file_cache_expired(file_path):
            os.unlink(file_path)

    log.info("Expired files have been removed from the file cache")
