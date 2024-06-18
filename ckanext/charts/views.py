from __future__ import annotations

from flask import Blueprint, jsonify
from flask.views import MethodView

import ckan.plugins.toolkit as tk
from ckan.logic import parse_params
from ckan.plugins import plugin_loaded

from ckanext.charts import cache, exception, utils, fetchers

charts = Blueprint("charts_view", __name__)
ERROR_TEMPLATE = "charts/snippets/error_chart.html"


@charts.route("/api/utils/charts/<resource_id>/update-chart")
def update_chart(resource_id: str) -> str:
    data = parse_params(tk.request.args)

    try:
        builder = _get_form_builder(data)
    except exception.ChartTypeNotImplementedError:
        return tk.render(ERROR_TEMPLATE)

    data, errors = tk.navl_validate(data, builder.get_validation_schema(), {})

    if errors:
        return tk.render_snippet(ERROR_TEMPLATE, {"error_msg": errors})

    try:
        return tk.render_snippet(
            f"charts/snippets/{data['engine']}_chart.html",
            {"chart": utils.build_chart_for_resource(data, resource_id)},
        )
    except exception.ChartTypeNotImplementedError:
        return tk.render(ERROR_TEMPLATE)
    except exception.ChartBuildError as e:
        return tk.render(
            ERROR_TEMPLATE,
            {"error_msg": tk._(f"Error building chart: {e}")},
        )


@charts.route("/api/utils/charts/update-form")
def update_form():
    data = parse_params(tk.request.args)
    resource_id = data["resource_id"]
    user_builder: bool = tk.asbool(data.pop("user_chart_builder", False))

    # if we're changing the engine, drop the chart type, cause we don't know
    # the list of supported types for the new engine
    if data.pop("reset_engine", False):
        data["type"] = ""

    try:
        builder = _get_form_builder(data)
    except exception.ChartTypeNotImplementedError:
        return tk.render(ERROR_TEMPLATE)

    data, errors = tk.navl_validate(data, builder.get_validation_schema(), {})

    extra_vars = {
        "builder": builder,
        "resource_id": resource_id,
        "data": data,
        "errors": errors,
        "active_tab": "Structure",
        "user_chart_builder": user_builder,
    }

    if user_builder:
        extra_vars["exclude_tabs"] = ["General"]

    return tk.render_snippet("charts/snippets/charts_form_fields.html", extra_vars)


@charts.route("/api/utils/charts/<resource_id>/clear-chart")
def clear_chart(resource_id: str):
    return _clear_chart(resource_id)


@charts.route("/api/utils/charts/<resource_id>/clear-builder-chart")
def clear_user_builder_chart(resource_id: str):
    return _clear_chart(resource_id, exclude_tabs=["General"], user_chart_builder=True)


def _clear_chart(
    resource_id: str,
    exclude_tabs: None | list[str] = None,
    user_chart_builder: bool = False,
):
    builder = _get_form_builder(
        {"engine": "plotly", "type": "Bar", "resource_id": resource_id}
    )

    data, errors = tk.navl_validate({}, builder.get_validation_schema(), {})

    if not exclude_tabs:
        exclude_tabs = []

    return tk.render_snippet(
        "charts/snippets/charts_form_fields.html",
        {
            "builder": builder,
            "resource_id": resource_id,
            "data": data,
            "errors": errors,
            "active_tab": "General",
            "exclude_tabs": exclude_tabs,
            "user_chart_builder": user_chart_builder,
        },
    )


def _get_form_builder(data: dict):
    """Get form builder for the given engine and chart type"""
    if "engine" not in data or "type" not in data:
        raise exception.ChartTypeNotImplementedError

    builder = utils.get_chart_form_builder(data["engine"], data["type"])

    return builder(data["resource_id"])


@charts.route("/api/utils/charts/get-values")
def get_chart_column_values():
    data = parse_params(tk.request.args)

    resource_id = tk.get_or_bust(data, "resource_id")
    column = tk.get_or_bust(data, "column")

    fetcher = fetchers.DatastoreDataFetcher(resource_id)

    result = []

    for val in fetcher.fetch_data()[column].tolist():
        if val in result:
            continue

        result.append(val)

    return jsonify(sorted(result))


if plugin_loaded("admin_panel"):
    from ckanext.ap_main.utils import ap_before_request
    from ckanext.ap_main.views.generics import ApConfigurationPageView

    charts_admin = Blueprint("charts_view_admin", __name__)
    charts_admin.before_request(ap_before_request)

    class ConfigClearCacheView(MethodView):
        def post(self):
            if "invalidate-all-cache" in tk.request.form:
                cache.invalidate_all_cache()

            if "invalidate-redis-cache" in tk.request.form:
                cache.drop_redis_cache()

            if "invalidate-file-cache" in tk.request.form:
                cache.drop_file_cache()

            tk.h.flash_success(tk._("Cache has been cleared"))

            return tk.h.redirect_to("charts_view_admin.config")

    charts_admin.add_url_rule(
        "/admin-panel/charts/clear-cache",
        view_func=ConfigClearCacheView.as_view("clear_cache"),
    )
    charts_admin.add_url_rule(
        "/admin-panel/charts/config",
        view_func=ApConfigurationPageView.as_view(
            "config",
            "charts_config",
            render_template="charts/config.html",
            page_title=tk._("Charts config"),
        ),
    )
