from __future__ import annotations

import math
from typing import Any

import pandas as pd
import sqlalchemy as sa

import ckan.plugins.toolkit as tk

from ckanext.datastore.backend.postgres import get_read_engine

from ckanext.charts.chart_builders import get_chart_engines
from ckanext.charts.exception import ChartBuildError
from ckanext.charts.fetchers import DatastoreDataFetcher


def get_column_options(resource_id: str) -> list[dict[str, str]]:
    """Get column options for the given resource.

    Args:
        resource_id: Resource ID

    Returns:
        List of column options
    """
    return [{"text": col, "value": col} for col in get_column_names(resource_id)]


def printable_file_size(size_bytes: int) -> str:
    """Convert file size in bytes to human-readable format.

    Args:
        size_bytes: File size in bytes

    Returns:
        str: Human-readable file size

    Examples:
        >>> printable_file_size(123456789)
        '117.7 MB'

        >>> printable_file_size(7777)
        '7.6 KB'
    """
    if size_bytes == 0:
        return "0 bytes"

    size_name = ("bytes", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(float(size_bytes) / p, 1)

    return f"{s} {size_name[i]}"


def get_chart_form_builder(engine: str, chart_type: str):
    """Get form builder for the given engine and chart type."""
    builders = get_chart_engines()

    if engine not in builders:
        raise NotImplementedError(f"Engine {engine} is not supported")

    return builders[engine].get_form_for_type(chart_type)


def build_chart_for_data(settings: dict[str, Any], data: pd.DataFrame) -> str | None:
    """Build chart for the given dataframe and settings.

    Args:
        settings: Chart settings
        data: Dataframe with data

    Returns:
        Chart config as JSON string
    """

    builder = get_chart_form_builder(settings["engine"], settings["type"])(
        dataframe=data,
    )

    settings, _ = tk.navl_validate(settings, builder.get_validation_schema(), {})

    return _build_chart(settings, data)


def build_chart_for_resource(settings: dict[str, Any], resource_id: str) -> str | None:
    """Build chart for the given resource ID.

    Uses a DatastoreDataFetcher to fetch data from the resource.

    Args:
        settings: Chart settings
        resource_id: Resource ID

    Returns:
        str | None: Chart config as JSON string or None if the chart can't be built
    """
    settings.pop("__extras", None)

    try:
        df = DatastoreDataFetcher(resource_id, settings).fetch_data()
    except tk.ValidationError:
        return None

    return _build_chart(settings, df)


def _build_chart(settings: dict[str, Any], dataframe: pd.DataFrame) -> str | None:
    """Get chart config for the given settings and dataframe"""
    builders = get_chart_engines()

    if settings["engine"] not in builders:
        return None

    builder = builders[settings["engine"]].get_builder_for_type(settings["type"])

    try:
        chart_config = builder(dataframe, settings).to_json()
    except KeyError as e:
        raise ChartBuildError(f"Missing column or field {e}") from e
    except ValueError as e:
        raise ChartBuildError(str(e)) from e

    return chart_config


def can_view(data_dict: dict[str, Any]) -> bool:
    """Check if the resource can be viewed as a chart.

    For now, we work only with resources stored with the DataStore.

    Args:
        data_dict: Resource data dictionary

    Returns:
        bool: True if the resource can be viewed as a chart, False otherwise
    """
    # TODO: Add support for XML, XLS, XLSX, and other formats tabular data?
    # if data_dict["resource"]["format"].lower() == "xml":
    #     return True

    return data_dict["resource"].get("datastore_active")


# TODO:
# - Cache the column names for a day.
# - Ensure that when the resource changes, the cache is cleared, so the actual columns
# are fetched.
def get_column_names(resource_id: str) -> list[str]:
    inspector = sa.inspect(get_read_engine())
    columns = inspector.get_columns(resource_id)
    return [col["name"] for col in columns if col["name"] not in {"_id", "_full_text"}]
