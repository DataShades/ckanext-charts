from __future__ import annotations

from typing import Any

import ckan.plugins.toolkit as tk

import ckanext.charts.utils as utils


def charts_plotly_datastore(settings: dict[str, Any], resource_id: str):

    import plotly.express as px
    from ckanext.charts.fetchers import DatastoreDataFetcher

    if settings.get("type") in ["line", "bar", "scatter"]:
        x, y = settings.get("x"), settings.get("y")

        if not x or not y:
            return

        color = settings.get("color")
        limit = settings.get("limit", 2000000)

        try:
            df = DatastoreDataFetcher(resource_id, limit).fetch_data()
        except tk.ValidationError:
            return

        # if query := settings.get("query"):
        #     try:
        #         df = df.query(query)
        #     except ValueError:
        #         return

        if size := settings.get("size"):
            try:
                df = df.astype(
                    {
                        size: "float32",
                    }
                )
            except ValueError:
                return

        kwargs = dict(
            log_x=settings.get("log_x"),
            log_y=settings.get("log_y"),
            x=x,
            y=y,
            color=color,
            animation_frame=settings.get("animation_frame"),
            hover_name=settings.get("hover_name"),
            # size_max=45,
            # range_x=[100, 100000],
            # range_y=[25, 90],
        )

        if settings["type"] == "scatter":
            kwargs["size"] = size
            kwargs["size_max"] = settings.get("size_max")

        func = getattr(px, settings["type"])

        return func(df, **kwargs)


from ckanext.charts.cache import count_redis_cache_size, count_file_cache_size


def get_redis_cache_size():
    """Get the size of the Redis cache in a human-readable format."""
    return utils.printable_file_size(count_redis_cache_size())


def get_file_cache_size():
    """Get the size of the file cache in a human-readable format."""
    return utils.printable_file_size(count_file_cache_size())
