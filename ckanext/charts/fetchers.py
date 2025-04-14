from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from io import BytesIO
from typing import Any

import lxml
import pandas as pd
import requests
import sqlalchemy as sa
from psycopg2.errors import UndefinedTable
from sqlalchemy.exc import ProgrammingError

from ckanext.datastore.backend.postgres import get_read_engine

from ckanext.charts import cache, config, exception

log = logging.getLogger(__name__)


class DataFetcherStrategy(ABC):
    def __init__(self, cache_strategy: str | None = None) -> None:
        self.cache = cache.get_cache_manager(cache_strategy)

    @abstractmethod
    def fetch_data(self) -> pd.DataFrame:
        """This method should implement the data fetch logic.

        All the necessary information should be provided in the constructor.

        Returns:
            pd.DataFrame: The fetched data
        """

    @abstractmethod
    def make_cache_key(self) -> str:
        """This method should generate a cache key for the fetched data.

        Every data fetcher should implement this method to support caching.

        Returns:
            str: The cache key
        """

    def invalidate_cache(self):
        """Invalidate the cache for the data fetcher."""
        self.cache.invalidate(self.make_cache_key())

    def get_cached_data(self) -> pd.DataFrame | None:
        """Fetch data from the cache.

        Returns:
            pd.DataFrame | None: The cached data or None if not found
        """
        return self.cache.get_data(self.make_cache_key())


class DatastoreDataFetcher(DataFetcherStrategy):
    """Fetch dataset resource data from the DataStore.

    This fetcher is used to fetch data from the DataStore using the resource ID.
    """

    def __init__(
        self,
        resource_id: str,
        limit: int = 2000000,
        cache_strategy: str | None = None,
    ):
        """Initialize the DatastoreDataFetcher.

        Args:
            resource_id (str): The ID of the resource to fetch data for.
            limit (int, optional): The maximum number of rows to fetch.
            cache_strategy (str, optional): The cache strategy to use. If not provided,
                the configured cache strategy will be used.
        """

        super().__init__(cache_strategy=cache_strategy)

        self.resource_id = resource_id
        self.limit = limit

    def fetch_data(self) -> pd.DataFrame:
        """Fetch data from the DataStore.

        Returns:
            pd.DataFrame: Data from the DataStore
        """
        if config.is_cache_enabled():
            cached_df = self.get_cached_data()

            if cached_df is not None:
                return cached_df

        try:
            df = pd.read_sql_query(
                sa.select(sa.text("*"))  # type: ignore
                .select_from(sa.table(self.resource_id))
                .limit(self.limit),
                get_read_engine(),
            ).drop(columns=["_id", "_full_text"], errors="ignore")

            if "date_time" in df.columns:
                try:
                    df["date_time"] = pd.to_datetime(df["date_time"])
                    # Convert valid dates to ISO format
                    df["date_time"] = df["date_time"].dt.strftime("%Y-%m-%dT%H:%M:%S")
                except (ValueError, TypeError, AttributeError) as e:
                    # Log the warning and keep the original values if conversion fails
                    log.warning("Warning: Could not convert date_time column: %s", e)

            # Apply numeric conversion to all columns - it will safely ignore
            # non-numeric values
            df = df.apply(pd.to_numeric, errors="ignore")

        except (ProgrammingError, UndefinedTable) as e:
            raise exception.DataFetchError(
                f"An error occurred during fetching data from DataStore: {e}",
            ) from e

        if config.is_cache_enabled():
            self.cache.set_data(self.make_cache_key(), df)

        return df

    def make_cache_key(self) -> str:
        """Generate a cache key for the DataStore data fetcher.

        Uses the resource ID as the part of a cache key.

        Returns:
            str: The cache key
        """
        return f"ckanext-charts:datastore:{self.resource_id}"


