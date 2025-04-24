from __future__ import annotations

from typing import Any, Callable

import ckan.plugins.toolkit as tk
from ckan import types

from ckanext.charts import const, utils
from ckanext.charts.chart_builders import DEFAULT_CHART_FORM


def float_validator(value: Any) -> float:
    """A validator for decimal numbers.

    Args:
        value (Any): The value to validate

    Returns:
        float: The value as a float
    """
    try:
        return float(value)
    except ValueError:
        raise tk.Invalid(tk._("Must be a decimal number")) from None


def charts_if_empty_same_as(other_key: str) -> Callable[..., Any]:
    """A custom version of if_empty_same_as validator for charts.

    This validator is used to set the value of a field to the value of another
    field if it is empty or missing.

    Args:
        other_key (str): The key of the field to copy the value from

    Returns:
        Callable[..., Any]: The validator function
    """

    def callable(key, data, errors, context):
        value = data.get(key)
        if not value or value is tk.missing:
            try:
                data[key] = data[key[:-1] + (other_key,)]
            except KeyError:
                data[key] = data.get(("__extras",), {}).get(other_key, "")

    return callable


def charts_strategy_support(strategy: str) -> str:
    """Check if the cache strategy is supported.

    Args:
        strategy (str): The cache strategy

    Returns:
        str: The cache strategy if it is supported

    Raises:
        tk.Invalid: If the cache strategy is not supported
    """
    if strategy not in const.SUPPORTED_CACHE_STRATEGIES:
        raise tk.Invalid(tk._("Invalid cache strategy"))

    if strategy == const.CACHE_FILE_ORC:
        try:
            from pyarrow import orc as _  # noqa
        except ImportError:
            raise tk.Invalid(
                tk._("Can't use File Orc cache strategy. PyArrow is not installed"),
            ) from None

    if not strategy:
        return const.DEFAULT_CACHE_STRATEGY

    return strategy


def charts_validate_extras(
    key: types.FlattenKey,
    data: types.FlattenDataDict,
    errors: types.FlattenErrorDict,
    context: types.Context,
):
    """Validate charts settings according to the chart type and engine schema.

    Args:
        key (types.FlattenKey): The key of the field
        data (types.FlattenDataDict): The data to validate
        errors (types.FlattenErrorDict): The errors dict
        context (types.Context): The context
    """
    settings = _extract_setting(data)

    if "engine" not in settings or "type" not in settings:
        builder = DEFAULT_CHART_FORM
    else:
        builder = utils.get_chart_form_builder(settings["engine"], settings["type"])

    settings, err = tk.navl_validate(
        settings,
        builder(settings["resource_id"], settings.get("id")).get_validation_schema(
            context.get("_for_show", False),
        ),
        {},
    )

    # TODO: do we have a better way to handle this? Seems like a hack
    for k, v in settings.items():
        data[(k,)] = v

    for k, v in settings.pop("__extras", {}).items():
        data[(k,)] = v

    for k, v in err.items():
        errors[(k,)] = v


def _extract_setting(data: types.FlattenDataDict) -> dict[str, Any]:
    result = {}

    for k, v in data.items():
        result[k[0]] = v

    result.update(data.get(("__extras",), {}))

    return result


def charts_to_list_if_string(value: Any) -> Any:
    """Convert a string to a list.

    Args:
        value (Any): The value to convert

    Returns:
        list[Any]: The value in a list
    """
    if isinstance(value, str):
        return [value]

    return value


def charts_list_to_csv(data: list[str] | str) -> str:
    """Convert a list of strings to a CSV string.

    Args:
        data (list[str] | str): The data to convert

    Returns:
        str: The comma separated string
    """
    if not isinstance(data, list):
        return data

    return ", ".join(data)


def charts_list_length_validator(max_length: int) -> Callable[..., Any]:
    """A validator to check the length of a list.

    Args:
        max_length (int): The maximum length of the list

    Returns:
        Callable[..., Any]: The validator function
    """
    def callable(
        key: types.FlattenKey,
        data: types.FlattenDataDict,
        errors: types.FlattenErrorDict,
        context: types.Context,
    ):
        if len(data[key]) > max_length:
            raise tk.Invalid(tk._("Length must be less than {0}").format(max_length))

    return callable


def chart_checkbox(value: str | list[str]) -> str:
    """A validator for checkbox.

    In a checkbox form snippet we have two inputs, one hidden and one checkbox.
    The hidden input always sends a value of "off" and the checkbox sends "on"

    We need it to properly set a default `True` value for the field.

    Args:
        value (str | list[str]): The checkbox(s) value(s)

    Returns:
        bool: The value as a boolean
    """
    if isinstance(value, list):
        return value[-1]

    return value
