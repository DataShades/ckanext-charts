from __future__ import annotations

import hashlib
import logging
import os
import tempfile
import time
from abc import ABC, abstractmethod
from io import BytesIO
from typing import IO

import pandas as pd
from redis.exceptions import ResponseError

import ckan.plugins.toolkit as tk
from ckan.lib.redis import connect_to_redis

from ckanext.charts import config, const, exception

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

        return pd.read_csv(BytesIO(raw_data))  # type: ignore

    def set_data(self, key: str, data: pd.DataFrame):
        """Serialize data and save to redis"""
        cache_ttl = config.get_redis_cache_ttl()

        try:
            if cache_ttl:
                self.client.setex(key, cache_ttl, data.to_csv(index=False))
            else:
                self.client.set(key, value=data.to_csv(index=False))
        except Exception:
            log.exception("Failed to save data to Redis")

    def invalidate(self, key: str):
        self.client.delete(key)


class FileCache(CacheStrategy):
    """Cache data as file"""

    FILE_FORMAT = ""

    def __init__(self):
        self.directory = get_file_cache_path()

    def get_data(self, key: str) -> pd.DataFrame | None:
        """Return data from cache if exists"""

        file_path = self.make_file_path_from_key(key)

        if os.path.exists(file_path):
            if self.is_file_cache_expired(file_path):
                return None

            with open(file_path, "rb") as f:
                return self.read_data(f)

        return None

    @abstractmethod
    def read_data(self, file: IO) -> pd.DataFrame | None:
        pass

    def set_data(self, key: str, data: pd.DataFrame) -> None:
        """Save data to cache. The data will be stored as an ORC file."""
        file_path = self.make_file_path_from_key(key)

        self.write_data(file_path, data)

    @abstractmethod
    def write_data(self, file_path: str, data: pd.DataFrame) -> None:
        pass

    def invalidate(self, key: str) -> None:
        """Remove data from cache"""
        file_path = self.make_file_path_from_key(key)

        if os.path.exists(file_path):
            os.remove(file_path)

    def make_file_path_from_key(self, key: str) -> str:
        return os.path.join(
            self.directory,
            f"{self.generate_unique_consistent_filename(key)}.{self.FILE_FORMAT}",
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


class FileCacheORC(FileCache):
    """Cache data as ORC file"""

    FILE_FORMAT = "orc"

    def read_data(self, file: IO) -> pd.DataFrame | None:
        from pyarrow import orc

        return orc.ORCFile(file).read().to_pandas()

    def write_data(self, file_path: str, data: pd.DataFrame) -> None:
        for col in data.select_dtypes(include=["object"]).columns:
            data[col] = data[col].astype(str)

        data.to_orc(file_path)


class FileCacheCSV(FileCache):
    """Cache data as CSV file"""

    FILE_FORMAT = "csv"

    def read_data(self, file: IO) -> pd.DataFrame | None:
        return pd.read_csv(file)

    def write_data(self, file_path: str, data: pd.DataFrame) -> None:
        data.to_csv(file_path, index=False)


def get_cache_manager(cache_strategy: str | None) -> CacheStrategy:
    """Return cache manager based on the strategy"""
    active_cache = cache_strategy or config.get_cache_strategy()

    if active_cache == const.CACHE_REDIS:
        return RedisCache()

    if active_cache == const.CACHE_FILE_ORC:
        return FileCacheORC()

    if active_cache == const.CACHE_FILE_CSV:
        return FileCacheCSV()

    raise exception.CacheStrategyNotImplementedError(
        f"Cache strategy {active_cache} is not implemented",
    )


def invalidate_all_cache() -> None:
    """Invalidate all caches"""
    drop_file_cache()
    drop_redis_cache()

    log.info("All chart caches have been invalidated")


def invalidate_by_key(key: str) -> None:
    """Invalidate cache by key"""
    RedisCache().invalidate(key)
    FileCacheORC().invalidate(key)
    FileCacheCSV().invalidate(key)

    log.info("Chart cache for key %s has been invalidated", key)


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
        except Exception:
            log.exception("Failed to delete file: %s", file_path)


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
        try:
            redis_conn.expire(name=key, time=time, lt=True)
        except (TypeError, ResponseError):
            redis_conn.expire(name=key, time=time)


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
