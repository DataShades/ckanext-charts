from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd
import pytest
from freezegun import freeze_time

from ckan.tests.helpers import call_action

from ckanext.charts import cache
from ckanext.charts import config
from ckanext.charts import const
from ckanext.charts import fetchers
from ckanext.charts.tests import helpers


# @pytest.mark.ckan_config("ckan.plugins", "charts_view datastore")
# @pytest.mark.usefixtures("clean_db", "with_plugins")
# class TestDataStoreFetcherCache:
#     def test_hit_cache_redis(self):
#         """Test fetch cached data from redis cache"""
#         resource = helpers.create_resource_with_datastore()

#         fetcher = fetchers.DatastoreDataFetcher(resource["id"])

#         assert fetcher.get_cached_data() is None

#         fetcher.fetch_data()

#         assert isinstance(fetcher.get_cached_data(), pd.DataFrame)

#     def test_invalidate_redis_cache_on_resource_delete(self):
#         """Test that the cache is invalidated when the resource is deleted"""
#         resource = helpers.create_resource_with_datastore()

#         fetcher = fetchers.DatastoreDataFetcher(resource["id"])

#         result = fetcher.fetch_data()

#         assert isinstance(result, pd.DataFrame)

#         call_action("resource_delete", id=resource["id"])

#         assert fetcher.get_cached_data() is None

#     @pytest.mark.usefixtures("clean_file_cache")
#     def test_hit_cache_file(self):
#         """Test fetch cached data from file cache"""
#         resource = helpers.create_resource_with_datastore()

#         fetcher = fetchers.DatastoreDataFetcher(
#             resource["id"],
#             cache_strategy=const.CACHE_FILE_ORC,
#         )

#         assert fetcher.get_cached_data() is None

#         fetcher.fetch_data()

#         assert isinstance(fetcher.get_cached_data(), pd.DataFrame)

#     def test_invalidate_file_cache_on_resource_delete(self):
#         """Test that the cache is invalidated when the resource is deleted"""
#         resource = helpers.create_resource_with_datastore()

#         fetcher = fetchers.DatastoreDataFetcher(
#             resource["id"],
#             cache_strategy=const.CACHE_FILE_ORC,
#         )

#         result = fetcher.fetch_data()

#         assert isinstance(result, pd.DataFrame)

#         call_action("resource_delete", id=resource["id"])

#         assert fetcher.get_cached_data() is None

#     def test_invalidate_redis_cache(self):
#         resource = helpers.create_resource_with_datastore()

#         fetcher = fetchers.DatastoreDataFetcher(resource["id"])

#         assert isinstance(fetcher.fetch_data(), pd.DataFrame)

#         fetcher.invalidate_cache()

#         assert fetcher.get_cached_data() is None

#     def test_invalidate_file_cache(self):
#         resource = helpers.create_resource_with_datastore()

#         fetcher = fetchers.DatastoreDataFetcher(
#             resource["id"],
#             cache_strategy=const.CACHE_FILE_ORC,
#         )

#         assert isinstance(fetcher.fetch_data(), pd.DataFrame)

#         fetcher.invalidate_cache()

#         assert fetcher.get_cached_data() is None