class URLDataFetcher(DataFetcherStrategy):
    """Fetch data from a URL.

    This fetcher is used to fetch data from a URL.

    Supported formats:
        - `CSV`
        - `XLSX`
        - `XLS`
        - `XML`
    """

    SUPPORTED_FORMATS = ["csv", "xlsx", "xls", "xml"]

    def __init__(
        self,
        url: str,
        file_format: str = "csv",
        timeout: int = 0,
        cache_strategy: str | None = None,
    ):
        """Initialize the URLDataFetcher.

        Args:
            url (str): The URL to fetch data from.
            file_format (str, optional): The format of the file.
            timeout (int, optional): The timeout for the request in seconds.
            cache_strategy (str, optional): The cache strategy to use. If not provided,
                the configured cache strategy will be used.
        """
        super().__init__(cache_strategy=cache_strategy)

        self.url = url
        self.file_format = file_format
        self.timeout = timeout

    def fetch_data(self) -> pd.DataFrame:
        """Fetch data from the URL.

        Returns:
            pd.DataFrame: Data fetched from the URL
        """
        if config.is_cache_enabled():
            cached_df = self.get_cached_data()

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
                f"An error occurred during fetching data from URL: {e}",
            ) from e

        if config.is_cache_enabled():
            self.cache.set_data(self.make_cache_key(), df)

        return df

    def make_cache_key(self) -> str:
        """Generate a cache key for the URL data fetcher.

        Uses the URL as the part of a cache key.

        Returns:
            str: The cache key
        """
        return f"ckanext-charts:url:{self.url}"

    def make_request(self) -> bytes:
        """Make a request to the URL and return the response content.

        Returns:
            bytes: The response content

        Raises:
            DataFetchError: If an error occurs during the request
        """
        try:
            response = requests.get(self.url)
            response.raise_for_status()
        except requests.exceptions.HTTPError:
            log.exception("HTTP error occurred")
        except requests.exceptions.ConnectionError:
            log.exception("Connection error occurred")
        except requests.exceptions.Timeout:
            log.exception("Timeout error occurred")
        except requests.exceptions.RequestException:
            log.exception("An error occurred during the request")
        except Exception:
            log.exception("An unexpected error occurred")
        else:
            return response.content

        raise exception.DataFetchError(
            f"An error occurred during fetching data by URL: {self.url}",
        )


class FileSystemDataFetcher(DataFetcherStrategy):
    """Fetch data from the file system.

    This fetcher is used to fetch data from a file on the file system.

    Supported formats:
        - `CSV`
        - `XLSX`
        - `XLS`
        - `XML`
    """

    SUPPORTED_FORMATS = ["csv", "xlsx", "xls", "xml"]

    def __init__(
        self,
        file_path: str,
        file_format: str = "csv",
        cache_strategy: str | None = None,
    ):
        """Initialize the FileSystemDataFetcher.

        Args:
            file_path (str): The path to the file.
            file_format (str, optional): The format of the file.
            cache_strategy (str, optional): The cache strategy to use. If not provided,
                the configured cache strategy will be used.
        """
        super().__init__(cache_strategy=cache_strategy)

        self.file_path = file_path
        self.file_format = file_format

    def fetch_data(self) -> pd.DataFrame:
        """Fetch data from the file system.

        Returns:
            pd.DataFrame: Data fetched from the file system
        """

        if config.is_cache_enabled():
            cached_df = self.get_cached_data()

            if cached_df is not None:
                return cached_df

        if self.file_format not in self.SUPPORTED_FORMATS:
            raise exception.DataFetchError(
                f"File format {self.file_format} is not supported. "
                "Only CSV files are supported.",
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
                f"An error occurred during fetching data from file: {e}",
            ) from e

        if config.is_cache_enabled():
            self.cache.set_data(self.make_cache_key(), df)

        return df

    def make_cache_key(self) -> str:
        """Generate a cache key for the FileSystem data fetcher.

        Uses the file path as the part of a cache key.

        Returns:
            str: The cache key
        """
        return f"ckanext-charts:url:{self.file_path}"


class HardcodedDataFetcher(DataFetcherStrategy):
    """Fetch hardcoded data.

    This fetcher is used to make a dataframe from hardcoded data, so you can
    build a chart from it.
    """

    def __init__(self, data: dict[str, list[Any]]):
        """Initialize the HardcodedDataFetcher.

        Args:
            data (dict[str, list[Any]]): The hardcoded data.
        """
        self.data = data

    def fetch_data(self) -> pd.DataFrame:
        """Transform arbitrary data into a dataframe.

        Returns:
            pd.DataFrame: The hardcoded data as a dataframe
        """
        try:
            df = pd.DataFrame(self.data)
        except ValueError as e:
            raise exception.DataFetchError(
                f"An error occurred during fetching hardcoded data: {e}",
            ) from e

        return df

    def make_cache_key(self) -> str:
        """Hardcoded data is not cached"""
        return "not-cached"

    def invalidate_cache(self) -> None:
        """Hardcoded data is not cached"""
