from __future__ import annotations

import math
from typing import Any

import ckan.plugins.toolkit as tk

from ckanext.charts.chart_builders import ChartJSBuilder, PlotlyBuilder
from ckanext.charts.fetchers import DatastoreDataFetcher


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
    if engine == "plotly":
        return PlotlyBuilder.get_form_for_type(chart_type)

    if engine == "chartjs":
        return ChartJSBuilder.get_form_for_type(chart_type)

    raise NotImplementedError(f"Engine {engine} is not supported")


def build_chart(settings: dict[str, Any], resource_id: str):
    from ckanext.charts.chart_builders import ChartJSBuilder, PlotlyBuilder
    from ckanext.charts.fetchers import DatastoreDataFetcher

    settings.pop("__extras", None)

    # x, y = settings.get("x"), settings.get("y")

    # if not x or not y:
    #     return None

    # limit = settings.get("limit", 2000000)

    try:
        df = DatastoreDataFetcher(resource_id).fetch_data()
    except tk.ValidationError:
        return None

    # TODO: rewrite it to pick the correct builder based on the engine more eloquently
    if settings["engine"] == "plotly":
        builder = PlotlyBuilder.get_builder_for_type(settings["type"])
    elif settings["engine"] == "chartjs":
        builder = ChartJSBuilder.get_builder_for_type(settings["type"])
    else:
        return None

    result = builder(df, settings)

    return result.to_json()