@pytest.mark.usefixtures("clean_redis", "clean_file_cache")
class TestUrlFetcherCache:
    URL = "http://xxx"

    def test_hit_cache_redis(self, requests_mock):
        requests_mock.get(self.URL, content=helpers.get_file_content("csv"))

        fetcher = fetchers.URLDataFetcher(self.URL)

        assert fetcher.get_cached_data() is None

        fetcher.fetch_data()

        assert isinstance(fetcher.get_cached_data(), pd.DataFrame)

    @pytest.mark.usefixtures("clean_file_cache")
    def test_hit_cache_file(self, requests_mock):
        requests_mock.get(self.URL, content=helpers.get_file_content("csv"))

        fetcher = fetchers.URLDataFetcher(self.URL, cache_strategy=const.CACHE_FILE_ORC)

        assert fetcher.get_cached_data() is None

        fetcher.fetch_data()

        assert isinstance(fetcher.get_cached_data(), pd.DataFrame)

    def test_invalidate_redis_cache(self, requests_mock):
        requests_mock.get(self.URL, content=helpers.get_file_content("csv"))

        fetcher = fetchers.URLDataFetcher(self.URL)

        assert isinstance(fetcher.fetch_data(), pd.DataFrame)

        fetcher.invalidate_cache()

        assert fetcher.get_cached_data() is None

    def test_invalidate_file_cache(self, requests_mock):
        requests_mock.get(self.URL, content=helpers.get_file_content("csv"))

        fetcher = fetchers.URLDataFetcher(self.URL, cache_strategy=const.CACHE_FILE_ORC)

        assert isinstance(fetcher.fetch_data(), pd.DataFrame)

        fetcher.invalidate_cache()

        assert fetcher.get_cached_data() is None


@pytest.mark.usefixtures("clean_redis", "clean_file_cache")
class TestFileSystemFetcherCache:
    def test_hit_cache_redis(self):
        fetcher = fetchers.FileSystemDataFetcher(helpers.get_file_path("sample.csv"))

        assert fetcher.get_cached_data() is None

        fetcher.fetch_data()

        assert isinstance(fetcher.get_cached_data(), pd.DataFrame)

    def test_hit_cache_file(self):
        fetcher = fetchers.FileSystemDataFetcher(
            helpers.get_file_path("sample.csv"),
            cache_strategy=const.CACHE_FILE_ORC,
        )

        assert fetcher.get_cached_data() is None

        fetcher.fetch_data()

        assert isinstance(fetcher.get_cached_data(), pd.DataFrame)

    def test_invalidate_redis_cache(self):
        fetcher = fetchers.FileSystemDataFetcher(helpers.get_file_path("sample.csv"))

        assert isinstance(fetcher.fetch_data(), pd.DataFrame)

        fetcher.invalidate_cache()

        assert fetcher.get_cached_data() is None

    def test_invalidate_file_cache(self):
        fetcher = fetchers.FileSystemDataFetcher(
            helpers.get_file_path("sample.csv"),
            cache_strategy=const.CACHE_FILE_ORC,
        )

        assert isinstance(fetcher.fetch_data(), pd.DataFrame)

        fetcher.invalidate_cache()

        assert fetcher.get_cached_data() is None


@pytest.mark.usefixtures("clean_file_cache")
@pytest.mark.ckan_config(config.CONF_FILE_CACHE_TTL, 100)
class TestCalculateFileORCExpiration:
    def test_file_is_expired(self):
        fetcher = fetchers.FileSystemDataFetcher(
            helpers.get_file_path("sample.csv"),
            cache_strategy=const.CACHE_FILE_ORC,
        )

        assert fetcher.get_cached_data() is None

        fetcher.fetch_data()

        assert isinstance(fetcher.get_cached_data(), pd.DataFrame)

        file_path = cache.FileCacheORC().make_file_path_from_key(
            fetcher.make_cache_key(),
        )

        with freeze_time(datetime.now() + timedelta(seconds=101)):
            assert cache.FileCacheORC().is_file_cache_expired(file_path)

    def test_file_is_not_expired(self):
        fetcher = fetchers.FileSystemDataFetcher(
            helpers.get_file_path("sample.csv"),
            cache_strategy=const.CACHE_FILE_ORC,
        )

        assert fetcher.get_cached_data() is None

        fetcher.fetch_data()

        assert isinstance(fetcher.get_cached_data(), pd.DataFrame)

        file_path = cache.FileCacheORC().make_file_path_from_key(
            fetcher.make_cache_key(),
        )

        assert not cache.FileCacheORC().is_file_cache_expired(file_path)
