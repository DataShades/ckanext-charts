from __future__ import annotations

from typing import Any

from flask.blueprints import Blueprint

import ckan.plugins as p
import ckan.plugins.toolkit as tk
from ckan import types
from ckan.common import CKANConfig
from ckan.logic import parse_params


@tk.blanket.helpers
class ChartsPlugin(p.SingletonPlugin):
    p.implements(p.IConfigurer)

    # IConfigurer

    def update_config(self, config_: CKANConfig):
        tk.add_template_directory(config_, "templates")
        tk.add_public_directory(config_, "public")
        tk.add_resource("assets", "charts")


class ChartsViewPlugin(p.SingletonPlugin):
    p.implements(p.IResourceView)
    p.implements(p.IBlueprint)

    def get_blueprint(self):
        return [charts_view_bp]

    def info(self) -> dict[str, Any]:
        return {
            "name": "charts_view",
            "title": tk._("Chart"),
            "schema": settings_schema(),
            "icon": "chart-line",
            "iframed": False,
            "filterable": False,
            "preview_enabled": False,
        }

    def can_view(self, data_dict: dict[str, Any]) -> bool:
        return data_dict["resource"].get("datastore_active")

    def setup_template_variables(
        self, context: types.Context, data_dict: dict[str, Any]
    ) -> dict[str, Any]:
        """
        The ``data_dict`` contains the following keys:

        :param resource_view: dict of the resource view being rendered
        :param resource: dict of the parent resource fields
        :param package: dict of the full parent dataset
        """
        # this function receives non-valid view in case of validation error.
        data, _errors = tk.navl_validate(
            data_dict["resource_view"], settings_schema(), {}
        )

        settings = _settings_from_dict(data)

        return {
            "settings": settings,
            "column_options": _get_column_options(data_dict["resource"]["id"]),
            "resource_id": data_dict["resource"]["id"],
        }

    def view_template(self, context: types.Context, data_dict: dict[str, Any]) -> str:
        """
        :param resource_view: dict of the resource view being rendered
        :param resource: dict of the parent resource fields
        :param package: dict of the full parent dataset

        :returns: the location of the view template.
        """
        return "charts/charts_view.html"

    def form_template(self, context: types.Context, data_dict: dict[str, Any]) -> str:
        """
        :param resource_view: dict of the resource view being rendered
        :param resource: dict of the parent resource fields
        :param package: dict of the full parent dataset

        :returns: the location of the edit view form template.
        """
        return "charts/charts_form.html"


def settings_schema() -> dict[str, Any]:
    v = tk.get_validator
    return {
        # "filter_value": [v("ignore_missing")],
        # "filter_fields": [v("ignore_missing")],
        "engine": [v("default")("plotly"), v("unicode_safe")],
        "type": [v("ignore_empty"), v("unicode_safe")],
        "x": [v("ignore_empty"), v("unicode_safe")],
        "y": [v("ignore_empty"), v("unicode_safe")],
        "color": [v("ignore_empty"), v("unicode_safe")],
        "query": [v("ignore_empty"), v("unicode_safe")],
        "hover_name": [v("ignore_empty"), v("unicode_safe")],
        "size": [v("ignore_empty"), v("unicode_safe")],
        "size_max": [v("ignore_empty"), v("int_validator")],
        "animation_frame": [v("ignore_empty"), v("unicode_safe")],
        "limit": [
            v("default")(100),
            v("int_validator"),
            v("limit_to_configured_maximum")("", 10_000),
        ],
        "log_x": [v("boolean_validator")],
        "log_y": [v("boolean_validator")],
        "__extras": [v("ignore")],
    }


charts_view_bp = Blueprint("charts_view", __name__)


@charts_view_bp.route("/api/utils/charts/<resource_id>/view-form")
def form(resource_id):
    data, _errors = tk.navl_validate(
        parse_params(tk.request.args), settings_schema(), {}
    )

    settings = _settings_from_dict(data)

    return tk.render_snippet(
        "charts/charts_form.html",
        {
            "settings": settings,
            "column_options": _get_column_options(resource_id),
            "resource_id": resource_id,
        },
    )


def _settings_from_dict(data: dict[str, Any]):
    attrs = [
        "engine",
        "type",
        "x",
        "y",
        "log_x",
        "log_y",
        "color",
        "query",
        "hover_name",
        "size",
        "size_max",
        "limit",
        "animation_frame",
    ]
    settings = {k: data.get(k, None) for k in attrs}

    if not settings["engine"]:
        settings["engine"] = "plotly"
    return settings


def _get_column_options(resource_id: str):
    result = tk.get_action("datastore_search")(
        {}, {"resource_id": resource_id, "limit": 0}
    )
    return [
        {"text": f["id"], "value": f["id"]}
        for f in result["fields"]
        if f["id"] != "_id"
    ]
