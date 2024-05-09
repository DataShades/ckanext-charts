from __future__ import annotations

from flask import Blueprint
from flask.views import MethodView

import ckan.plugins.toolkit as tk
from ckan.logic import parse_params
from ckan.plugins import plugin_loaded

from ckanext.charts import cache, exception, utils

charts = Blueprint("charts_view", __name__)


@charts.route("/api/utils/charts/<resource_id>/update-chart")
def update_chart(resource_id: str):
    """TODO: update_chart and update_form are very similar, consider refactoring"""

    data = parse_params(tk.request.args)

    if "engine" not in data or "type" not in data:
        return tk.render("charts/snippets/unknown_chart.html")

    try:
        form_builder = utils.get_chart_form_builder(
            data["engine"],
            data["type"],
        )
    except exception.ChartTypeNotImplementedError:
        return tk.render("charts/snippets/unknown_chart.html")

    settings, _ = tk.navl_validate(
        data,
        form_builder(resource_id).get_validation_schema(),
        {},
    )

    try:
        return tk.render_snippet(
            f"charts/snippets/{settings['engine']}_chart.html",
            {"chart": utils.build_chart_for_resource(settings, resource_id)},
        )
    except exception.ChartTypeNotImplementedError:
        return tk.render("charts/snippets/unknown_chart.html")


@charts.route("/api/utils/charts/update-form")
def update_form():
    data = parse_params(tk.request.args)
    resource_id = tk.get_or_bust(data, "resource_id")

    if "engine" not in data or "type" not in data:
        return tk.render("charts/snippets/unknown_chart.html")

    try:
        form_builder = utils.get_chart_form_builder(
            data["engine"],
            data["type"],
        )
    except exception.ChartTypeNotImplementedError:
        return tk.render("charts/snippets/unknown_chart.html")

    builder = form_builder(resource_id)
    data, errors = tk.navl_validate(data, builder.get_validation_schema(), {})

    try:
        return tk.render_snippet(
            "charts/snippets/charts_form_fields.html",
            {
                "form_fields": builder.get_expanded_form_fields(),
                "resource_id": resource_id,
                "data": data,
                "errors": errors,
            },
        )
    except exception.ChartTypeNotImplementedError:
        return tk.render("charts/snippets/unknown_form.html")


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
