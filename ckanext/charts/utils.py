from __future__ import annotations

import math
from typing import Any

import ckan.plugins.toolkit as tk


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
        {},
        {"resource_id": resource_id, "limit": 0},
    )
    return [
        {"text": f["id"], "value": f["id"]}
        for f in result["fields"]
        if f["id"] != "_id"
    ]


def printable_file_size(size_bytes: int) -> str:
    if size_bytes == 0:
        return "0 bytes"

    size_name = ("bytes", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(float(size_bytes) / p, 1)

    return f"{s} {size_name[i]}"
