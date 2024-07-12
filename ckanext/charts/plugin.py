from __future__ import annotations

from typing import Any
from os import path

from yaml import safe_load

import ckan.plugins as p
import ckan.plugins.toolkit as tk
import ckan.logic as logic
from ckan import types
from ckan.common import CKANConfig
from ckan.config.declaration import Declaration, Key

import ckanext.charts.config as conf
import ckanext.charts.utils as utils
import ckanext.charts.const as const
from ckanext.charts import cache, exception, fetchers, utils
from ckanext.charts.logic.schema import settings_schema
from ckanext.charts.chart_builders import DEFAULT_CHART_FORM


@tk.blanket.helpers
@tk.blanket.blueprints
@tk.blanket.validators
class ChartsViewPlugin(p.SingletonPlugin):
    p.implements(p.IConfigurer)
    p.implements(p.IConfigDeclaration)
    p.implements(p.IResourceView)
    p.implements(p.IBlueprint)
    p.implements(p.ISignal)
    p.implements(p.IResourceController, inherit=True)
    p.implements(p.IConfigurable)

    # IConfigurable

    def configure(self, config: CKANConfig) -> None:
        # Update redis keys TTL
        cache.update_redis_expiration(config[conf.CONF_REDIS_CACHE_TTL])

        # Remove expired file cache
        cache.remove_expired_file_cache()

    # IConfigurer

    def update_config(self, config_: CKANConfig):
        tk.add_template_directory(config_, "templates")
        tk.add_public_directory(config_, "public")
        tk.add_resource("assets", "charts")

    # IConfigDeclaration

    def declare_config_options(self, declaration: Declaration, key: Key):
        """Allow usage of custom validators by clearing the validators cache"""
        logic.clear_validators_cache()

        with open(path.dirname(__file__) + "/config_declaration.yaml") as file:
            data_dict = safe_load(file)

        return declaration.load_dict(data_dict)

    # IResourceView

    def info(self) -> dict[str, Any]:
        return {
            "name": "charts_view",
            "title": tk._("Chart"),
            "schema": settings_schema(),
            "icon": "chart-line",
            "iframed": False,
            "filterable": False,
            "preview_enabled": False,
            "requires_datastore": True,
        }

    def can_view(self, data_dict: dict[str, Any]) -> bool:
        return utils.can_view_be_viewed(data_dict)

    def setup_template_variables(
        self, context: types.Context, data_dict: dict[str, Any]
    ) -> dict[str, Any]:
        """
        The ``data_dict`` contains the following keys:

        :param resource_view: dict of the resource view being rendered
        :param resource: dict of the parent resource fields
        :param package: dict of the full parent dataset
        """

        data = {
            "settings": {},
            "resource_id": data_dict["resource"]["id"],
            "form_builder": DEFAULT_CHART_FORM,
        }

        data_dict["resource_view"]["resource_id"] = data_dict["resource"]["id"]
        context["_for_show"] = True  # type: ignore

        try:
            settings, _ = tk.navl_validate(
                data_dict["resource_view"], settings_schema(), context
            )
        except Exception as e:
            data["error_msg"] = e
            return data

        # view create or edit
        if "resource_view" in context or "for_view" in context:
            try:
                form_builder = utils.get_chart_form_builder(
                    settings["engine"],
                    settings["type"],
                )
            except exception.ChartTypeNotImplementedError:
                form_builder = DEFAULT_CHART_FORM

            data.update({"form_builder": form_builder})
        # view show
        else:
            try:
                chart = utils.build_chart_for_resource(
                    settings, data_dict["resource"]["id"]
                )
            except exception.ChartBuildError as e:
                data["error_msg"] = e
                return data

            data["chart"] = chart

        data.update({"settings": settings})

        return data

    def view_template(self, context: types.Context, data_dict: dict[str, Any]) -> str:
        return "charts/charts_view.html"

    def form_template(self, context: types.Context, data_dict: dict[str, Any]) -> str:
        return "charts/charts_form.html"

    # ISignal

    def get_signal_subscriptions(self) -> types.SignalMapping:
        return {
            tk.signals.ckanext.signal("ap_main:collect_config_sections"): [
                self.collect_config_sections_subs,
            ],
            tk.signals.ckanext.signal("ap_main:collect_config_schemas"): [
                self.collect_config_schemas_subs,
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
                fetchers.DatastoreDataFetcher(resource_dict["id"]).make_cache_key(),
            )

    # IResourceController

    def before_resource_delete(
        self,
        context: types.Context,
        resource: dict[str, Any],
        resources: list[dict[str, Any]],
    ) -> None:
        cache.invalidate_by_key(
            fetchers.DatastoreDataFetcher(resource["id"]).make_cache_key(),
        )


class ChartsBuilderViewPlugin(p.SingletonPlugin):
    p.implements(p.IResourceView)

    # IResourceView

    def info(self) -> dict[str, Any]:
        return {
            "name": "charts_builder_view",
            "title": tk._("Chart Builder"),
            "schema": {},
            "icon": "chart-area",
            "iframed": False,
            "filterable": False,
            "preview_enabled": False,
            "requires_datastore": True,
        }

    def can_view(self, data_dict: dict[str, Any]) -> bool:
        return utils.can_view_be_viewed(data_dict)

    def setup_template_variables(
        self, context: types.Context, data_dict: dict[str, Any]
    ) -> dict[str, Any]:
        form_builder = DEFAULT_CHART_FORM

        data = {
            "resource_id": data_dict["resource"]["id"],
            "settings": {
                "engine": "plotly",
                "type": "line",
                "limit": const.CHART_DEFAULT_ROW_LIMIT,
            },
            "form_builder": form_builder,
        }

        return data

    def view_template(self, context: types.Context, data_dict: dict[str, Any]) -> str:
        return "charts/charts_builder_view.html"

    def form_template(self, context: types.Context, data_dict: dict[str, Any]) -> str:
        return "charts/charts_builder_form.html"
