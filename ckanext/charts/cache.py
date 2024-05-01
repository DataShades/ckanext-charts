from __future__ import annotations

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
from ckanext.charts.config import get_cache_strategy
import ckanext.charts.utils as utils


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
        raw_data = self.client.get(key)

        if not raw_data:
            return None

        return pa.deserialize_pandas(raw_data)

    def set_data(self, key: str, data: pd.DataFrame):
        self.client.set(key, pa.serialize_pandas(data).to_pybytes())

    def invalidate(self, key: str):
        self.client.delete(key)


class DiskCache(CacheStrategy):
    """Cache data to disk"""

    def __init__(self):
        self.directory = get_disk_cache_path()

    def get_data(self, key: str) -> pd.DataFrame | None:
        file_path = os.path.join(
            self.directory, f"{self.generate_unique_consistent_filename(key)}.orc"
        )

        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                return orc.ORCFile(f).read().to_pandas()

        return None

    def path_to_key(self, path: str) -> str:
        """Convert a path to unique key"""
        return path.replace("/", "_")

    def set_data(self, key: str, data: pd.DataFrame):
        file_path = os.path.join(
            self.directory, f"{self.generate_unique_consistent_filename(key)}.orc"
        )

        data.to_orc(file_path)

        # table = pa.Table.from_pandas(data)

        # with open(file_path, "wb") as f:
        #     orc.write_table(table, f)

    def invalidate(self, key: str):
        file_path = os.path.join(
            self.directory, f"{self.generate_unique_consistent_filename(key)}.orc"
        )

        if os.path.exists(file_path):
            os.remove(file_path)

    def generate_unique_consistent_filename(self, key: str) -> str:
        hash_object = hashlib.sha256()
        hash_object.update(key.encode("utf-8"))
        return hash_object.hexdigest()


def get_cache_manager(cache_stragegy: str | None) -> CacheStrategy:
    """Return cache manager based on the strategy"""
    active_cache = cache_stragegy or get_cache_strategy()

    if active_cache == "redis":
        return RedisCache()
    elif active_cache == "disk":
        return DiskCache()

    raise exception.CacheStrategyNotImplemented(
        f"Cache strategy {active_cache} is not implemented"
    )


def invalidate_cache() -> None:
    """Invalidate all caches"""
    drop_disk_cache()
    drop_redis_cache()


def drop_redis_cache():
    """Drop all ckanext-charts keys from Redis cache"""
    conn = connect_to_redis()

    for key in conn.scan_iter("ckanext-charts:"):
        conn.delete(key)


def drop_disk_cache():
    """Drop all cached files from storage"""

    folder_path = get_disk_cache_path()

    for filename in os.listdir(get_disk_cache_path()):
        file_path = os.path.join(folder_path, filename)

        try:
            os.unlink(file_path)
        except Exception as e:
            log.error("Failed to delete %s. Reason: %s" % (file_path, e))


def get_disk_cache_path() -> str:
    """Return path to the disk cache folder"""
    storage_path: str = tk.config["ckan.storage_path"] or tempfile.gettempdir()

    cache_path = os.path.join(storage_path, "charts_cache")

    os.makedirs(cache_path, exist_ok=True)

    return cache_path
