from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from io import BytesIO
from typing import Any

import lxml
import requests
import pandas as pd
import sqlalchemy as sa

from ckanext.datastore.backend.postgres import get_read_engine

import ckanext.charts.exception as exception
import ckanext.charts.cache as cache

log = logging.getLogger(__name__)


class DataFetcherStrategy(ABC):
    def __init__(self, cache_stragegy: str | None = None) -> None:
        self.cache = cache.get_cache_manager(cache_stragegy)

    @abstractmethod
    def fetch_data(self) -> pd.DataFrame:
        pass

    @abstractmethod
    def make_cache_key(self) -> str:
        pass

    def invalidate_cache(self):
        self.cache.invalidate(self.make_cache_key())


class DatastoreDataFetcher(DataFetcherStrategy):
    """Fetch data from the DataStore"""

    def __init__(
        self, resource_id: str, limit: int = 2000000, cache_stragegy: str | None = None
    ):
        super().__init__(cache_stragegy=cache_stragegy)

        self.resource_id = resource_id
        self.limit = limit

    def fetch_data(self) -> pd.DataFrame:
        """We are working with resources, that are stored with DataStore in
        a separate table.

        Returns:
            pd.DataFrame: Data from the DataStore
        """
        cached_df = self.cache.get_data(self.make_cache_key())

        if cached_df is not None:
            return cached_df

        df = pd.read_sql_query(
            sa.select(sa.text("*"))  # type: ignore
            .select_from(sa.table(self.resource_id))
            .limit(self.limit),
            get_read_engine(),
        ).drop(columns=["_id", "_full_text"])

        self.cache.set_data(self.make_cache_key(), df)

        return df

    def make_cache_key(self) -> str:
        return f"ckanext-charts:datastore:{self.resource_id}"


class URLDataFetcher(DataFetcherStrategy):
    SUPPORTED_FORMATS = ["csv", "xlsx", "xls", "xml"]

    def __init__(
        self,
        url: str,
        file_format: str = "csv",
        timeout: int = 0,
        cache_stragegy: str | None = None,
    ):
        super().__init__(cache_stragegy=cache_stragegy)

        self.url = url
        self.file_format = file_format
        self.timeout = timeout

    def fetch_data(self) -> pd.DataFrame:
        cached_df = self.cache.get_data(self.make_cache_key())

        if cached_df is not None:
            return cached_df

        data = self.make_request()

        try:
            if self.file_format in ("xlsx", "xls"):
                df = pd.read_excel(BytesIO(data))
            elif self.file_format == "xml":
                df = pd.read_xml(BytesIO(data))
            else:
                df = pd.read_csv(BytesIO(data))
        except (
            pd.errors.ParserError,
            lxml.etree.XMLSyntaxError,
            UnicodeDecodeError,
            ValueError,
        ) as e:
            raise exception.DataFetchError(
                f"An error occurred during fetching data from URL: {e}"
            )

        self.cache.set_data(self.make_cache_key(), df)

        return df

    def make_cache_key(self) -> str:
        return f"ckanext-charts:url:{self.url}"

    def make_request(self) -> bytes:
        """Make a request to the URL and return the response text"""
        try:
            response = requests.get(self.url)
            response.raise_for_status()
            return response.content
        except requests.exceptions.HTTPError as e:
            log.error(f"HTTP error occurred: {e}")
        except requests.exceptions.ConnectionError as e:
            log.error(f"Connection error occurred: {e}")
        except requests.exceptions.Timeout as e:
            log.error(f"Timeout error occurred: {e}")
        except requests.exceptions.RequestException as e:
            log.error(f"An error occurred during the request: {e}")
        except Exception as e:
            log.error(f"An unexpected error occurred: {e}")

        raise exception.DataFetchError(
            f"An error occurred during fetching data by URL: {self.url}"
        )


class FileSystemDataFetcher(DataFetcherStrategy):
    SUPPORTED_FORMATS = ["csv", "xlsx", "xls", "xml"]

    def __init__(
        self,
        file_path: str,
        file_format: str = "csv",
        cache_stragegy: str | None = None,
    ):
        super().__init__(cache_stragegy=cache_stragegy)

        self.file_path = file_path
        self.file_format = file_format

    def fetch_data(self) -> pd.DataFrame:
        """Fetch data from the file system"""

        cached_df = self.cache.get_data(self.make_cache_key())

        if cached_df is not None:
            return cached_df

        if self.file_format not in self.SUPPORTED_FORMATS:
            raise exception.DataFetchError(
                f"File format {self.file_format} is not supported. Only CSV files are supported."
            )

        try:
            if self.file_format in ("xlsx", "xls"):
                df = pd.read_excel(self.file_path)
            elif self.file_format == "xml":
                df = pd.read_xml(self.file_path)
            else:
                df = pd.read_csv(self.file_path)
        except (
            pd.errors.ParserError,
            lxml.etree.XMLSyntaxError,
            UnicodeDecodeError,
            ValueError,
        ) as e:
            raise exception.DataFetchError(
                f"An error occurred during fetching data from file: {e}"
            )

        self.cache.set_data(self.make_cache_key(), df)

        return df

    def make_cache_key(self) -> str:
        return f"ckanext-charts:url:{self.file_path}"


class HardcodedDataFetcher(DataFetcherStrategy):
    def __init__(self, data: dict[str, list[Any]]):
        self.data = data

    def fetch_data(self) -> pd.DataFrame:
        try:
            df = pd.DataFrame(self.data)
        except ValueError as e:
            raise exception.DataFetchError(
                f"An error occurred during fetching hardcoded data: {e}"
            )

        return df

    def make_cache_key(self) -> str:
        return "not-cached"

    def invalidate_cache(self):
        pass
