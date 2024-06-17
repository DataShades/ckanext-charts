from __future__ import annotations

import math
from typing import Any

import pandas as pd

import ckan.plugins.toolkit as tk

from ckanext.charts.chart_builders import get_chart_engines
from ckanext.charts.fetchers import DatastoreDataFetcher
from ckanext.charts.exception import ChartBuildError


def get_column_options(resource_id: str) -> list[dict[str, str]]:
    """Get column options for the given resource"""
    df = DatastoreDataFetcher(resource_id).fetch_data()

    return [{"text": col, "value": col} for col in df.columns]


def printable_file_size(size_bytes: int) -> str:
    """Convert file size in bytes to human-readable format"""
    if size_bytes == 0:
        return "0 bytes"

    size_name = ("bytes", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(float(size_bytes) / p, 1)

    return f"{s} {size_name[i]}"


def get_chart_form_builder(engine: str, chart_type: str):
    builders = get_chart_engines()

    if engine not in builders:
        raise NotImplementedError(f"Engine {engine} is not supported")

    return builders[engine].get_form_for_type(chart_type)


def build_chart_for_data(settings: dict[str, Any], data: pd.DataFrame):
    """Build chart for the given dataframe"""
    return _build_chart(settings, data)


def build_chart_for_resource(settings: dict[str, Any], resource_id: str):
    """Build chart for the given resource ID"""
    settings.pop("__extras", None)

    try:
        df = DatastoreDataFetcher(resource_id).fetch_data()
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
        raise ChartBuildError(f"Missing column or field {e}")
    except ValueError as e:
        raise ChartBuildError(f"{e}")

    return chart_config


def can_view_be_viewed(data_dict: dict[str, Any]) -> bool:
    if data_dict["resource"].get("datastore_active"):
        return True

    # TODO: Add support for XML, XLS, XLSX, and other formats tabular data?
    # if data_dict["resource"]["format"].lower() == "xml":
    #     return True

    return False
