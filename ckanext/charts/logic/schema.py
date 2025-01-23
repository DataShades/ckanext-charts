from __future__ import annotations

from typing import Any

from ckan.logic.schema import validator_args

Schema = dict[str, Any]


@validator_args
def settings_schema(charts_validate_extras) -> Schema:
    return {"__extras": [charts_validate_extras]}
