from __future__ import annotations

from typing import Any

import ckan.plugins.toolkit as tk


def settings_schema() -> dict[str, Any]:
    v = tk.get_validator
    return {
        "engine": [v("default")("plotly"), v("unicode_safe")],
        "type": [v("ignore_empty"), v("unicode_safe")],
        "x": [v("ignore_empty"), v("unicode_safe")],
        "y": [v("ignore_empty"), v("unicode_safe")],
        "color": [v("ignore_empty"), v("unicode_safe")],
        "query": [v("ignore_empty"), v("unicode_safe")],
        "hover_name": [v("ignore_empty"), v("unicode_safe")],
        "size": [v("ignore_empty"), v("unicode_safe")],
        "size_max": [v("ignore_empty"), v("int_validator")],
        "animation_frame": [v("ignore_empty"), v("unicode_safe")],
        "limit": [
            v("default")(100),
            v("int_validator"),
            v("limit_to_configured_maximum")("", 10_000),
        ],
        "log_x": [v("boolean_validator")],
        "log_y": [v("boolean_validator")],
        "__extras": [v("ignore")],
    }


def settings_from_dict(data: dict[str, Any]):
    attrs = [
        "engine",
        "type",
        "x",
        "y",
        "log_x",
        "log_y",
        "color",
        "query",
        "hover_name",
        "size",
        "size_max",
        "limit",
        "animation_frame",
    ]
    settings = {k: data.get(k, None) for k in attrs}

    if not settings["engine"]:
        settings["engine"] = "plotly"
    return settings


def get_column_options(resource_id: str):
    result = tk.get_action("datastore_search")(
        {}, {"resource_id": resource_id, "limit": 0}
    )
    return [
        {"text": f["id"], "value": f["id"]}
        for f in result["fields"]
        if f["id"] != "_id"
    ]
