from __future__ import annotations

from typing import Any, Dict

from ckan.logic.schema import validator_args

Schema = Dict[str, Any]


@validator_args
def settings_schema(validate_chart_extras) -> Schema:
    return {
        "__extras": [validate_chart_extras],
    }
