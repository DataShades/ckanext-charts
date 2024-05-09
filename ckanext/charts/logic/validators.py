import ckan.plugins.toolkit as tk

from ckanext.charts.logic.schema import default_schema


def float_validator(value):
    try:
        return float(value)
    except ValueError:
        raise tk.Invalid(tk._("Must be a decimal number")) from None


def validate_chart_extras(key, data, errors, context):
    settings = data.get(("__extras",), {})

    if "engine" not in settings:
        settings, _ = tk.navl_validate(settings, default_schema(), {})
        data[("__extras",)] = settings

    for k, v in data[("__extras",)].items():
        data[(k,)] = v
