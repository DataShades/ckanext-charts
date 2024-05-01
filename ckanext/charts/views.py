from __future__ import annotations

from flask import Blueprint
from flask.views import MethodView

import ckan.plugins.toolkit as tk
from ckan.logic import parse_params
from ckan.plugins import plugin_loaded

import ckanext.charts.utils as utils
import ckanext.charts.cache as cache

charts = Blueprint("charts_view", __name__)


@charts.route("/api/utils/charts/<resource_id>/view-form")
def form(resource_id):
    data, _ = tk.navl_validate(
        parse_params(tk.request.args), utils.settings_schema(), {}
    )

    settings = utils.settings_from_dict(data)

    return tk.render_snippet(
        "charts/charts_form.html",
        {
            "settings": settings,
            "column_options": utils.get_column_options(resource_id),
            "resource_id": resource_id,
        },
    )


if plugin_loaded("admin_panel"):
    from ckanext.ap_main.utils import ap_before_request
    from ckanext.ap_main.views.generics import ApConfigurationPageView

    charts_admin = Blueprint("charts_view_admin", __name__)
    charts_admin.before_request(ap_before_request)

    class ConfigClearCacheView(MethodView):
        def post(self):
            if "invalidate-cache" in tk.request.form:
                cache.invalidate_cache()

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
