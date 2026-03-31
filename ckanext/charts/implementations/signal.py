from __future__ import annotations

from typing import Any

import ckan.plugins as p
import ckan.plugins.toolkit as tk
from ckan import types


class SignalController(p.SingletonPlugin):
    p.implements(p.ISignal)

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
    def collect_config_sections_subs(sender: None) -> Any:
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
    def collect_config_schemas_subs(sender: None) -> list[str]:
        return ["ckanext.charts:config_schema.yaml"]
