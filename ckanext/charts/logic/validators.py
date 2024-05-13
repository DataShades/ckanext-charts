import ckan.plugins.toolkit as tk

from ckanext.charts import utils
from ckanext.charts.chart_builders.plotly import PlotlyBarForm


def float_validator(value):
    try:
        return float(value)
    except ValueError:
        raise tk.Invalid(tk._("Must be a decimal number")) from None


def validate_chart_extras(key, data, errors, context):
    settings = data.get(("__extras",), {})
    resource_id = data.get(("resource_id",)) or settings["resource_id"]

    # use plotly bar as default settings
    if "engine" not in settings or "type" not in settings:
        builder = PlotlyBarForm
    else:
        builder = utils.get_chart_form_builder(settings["engine"], settings["type"])

    settings, _ = tk.navl_validate(
        settings, builder(resource_id).get_validation_schema(), {}
    )

    for k, v in settings.items():
        data[(k,)] = v

    for k, v in settings.pop("__extras", {}).items():
        data[(k,)] = v
