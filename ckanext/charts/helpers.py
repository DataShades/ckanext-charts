from __future__ import annotations

import json

import ckan.plugins.toolkit as tk

from ckanext.charts import utils
from ckanext.charts.cache import count_file_cache_size, count_redis_cache_size
from ckanext.charts import config
from ckanext.charts.fetchers import DatastoreDataFetcher
from ckanext.charts.chart_builders import get_chart_engines


def get_redis_cache_size():
    """Get the size of the Redis cache in a human-readable format."""
    return utils.printable_file_size(count_redis_cache_size())


def get_file_cache_size():
    """Get the size of the file cache in a human-readable format."""
    return utils.printable_file_size(count_file_cache_size())


def get_available_chart_engines_options():
    """Get the available chart engines."""
    return [{"value": engine, "text": engine} for engine in get_chart_engines()]


def charts_include_htmx_asset() -> bool:
    """Include HTMX asset if enabled."""
    return config.include_htmx_asset()


def charts_reinit_ckan_js_modules() -> bool:
    """Reinitialize CKAN JS modules."""
    return config.reinit_ckan_js_modules()


def charts_get_resource_columns(resource_id: str) -> str:
    """Get the columns of the given resource."""
    fetcher = DatastoreDataFetcher(resource_id)

    return json.dumps(
        [{"id": col, "title": col} for col in fetcher.fetch_data().columns]
    )


def charts_user_is_authenticated() -> bool:
    """Check if the user is authenticated."""
    return tk.current_user.is_authenticated


def charts_allow_anon_building_charts() -> bool:
    """Allow anonymous users to build charts."""
    return config.allow_anon_building_charts()
