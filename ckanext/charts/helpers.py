from __future__ import annotations

from ckanext.charts import utils
from ckanext.charts.cache import count_file_cache_size, count_redis_cache_size


def get_redis_cache_size():
    """Get the size of the Redis cache in a human-readable format."""
    return utils.printable_file_size(count_redis_cache_size())


def get_file_cache_size():
    """Get the size of the file cache in a human-readable format."""
    return utils.printable_file_size(count_file_cache_size())


def get_available_chart_engines_options():
    """Get the available chart engines."""
    from ckanext.charts.chart_builders import get_chart_engines

    return [{"value": engine, "text": engine} for engine in get_chart_engines()]
