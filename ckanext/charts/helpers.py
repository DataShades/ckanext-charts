from __future__ import annotations

import json

import ckan.plugins.toolkit as tk

from ckanext.charts import config, utils
from ckanext.charts.cache import count_file_cache_size, count_redis_cache_size
from ckanext.charts.chart_builders import get_chart_engines
from ckanext.charts.fetchers import DatastoreDataFetcher


def get_redis_cache_size() -> str:
    """Get the size of the Redis cache in a human-readable format.

    Returns:
        str: Human-readable Redis cache size
    """
    return utils.printable_file_size(count_redis_cache_size())


def get_file_cache_size() -> str:
    """Get the size of the file cache in a human-readable format.

    Returns:
        str: Human-readable file cache size
    """
    return utils.printable_file_size(count_file_cache_size())


def get_available_chart_engines_options() -> list[dict[str, str]]:
    """Get the available chart engines.

    Returns:
        List of chart engines options
    """
    return [{"value": engine, "text": engine} for engine in get_chart_engines()]


def charts_include_htmx_asset() -> bool:
    """Checks if the HTMX asset should be included.

    Returns:
        bool: True if the HTMX asset should be included, False otherwise.
    """
    return config.include_htmx_asset()


def charts_reinit_ckan_js_modules() -> bool:
    """Checks if CKAN JS modules should be reinitialized.

    Returns:
        bool: True if CKAN JS modules should be reinitialized, False otherwise.
    """
    return config.reinit_ckan_js_modules()


def charts_get_resource_columns(resource_id: str) -> str:
    """Get the columns of the given resource.

    Args:
        resource_id: Resource ID

    Returns:
        str: JSON string of columns options
    """
    fetcher = DatastoreDataFetcher(resource_id)

    return json.dumps(
        [{"id": col, "title": col} for col in fetcher.fetch_data().columns],
    )


def charts_user_is_authenticated() -> bool:
    """Check if the user is authenticated.

    Returns:
        bool: True if the user is authenticated, False otherwise.
    """
    return tk.current_user.is_authenticated


def charts_allow_anon_building_charts() -> bool:
    """Check if anonymous users are allowed to build charts.

    Returns:
        bool: True if anonymous users are allowed to build charts, False otherwise.
    """
    return config.allow_anon_building_charts()
