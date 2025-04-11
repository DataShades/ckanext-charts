from __future__ import annotations

import logging
import hashlib
import json
from abc import ABC, abstractmethod
from io import BytesIO
from typing import Any

import lxml
import pandas as pd
import requests
import sqlalchemy as sa
from psycopg2.errors import UndefinedTable
from sqlalchemy.exc import ProgrammingError

import ckan.plugins.toolkit as tk

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
        settings: dict[str, Any] | None = None,
        limit: int = 50000,
        cache_strategy: str | None = None,
    ):
        """Initialize the DatastoreDataFetcher.

        Args:
            resource_id (str): The ID of the resource to fetch data for.
            settings (dict[str, Any], optional): The settings for the chart.
            limit (int, optional): The maximum number of rows to fetch.
            cache_strategy (str, optional): The cache strategy to use. If not provided,
                the configured cache strategy will be used.
        """

        super().__init__(cache_strategy=cache_strategy)

        self.resource_id = resource_id
        self.limit = limit
        self.settings = settings

    def fetch_data(self) -> pd.DataFrame:
        """Fetch data from the DataStore.

        Returns:
            pd.DataFrame: Data from the DataStore
        """
        try:
            needed_columns = self.get_needed_columns()
            filter_conditions = self.parse_filters()

            columns_expr = self._prepare_column_expressions(needed_columns)

            if columns_expr:
                query = sa.select(*columns_expr).select_from(sa.table(self.resource_id))
                if filter_conditions:
                    query = query.where(sa.and_(*filter_conditions))

                limit = (
                    self.settings.get("limit", self.limit)
                    if self.settings
                    else self.limit
                )
                query = query.limit(limit)

            else:
                # Fallback: Fetch a single row to identify available columns
                # (excluding system columns).
                # This query is lightweight, with a limit of 1 to avoid unnecessary
                # expense before using actual data fields or filters.
                columns_expr = self._get_all_table_columns()
                query = (
                    sa.select(*columns_expr)
                    .select_from(sa.table(self.resource_id))
                    .limit(1)
                )

            sort_clauses = self.build_sort_clauses()
            if sort_clauses:
                query = query.order_by(*sort_clauses)

            df = pd.read_sql_query(query, get_read_engine())
            # Apply numeric conversion to all columns - it will safely ignore
            # non-numeric values
            df = df.apply(pd.to_numeric, errors="ignore")

        except (ProgrammingError, UndefinedTable, sa.exc.NoSuchTableError) as e:
            raise exception.DataFetchError(
                f"Error fetching data from DataStore: {e}",
            ) from e

        return df

    def _format_column(self, col_name: str):
        """Format the 'date_time' column for SQL queries; return other columns as-is.

        - 'date_time' is cast to TIMESTAMP and formatted as ISO 8601 string.
        - All other column names are returned as SQLAlchemy column expressions.
        """
        if col_name == "date_time":
            return sa.func.to_char(
                sa.cast(sa.column("date_time"), sa.TIMESTAMP),
                'YYYY-MM-DD"T"HH24:MI:SS',
            ).label("date_time")
        return sa.column(col_name)

    def _prepare_column_expressions(self, column_names):
        """Convert column names to SQLAlchemy column expressions."""
        if not column_names:
            return []

        return [self._format_column(col) for col in column_names]

    def _get_all_table_columns(self):
        """Get all columns from the table, excluding system columns."""
        inspector = sa.inspect(get_read_engine())
        columns = inspector.get_columns(self.resource_id)

        return [
            self._format_column(col["name"])
            for col in columns
            if col["name"] not in {"_id", "_full_text"}
        ]

    def get_needed_columns(self) -> set:
        """Extract a set of all column names required for chart generation.

        This includes:
        - Fields explicitly defined in the chart settings (e.g., 'x', 'y', 'color', etc)
        - Filter columns used in the 'filter' expression (e.g., 'column:value|...')
        """
        needed_columns = set()
        if self.settings:
            for field in [
                "x",
                "y",
                "color",
                "animation_frame",
                "size",
                "names",
                "values",
            ]:
                value = self.settings.get(field)
                if isinstance(value, list):
                    needed_columns.update(value)
                elif value:
                    needed_columns.add(value)

            # Include filter columns
            filters = self.settings.get("filter")
            if filters:
                for condition in filters.split("|"):
                    if ":" in condition:
                        column, _ = condition.split(":", 1)
                        needed_columns.add(column.strip())
        return needed_columns

    def parse_filters(self) -> list:
        """Parse filter string from settings into SQLAlchemy expressions.

        Returns:
            list: List of SQLAlchemy filter expressions (e.g., column == value).
        """
        expressions = []
        if self.settings:
            filters = self.settings.get("filter")

            if filters:
                for condition in filters.split("|"):
                    if ":" in condition:
                        column, value = condition.split(":", 1)
                        expressions.append(sa.column(column) == value)
        return expressions

    def build_sort_clauses(self) -> list:
        """Build sort clauses for SQL query based on settings."""
        sort_clauses = []

        if not self.settings:
            return sort_clauses

        if not isinstance(self.settings.get("sort_x"), list) and tk.asbool(
            self.settings.get("sort_x"),
        ):
            sort_clauses.append(sa.column(self.settings.get("x")))

        if not isinstance(self.settings.get("sort_y"), list) and tk.asbool(
            self.settings.get("sort_y"),
        ):
            y_fields = self.settings.get("y")
            if isinstance(y_fields, list):
                sort_clauses.extend(
                    sa.column(field) for field in y_fields if isinstance(field, str)
                )
            elif isinstance(y_fields, str):
                sort_clauses.append(sa.column(y_fields))

        return sort_clauses

    def make_cache_key(self) -> str:
        """Generate a cache key for the DataStore data fetcher.

        Uses the resource ID as the part of a cache key.

        Returns:
            str: The cache key
        """
        prefix = f"ckanext-charts:datastore:{self.resource_id}"

        if not self.settings:
            return prefix

        # Extract only fields that affect the query
        query_relevant = {
            "x": self.settings.get("x"),
            "y": self.settings.get("y"),
            "color": self.settings.get("color"),
            "animation_frame": self.settings.get("animation_frame"),
            "filter": self.settings.get("filter"),
            "limit": self.settings.get("limit"),
            "sort_x": self.settings.get("sort_x"),
            "sort_y": self.settings.get("sort_y"),
            "resource_id": self.resource_id,
        }

        settings_part = hashlib.md5(
            json.dumps(query_relevant, sort_keys=True).encode(),
        ).hexdigest()

        return f"{prefix}:settings:{settings_part}"


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
