from __future__ import annotations

from math import log
from typing import Any

import ckan.types as types
import ckan.plugins as p
import ckan.plugins.toolkit as tk
from ckan import types
from ckan.common import CKANConfig

from ckanext.charts import fetchers
import ckanext.charts.cache as cache
import ckanext.charts.utils as utils
import ckanext.charts.config as conf


@tk.blanket.helpers
@tk.blanket.blueprints
@tk.blanket.config_declarations
class ChartsViewPlugin(p.SingletonPlugin):
    p.implements(p.IConfigurer)
    p.implements(p.IResourceView)
    p.implements(p.IBlueprint)
    p.implements(p.ISignal)
    p.implements(p.IResourceController, inherit=True)
    p.implements(p.IConfigurable)

    # IConfigurable

    def configure(self, config: "CKANConfig") -> None:
        # Update redis keys TTL
        cache.update_redis_expiration(config[conf.CONF_REDIS_CACHE_TTL])

        # Remove expired file cache
        cache.remove_expired_file_cache()

        return

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
        if data_dict["resource"].get("datastore_active"):
            return True

        # TODO: Add support for XML, XLS, XLSX, and other formats tabular data?
        # if data_dict["resource"]["format"].lower() == "xml":
        #     return True

        return False

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

    # IXloader & IDataPusher

    if p.plugin_loaded("xloader") or p.plugin_loaded("datapusher"):
        if p.plugin_loaded("xloader"):
            from ckanext.xloader.interfaces import IXloader

            pusher_interface = IXloader
        else:
            from ckanext.datapusher.interfaces import IDataPusher

            pusher_interface = IDataPusher

        p.implements(pusher_interface, inherit=True)

        def after_upload(
            self,
            context: types.Context,
            resource_dict: dict[str, Any],
            dataset_dict: dict[str, Any],
        ) -> None:
            """Invalidate cache after upload to DataStore"""
            cache.invalidate_by_key(
                fetchers.DatastoreDataFetcher(resource_dict["id"]).make_cache_key()
            )

    # IResourceController

    def before_resource_delete(
        self,
        context: types.Context,
        resource: dict[str, Any],
        resources: list[dict[str, Any]],
    ) -> None:
        cache.invalidate_by_key(
            fetchers.DatastoreDataFetcher(resource["id"]).make_cache_key()
        )


# 1. show cache Sized
# 2. use configurer
