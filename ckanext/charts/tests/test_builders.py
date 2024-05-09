from __future__ import annotations

import json

import pytest

import ckanext.charts.chart_builders as builders


@pytest.mark.ckan_config("ckan.plugins", "datastore")
@pytest.mark.usefixtures("clean_db", "with_plugins")
class TestPlotlyBuilder:
    """Tests for PlotlyBuilder"""

    def test_bar_as_html(self, data_frame):
        builder = builders.PlotlyBuilder(
            data_frame,
            {"x": "name", "y": "age", "chart_type": "bar"},
        )

        result = builder.to_html()

        assert "Alice" in result
        assert "</html>" in result
        assert isinstance(result, str)

    def test_bar_as_json(self, data_frame):
        builder = builders.PlotlyBuilder(
            data_frame,
            {"x": "name", "y": "age", "chart_type": "bar"},
        )

        result = json.loads(builder.to_json())

        assert "data" in result
        assert "layout" in result

    def test_bar_with_color(self, data_frame):
        builder = builders.PlotlyBuilder(
            data_frame,
            {"x": "name", "y": "age", "chart_type": "bar", "color": "name"},
        )

        assert json.loads(builder.to_json())

    def test_bar_with_missing_color_column(self, data_frame):
        with pytest.raises(
            ValueError,
            match="Column wrong_column does not exist in the dataframe",
        ):
            builders.PlotlyBuilder(
                data_frame,
                {"x": "name", "y": "age", "chart_type": "bar", "color": "wrong_column"},
            )

    def test_columns(self, data_frame):
        builder = builders.PlotlyBuilder(data_frame, {})

        result = builder.columns()

        assert result == ["name", "age"]
