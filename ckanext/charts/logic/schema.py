from __future__ import annotations

from ckan.logic.schema import validator_args
from ckan.types import Schema


@validator_args
def settings_schema(charts_validate_extras) -> Schema:
    return {"__extras": [charts_validate_extras]}
