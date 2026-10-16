"""Saved charts must remain editable after resource columns change."""
from unittest.mock import Mock

import pandas as pd
import pytest

from ckanext.charts import utils
from ckanext.charts.chart_builders import base
from ckanext.charts.exception import ChartBuildError, DataFetchError


def test_form_loads_current_columns_without_saved_settings(monkeypatch):
    class Form(base.BaseChartForm):
        def get_form_fields(self):
            return []

    current_data = pd.DataFrame({"CANTIDAD_PROCESO": [3]})
    fetcher = Mock()
    fetcher.return_value.fetch_data.return_value = current_data
    monkeypatch.setattr(base.fetchers, "DatastoreDataFetcher", fetcher)

    form = Form(
        "resource-id",
        resource_view_id="saved-view",
        settings={"y": "CANTIDAD_PROCESOS", "filter": "old-column:value"},
    )

    fetcher.assert_called_once_with("resource-id")
    assert list(form.df.columns) == ["CANTIDAD_PROCESO"]


def test_invalid_saved_chart_returns_handled_error(monkeypatch):
    fetcher = Mock()
    fetcher.return_value.fetch_data.side_effect = DataFetchError("SQL details")
    monkeypatch.setattr(utils, "DatastoreDataFetcher", fetcher)
    monkeypatch.setattr(utils.tk, "_", lambda message: message)
    build = Mock()
    monkeypatch.setattr(utils, "_build_chart", build)

    with pytest.raises(ChartBuildError, match="Edit the chart") as error:
        utils.build_chart_for_resource({"y": "CANTIDAD_PROCESOS"}, "resource-id")

    assert "SQL details" not in str(error.value)
    build.assert_not_called()
