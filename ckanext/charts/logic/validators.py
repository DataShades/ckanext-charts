from __future__ import annotations

from typing import Any, Callable

import ckan.plugins.toolkit as tk

from ckanext.charts import utils
from ckanext.charts.chart_builders import DEFAULT_CHART_FORM


def float_validator(value):
    try:
        return float(value)
    except ValueError:
        raise tk.Invalid(tk._("Must be a decimal number")) from None


def charts_if_empty_same_as(other_key: str) -> Callable[..., Any]:
    """A custom version of if_empty_same_as validator for charts"""

    def callable(key, data, errors, context):
        value = data.get(key)
        if not value or value is tk.missing:
            try:
                data[key] = data[key[:-1] + (other_key,)]
            except KeyError:
                data[key] = data.get(("__extras",), {}).get(other_key, "")

    return callable


def validate_chart_extras(key, data, errors, context):
    """Use a custom validation schema for specific chart types."""
    settings = _extract_setting(data)

    if "engine" not in settings or "type" not in settings:
        builder = DEFAULT_CHART_FORM
    else:
        builder = utils.get_chart_form_builder(settings["engine"], settings["type"])

    settings, err = tk.navl_validate(
        settings,
        builder(settings["resource_id"]).get_validation_schema(),
        {},
    )

    # TODO: do we have a better way to handle this? Seems like a hack
    for k, v in settings.items():
        data[(k,)] = v

    for k, v in settings.pop("__extras", {}).items():
        data[(k,)] = v

    for k, v in err.items():
        errors[(k,)] = v


def _extract_setting(data) -> dict[str, Any]:
    result = {}

    for k, v in data.items():
        result[k[0]] = v

    result.update(data.get(("__extras",), {}))

    return result
