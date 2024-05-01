from __future__ import annotations

import os

import requests
import pytest
import pandas as pd

from ckan.tests.helpers import call_action

import ckanext.charts.fetchers as fetchers
from ckanext.charts.exception import DataFetchError

CSV_DATA = b"col1,col2\n1,2\n3,4\n"


@pytest.mark.ckan_config("ckan.plugins", "datastore")
@pytest.mark.usefixtures("clean_db", "with_plugins")
class TestDatastoreDataFetcher:
    def test_fetch_data_success(self, resource_factory):
        resource = resource_factory()

        result = call_action(
            "datastore_create",
            **{
                "resource_id": resource["id"],
                "fields": [
                    {"id": "name", "type": "text"},
                    {"id": "age", "type": "text"},
                ],
                "records": [
                    {"name": "Sunita", "age": "51"},
                    {"name": "Bowan", "age": "68"},
                ],
                "force": True,
            },
        )

        result = fetchers.DatastoreDataFetcher(resource["id"]).fetch_data()

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert list(result.columns) == ["name", "age"]


@pytest.mark.usefixtures("clean_redis")
class TestURLDataFetcher:
    URL = "http://example.com/data.csv"

    def test_fetch_data_success(self, requests_mock):
        requests_mock.get(self.URL, content=CSV_DATA)

        result = fetchers.URLDataFetcher(self.URL).fetch_data()

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert list(result.columns) == ["col1", "col2"]
        assert list(result["col1"]) == [1, 3]
        assert list(result["col2"]) == [2, 4]

    def test_fetch_data_http_error(self, requests_mock):
        requests_mock.get(self.URL, status_code=404)

        with pytest.raises(DataFetchError):
            fetchers.URLDataFetcher(self.URL).fetch_data()

    def test_fetch_data_connection_error(self, requests_mock):
        requests_mock.get(self.URL, exc=requests.exceptions.ConnectionError)

        with pytest.raises(DataFetchError):
            fetchers.URLDataFetcher(self.URL).fetch_data()

    def test_fetch_data_timeout_error(self, requests_mock):
        requests_mock.get(self.URL, exc=requests.exceptions.Timeout)

        with pytest.raises(DataFetchError):
            fetchers.URLDataFetcher(self.URL).fetch_data()

    def test_hit_cache_redis(self, requests_mock):
        requests_mock.get(self.URL, content=CSV_DATA)

        fetcher = fetchers.URLDataFetcher(self.URL)

        assert fetcher.cache.get_data(fetcher.make_cache_key()) is None

        fetcher.fetch_data()

        assert isinstance(
            fetcher.cache.get_data(fetcher.make_cache_key()), pd.DataFrame
        )

    @pytest.mark.usefixtures("clean_disk_cache")
    def test_hit_cache_disk(self, requests_mock):
        requests_mock.get(self.URL, content=CSV_DATA)

        fetcher = fetchers.URLDataFetcher(self.URL, cache_stragegy="disk")

        assert fetcher.cache.get_data(fetcher.make_cache_key()) is None

        fetcher.fetch_data()

        assert isinstance(
            fetcher.cache.get_data(fetcher.make_cache_key()), pd.DataFrame
        )


class TestHardcodedDataFetcher:
    def test_fetch_data(self):
        fetcher = fetchers.HardcodedDataFetcher(
            {
                "col1": ["1", "2", "3", "4"],
                "col2": ["a", "b", "c", "d"],
                "col3": [42, 37, 69, 11],
            }
        )

        result = fetcher.fetch_data()

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 4
        assert list(result.columns) == ["col1", "col2", "col3"]


@pytest.mark.usefixtures("clean_redis", "clean_disk_cache")
class TestFileSystemDataFetcher:
    def _get_file_path(self, file_name: str) -> str:
        return os.path.join(os.path.dirname(__file__), "data", file_name)

    def test_fetch_data_csv(self):
        fetcher = fetchers.FileSystemDataFetcher(self._get_file_path("sample.csv"))

        result = fetcher.fetch_data()

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 10000

    def test_fetch_data_xml(self):
        fetcher = fetchers.FileSystemDataFetcher(
            self._get_file_path("sample.xml"), file_format="xml"
        )

        result = fetcher.fetch_data()

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 36

    def test_fetch_data_xlsx(self):
        fetcher = fetchers.FileSystemDataFetcher(
            self._get_file_path("sample.xlsx"), file_format="xlsx"
        )

        result = fetcher.fetch_data()

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 100

    def test_fetch_data_xls(self):
        fetcher = fetchers.FileSystemDataFetcher(
            self._get_file_path("sample.xls"), file_format="xls"
        )

        result = fetcher.fetch_data()

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 100

    def test_wrong_file_format(self):
        fetcher = fetchers.FileSystemDataFetcher(
            self._get_file_path("sample.xls"), file_format="xml"
        )

        with pytest.raises(DataFetchError):
            fetcher.fetch_data()

    def test_hit_cache_redis(self):
        fetcher = fetchers.FileSystemDataFetcher(self._get_file_path("sample.csv"))

        assert fetcher.cache.get_data(fetcher.make_cache_key()) is None

        fetcher.fetch_data()

        assert isinstance(
            fetcher.cache.get_data(fetcher.make_cache_key()), pd.DataFrame
        )

    def test_hit_cache_disk(self):
        fetcher = fetchers.FileSystemDataFetcher(
            self._get_file_path("sample.csv"), cache_stragegy="disk"
        )

        assert fetcher.cache.get_data(fetcher.make_cache_key()) is None

        fetcher.fetch_data()

        assert isinstance(
            fetcher.cache.get_data(fetcher.make_cache_key()), pd.DataFrame
        )
