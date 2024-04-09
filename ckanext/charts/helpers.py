from __future__ import annotations

from typing import Any

import sqlalchemy as sa

import ckan.plugins.toolkit as tk

from ckanext.datastore.backend.postgres import get_read_engine


def charts_plotly_datastore(settings: dict[str, Any], resource_id: str):
    import pandas as pd
    import plotly.express as px

    if settings.get("type") in ["line", "bar", "scatter"]:
        x, y = settings.get("x"), settings.get("y")
        if not x or not y:
            return

        color = settings.get("color")
        limit = settings.get("limit", 2000000)
        try:
            df = pd.read_sql_query(
                sa.select(sa.text("*")).select_from(sa.table(resource_id)).limit(limit),
                get_read_engine(),
            ).drop(columns=["_id", "_full_text"])

        except tk.ValidationError:
            return

        if query := settings.get("query"):
            try:
                df = df.query(query)
            except ValueError:
                return

        if size := settings.get("size"):
            try:
                df = df.astype(
                    {
                        size: "float32",
                    }
                )
            except ValueError:
                return

        df2 = px.data.gapminder()
        # breakpoint()
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
