from __future__ import annotations

from typing import Any

import ckan.plugins as p
import ckan.plugins.toolkit as tk
from ckan import types
from ckan.common import CKANConfig

import ckanext.charts.utils as utils


@tk.blanket.helpers
@tk.blanket.blueprints
@tk.blanket.config_declarations
class ChartsViewPlugin(p.SingletonPlugin):
    p.implements(p.IConfigurer)
    p.implements(p.IResourceView)
    p.implements(p.IBlueprint)
    p.implements(p.ISignal)

    # IConfigurer

    def update_config(self, config_: CKANConfig):
        tk.add_template_directory(config_, "templates")
        tk.add_public_directory(config_, "public")
        tk.add_resource("assets", "charts")

    # IResourceView

    def info(self) -> dict[str, Any]:
        return {
            "name": "charts_view",
            "title": tk._("Chart"),
            "schema": utils.settings_schema(),
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
            data_dict["resource_view"], utils.settings_schema(), {}
        )

        settings = utils.settings_from_dict(data)

        return {
            "settings": settings,
            "column_options": utils.get_column_options(data_dict["resource"]["id"]),
            "resource_id": data_dict["resource"]["id"],
        }

    def view_template(self, context: types.Context, data_dict: dict[str, Any]) -> str:
        return "charts/charts_view.html"

    def form_template(self, context: types.Context, data_dict: dict[str, Any]) -> str:
        return "charts/charts_form.html"

    # ISignal

    def get_signal_subscriptions(self) -> types.SignalMapping:
        return {
            tk.signals.ckanext.signal("ap_main:collect_config_sections"): [
                self.collect_config_sections_subs
            ],
            tk.signals.ckanext.signal("ap_main:collect_config_schemas"): [
                self.collect_config_schemas_subs
            ],
        }

    @staticmethod
    def collect_config_sections_subs(sender: None):
        return {
            "name": "Charts",
            "configs": [
                {
                    "name": "Configuration",
                    "blueprint": "charts_view_admin.config",
                    "info": "Charts settings",
                },
            ],
        }

    @staticmethod
    def collect_config_schemas_subs(sender: None):
        return ["ckanext.charts:config_schema.yaml"]
