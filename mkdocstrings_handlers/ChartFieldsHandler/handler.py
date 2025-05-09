from __future__ import annotations

import os
from collections.abc import Mapping, MutableMapping
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

from mkdocstrings import BaseHandler, CollectorItem

from ckan.cli import CKANConfigLoader
from ckan.config.middleware import make_app

from ckanext.charts.utils import get_chart_form_builder

config_path = os.environ["CKAN_INI"]

if not os.path.exists(config_path):
    raise RuntimeError(f"CKAN config file not found: {config_path}")


class ChartFieldsHandler(BaseHandler):
    """Custom handler for documenting different chart types fields according to the
    form fields schema."""
    def collect(
        self, identifier: str, config: MutableMapping[str, Any],
    ) -> CollectorItem:
        if not os.environ.get("CHARTS_FIELDS"):
            return {}

        if "engine" not in config or "chart_type" not in config:
            return {}

        # init CKAN, because we're using helpers and validators in get_form_fields
        ckan_config = CKANConfigLoader(config_path).get_config()
        make_app(ckan_config)

        # Mock the SQLAlchemy inspector to simulate column fetching
        mock_inspector = MagicMock()
        mock_inspector.get_columns = MagicMock(return_value=[])

        # mock the fetcher, cause we don't have a resource to fetch data from
        mock = MagicMock()
        patcher = patch("ckanext.charts.fetchers.DatastoreDataFetcher", mock)
        patcher.start()
        mock.fetch_data.return_value = {}

        # Patch the inspector
        patcher_inspector = patch("sqlalchemy.inspect", return_value=mock_inspector)
        patcher_inspector.start()

        form_builder = get_chart_form_builder(config["engine"], config["chart_type"])(
            "xxx",
        )

        return {
            "fields": form_builder.get_form_fields(),
        }

    def render(self, data: CollectorItem, config: Mapping[str, Any]) -> str:
        if not data.get("fields"):
            return ""

        return self.env.get_template("fields.html").render(
            fields=data["fields"],
        )


def get_handler(**kwargs: Any) -> ChartFieldsHandler:
    return ChartFieldsHandler(handler="ChartFieldsHandler", theme=kwargs["theme"])


def get_templates_path() -> Path:
    return Path(__file__).parent / "templates"
