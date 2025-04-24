from __future__ import annotations

import hashlib
import json
import logging
import os
import pickle
import tempfile
import time
from abc import ABC, abstractmethod
from typing import IO, Any, cast

import pandas as pd

import ckan.plugins.toolkit as tk
from ckan.lib.redis import connect_to_redis

from ckanext.charts import config, const, exception, types, fetchers, utils

log = logging.getLogger(__name__)


class CacheStrategy(ABC):
    """Cache strategy interface.

    Defines the abstracts methods for cache strategies.
    """

    @abstractmethod
    def get_data(self, key: str) -> types.ChartData | None:
        """Return data and settings from cache if exists.

        Args:
            key: The cache  key to retrieve the data.

        Returns:
            ChartData or None if not found.
        """

    @abstractmethod
    def set_data(
        self,
        key: str,
        data: types.ChartData,
    ):
        """Store data and settings to cache.

        Args:
            key: The cache key to store the data.
            data: The ChartData to be stored.
        """

    @abstractmethod
    def invalidate(self, key: str) -> None:
        """Invalidate cache by key.

        Args:
            key: The cache key to invalidate.
        """


class RedisCache(CacheStrategy):
    """Cache data to Redis as a CSV string"""

    def __init__(self):
        self.client = connect_to_redis()

    def get_data(self, key: str) -> types.ChartData | None:
        """Return data, settings from cache if exists.

        Args:
            key: The cache key to retrieve the data.

        Returns:
            ChartData or None if not found.
        """
        raw_data = self.client.get(key)  # type: ignore

        if not raw_data:
            return None

        if not isinstance(raw_data, (bytes, bytearray, memoryview)):
            raise TypeError(f"Expected bytes-like object, got {type(raw_data)}")

        return pickle.loads(raw_data)

    def set_data(
        self,
        key: str,
        data: types.ChartData,
    ) -> None:
        """Serialize and store DataFrame, settings, and column names in Redis.

        Args:
            key: The cache key to store the data.
            data: The ChartData to be stored.

        Raises:
            Exception: If failed to save data to Redis.
        """

        cache_ttl = config.get_redis_cache_ttl()
        payload = pickle.dumps(data)

        try:
            self.client.setex(key, cache_ttl, payload)
        except Exception:
            log.exception("Failed to save data to Redis")

    def invalidate(self, key: str):
        """Remove data from cache.

        Args:
            key: The cache key to invalidate.
        """
        self.client.delete(key)


class FileCache(CacheStrategy):
    """Cache data and settings as separate files.

    We store the cached files in a separate folder in the CKAN storage.
    """

    FILE_FORMAT = ""

    def __init__(self):
        self.directory = get_file_cache_path()

    def get_data(self, key: str) -> types.ChartData | None:
        """Return data and settings from cache if exists.

        Args:
            key: The cache key to retrieve the data.

        Returns:
            ChartData or None if not found.
        """

        file_path = self.make_file_path_from_key(key)

        if os.path.exists(file_path):
            if self.is_file_cache_expired(file_path):
                return None

            with open(file_path, "rb") as f:
                return self.read_data(f, file_path)

        return None

    @abstractmethod
    def read_data(
        self,
        file: IO[bytes],
        file_path: str,
    ) -> types.ChartData | None:
        """Read cached data and settings from a file object.

        Args:
            file: The file object to read the data.

        Returns:
            ChartData or None if not found.
        """

    def set_data(
        self,
        key: str,
        data: types.ChartData,
    ) -> None:
        """Store data and settings to cache.

        Args:
            key: The cache key to store the data.
            data: The ChartData to be stored.
        """
        file_path = self.make_file_path_from_key(key)

        self.write_data(file_path, data)

    @abstractmethod
    def write_data(
        self,
        file_path: str,
        data: types.ChartData,
    ) -> None:
        """Defines how to write data and settings to a file.

        Args:
            file_path: The path to the file.
            data: The ChartData to be stored.
        """

    def invalidate(self, key: str) -> None:
        """Remove data from cache.

        Args:
            key: The cache key to invalidate.
        """
        file_path = self.make_file_path_from_key(key)
        meta_path = self.get_meta_path(file_path)

        if os.path.exists(file_path):
            os.remove(file_path)

        if os.path.exists(meta_path):
            os.remove(meta_path)

    def make_file_path_from_key(self, key: str) -> str:
        """Generate file path based on the key

        Args:
            key: The cache key to generate the file path.

        Returns:
            The file path.
        """
        return os.path.join(
            self.directory,
            f"{self.generate_unique_consistent_filename(key)}.{self.FILE_FORMAT}",
        )

    def generate_unique_consistent_filename(self, key: str) -> str:
        """Generate unique and consistent filename based on the key.

        Args:
            key: The cache key to generate the filename.

        Returns:
            The filename.
        """
        hash_object = hashlib.sha256()
        hash_object.update(key.encode("utf-8"))
        return hash_object.hexdigest()

    @staticmethod
    def is_file_cache_expired(file_path: str) -> bool:
        """Check if file cache is expired.

        Args:
            file_path: The path to the file.

        Returns:
            True if file cache is expired, otherwise False.
        """
        file_ttl = config.get_file_cache_ttl()

        return time.time() - os.path.getmtime(file_path) > file_ttl

    def get_meta_path(self, file_path: str) -> str:
        """Return the metadata file path for a given file.

        Args:
            file_path: The original file path.

        Returns:
            The corresponding .meta file path.
        """
        return file_path + ".meta"

    def write_metadata(self, file_path: str, data: types.ChartData):
        """Write metadata to a .meta file if settings and columns are provided.

        Args:
            file_path: The original file path.
            data: The metadata to store.
        """
        metadata = {
            "settings": data.settings,
            "columns": data.columns,
        }

        with open(self.get_meta_path(file_path), "w", encoding="utf-8") as f:
            json.dump(metadata, f)

    def read_metadata(self, file_path: str) -> dict[str, Any]:
        """Read metadata from a .meta file if it exists.

        Args:
            file_path: The original file path.

        Returns:
            The metadata if it exists, otherwise None.
        """
        meta_path = self.get_meta_path(file_path)
        if not os.path.exists(meta_path):
            return {"settings": {}, "columns": []}

        with open(meta_path, encoding="utf-8") as f:
            return json.load(f)


