from __future__ import annotations

import pandas as pd
import pytest
import requests

from ckan.tests.factories import Resource

import ckanext.charts.fetchers as fetchers
import ckanext.charts.tests.helpers as helpers
from ckanext.charts.exception import DataFetchError


@pytest.mark.ckan_config("ckan.plugins", "datastore")
@pytest.mark.usefixtures("clean_db", "with_plugins")
class TestDatastoreDataFetcher:
    """Tests for DatastoreDataFetcher"""

    def test_fetch_data_success(self):
        """Test fetching data from the DataStore"""
        resource = helpers.create_resource_with_datastore()

        result = fetchers.DatastoreDataFetcher(resource["id"]).fetch_data()

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert list(result.columns) == ["name", "age"]

    def test_not_in_datastore(self):
        """Test fetching data when resource is not in the DataStore"""
        resource = Resource()

        with pytest.raises(DataFetchError):
            fetchers.DatastoreDataFetcher(resource["id"]).fetch_data()


@pytest.mark.usefixtures("clean_redis")
class TestURLDataFetcher:
    URL = "http://xxx"

    def test_fetch_data_success(self, requests_mock):
        requests_mock.get(self.URL, content=helpers.get_file_content("csv"))

        result = fetchers.URLDataFetcher(self.URL).fetch_data()

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 10000

    def test_fetch_data_success_xml(self, requests_mock):
        requests_mock.get(self.URL, content=helpers.get_file_content("xml"))

        result = fetchers.URLDataFetcher(self.URL, file_format="xml").fetch_data()

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 36

    def test_fetch_data_success_xlsx(self, requests_mock):
        requests_mock.get(self.URL, content=helpers.get_file_content("xlsx"))

        result = fetchers.URLDataFetcher(self.URL, file_format="xlsx").fetch_data()

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 100

    def test_fetch_data_success_xlx(self, requests_mock):
        requests_mock.get(self.URL, content=helpers.get_file_content("xls"))

        result = fetchers.URLDataFetcher(self.URL, file_format="xls").fetch_data()

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 100

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


class TestHardcodedDataFetcher:
    def test_fetch_data(self):
        fetcher = fetchers.HardcodedDataFetcher(
            {
                "col1": ["1", "2", "3", "4"],
                "col2": ["a", "b", "c", "d"],
                "col3": [42, 37, 69, 11],
            },
        )

        result = fetcher.fetch_data()

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 4
        assert list(result.columns) == ["col1", "col2", "col3"]

    def test_malformed_data(self):
        with pytest.raises(DataFetchError):
            fetchers.HardcodedDataFetcher(
                {"col1": ["1"], "col2": ["a", "b"]},
            ).fetch_data()


@pytest.mark.usefixtures("clean_redis", "clean_file_cache")
class TestFileSystemDataFetcher:
    def test_fetch_data_csv(self):
        fetcher = fetchers.FileSystemDataFetcher(helpers.get_file_path("sample.csv"))

        result = fetcher.fetch_data()

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 10000

    def test_fetch_data_xml(self):
        fetcher = fetchers.FileSystemDataFetcher(
            helpers.get_file_path("sample.xml"),
            file_format="xml",
        )

        result = fetcher.fetch_data()

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 36

    def test_fetch_data_xlsx(self):
        fetcher = fetchers.FileSystemDataFetcher(
            helpers.get_file_path("sample.xlsx"),
            file_format="xlsx",
        )

        result = fetcher.fetch_data()

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 100

    def test_fetch_data_xls(self):
        fetcher = fetchers.FileSystemDataFetcher(
            helpers.get_file_path("sample.xls"),
            file_format="xls",
        )

        result = fetcher.fetch_data()

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 100

    def test_wrong_file_format(self):
        fetcher = fetchers.FileSystemDataFetcher(
            helpers.get_file_path("sample.xls"),
            file_format="xml",
        )

        with pytest.raises(DataFetchError):
            fetcher.fetch_data()
