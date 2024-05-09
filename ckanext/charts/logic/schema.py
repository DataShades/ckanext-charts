from __future__ import annotations

from typing import Any, Dict

from ckan.logic.schema import validator_args

Schema = Dict[str, Any]


@validator_args
def settings_schema(validate_chart_extras) -> Schema:
    return {
        "__extras": [validate_chart_extras],
    }


@validator_args
def default_schema(
    default,
    unicode_safe,
    ignore_empty,
    ignore,
    int_validator,
    limit_to_configured_maximum,
    boolean_validator,
    float_validator,
) -> Schema:
    return {
        "engine": [default("plotly"), unicode_safe],
        "type": [default("Bar"), unicode_safe],
        "x": [ignore_empty, unicode_safe],
        "y": [ignore_empty, unicode_safe],
        "color": [ignore_empty, unicode_safe],
        "query": [ignore_empty, unicode_safe],
        "animation_frame": [ignore_empty, unicode_safe],
        "limit": [
            default(100),
            int_validator,
            limit_to_configured_maximum("", 10_000),
        ],
        "log_x": [default(False), boolean_validator],
        "log_y": [default(False), boolean_validator],
        "sort_x": [default(False), boolean_validator],
        "sort_y": [default(False), boolean_validator],
        "opacity": [default(1), float_validator],
        "__extras": [ignore],
    }