class FileCacheORC(FileCache):
    """Cache data as ORC file"""

    FILE_FORMAT = "orc"

    def read_data(
        self,
        file: IO[bytes],
        file_path: str,
    ) -> types.ChartData | None:
        """Read cached data from an ORC file and settings from .meta file.

        Args:
            file: The file object to read the data.

        Returns:
            ChartData or None if not found.
        """
        from pyarrow import orc

        df = cast(pd.DataFrame, orc.ORCFile(file).read().to_pandas())
        metadata = self.read_metadata(file_path)
        return types.ChartData(
            df=df,
            settings=metadata["settings"],
            columns=metadata["columns"],
        )

    def write_data(
        self,
        file_path: str,
        data: types.ChartData,
    ) -> None:
        """Write data to an ORC file and store settings in a separate .meta file.

        Args:
            file_path: The path to the file.
            data: The ChartData to be stored.
        """
        df = data.df
        if not df.empty:
            for col in df.select_dtypes(include=["object"]).columns:
                df[col] = df[col].astype(str)

            df.to_orc(file_path)

        self.write_metadata(file_path, data)


class FileCacheCSV(FileCache):
    """Cache data as CSV file"""

    FILE_FORMAT = "csv"

    def read_data(
        self,
        file: IO[bytes],
        file_path: str,
    ) -> types.ChartData | None:
        """Read cached data from a CSV file and settings from .meta file.

        Args:
            file: The file object.
            file_path: The original file path.

        Returns:
            ChartData or None if not found.
        """
        df = pd.read_csv(file)
        metadata = self.read_metadata(file_path)
        return types.ChartData(
            df=df,
            settings=metadata["settings"],
            columns=metadata["columns"],
        )

    def write_data(
        self,
        file_path: str,
        data: types.ChartData,
    ) -> None:
        """Write data to a CSV file and optionally write settings metadata.

        Args:
            file_path: The path to the file.
            data: The ChartData to be stored.
        """
        if not data.df.empty:
            data.df.to_csv(file_path, index=False)

        self.write_metadata(file_path, data)


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

    for key in conn.scan_iter(const.REDIS_PREFIX, count=1000):  # type: ignore
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


def count_redis_cache_size() -> int:
    """Return the size of the Redis cache"""
    redis_conn = RedisCache().client

    total_size = 0

    for key in redis_conn.scan_iter(const.REDIS_PREFIX, count=1000):  # type: ignore
        size: Any = redis_conn.memory_usage(key)

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


def invalidate_resource_cache(resource_id: str):
    """Invalidate all chart-related caches (data and metadata) for a given resource."""
    fetcher = fetchers.DatastoreDataFetcher(resource_id)

    # Invalidate columns
    invalidate_by_key(fetcher.make_metadata_cache_key())

    # Invalidate main cache key (used before view_id is known)
    invalidate_by_key(fetcher.make_cache_key())

    # Invalidate all view-specific cache keys
    for view_id in utils.get_chart_view_ids(resource_id):
        invalidate_by_key(
            fetchers.DatastoreDataFetcher(resource_id, view_id).make_cache_key(),
        )
