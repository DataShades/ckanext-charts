from __future__ import annotations

from typing import Any, Dict

from ckan.logic.schema import validator_args

Schema = Dict[str, Any]


@validator_args
def settings_schema(
    default,
    unicode_safe,
    ignore_empty,
    ignore,
    int_validator,
    limit_to_configured_maximum,
) -> Schema:
    return {
        "engine": [default("plotly"), unicode_safe],
        "type": [default("bar"), unicode_safe],
        "x": [ignore_empty, unicode_safe],
        "y": [ignore_empty, unicode_safe],
        "color": [ignore_empty, unicode_safe],
        # "query": [ignore_empty, unicode_safe],
        # "hover_name": [ignore_empty, unicode_safe],
        # "size": [ignore_empty, unicode_safe],
        # "size_max": [ignore_empty, v("int_validator")],
        # "animation_frame": [ignore_empty, unicode_safe],
        "limit": [
            default(100),
            int_validator,
            limit_to_configured_maximum("", 10_000),
        ],
        # "log_x": [boolean_validator],
        # "log_y": [boolean_validator],
        "__extras": [ignore],
    }
