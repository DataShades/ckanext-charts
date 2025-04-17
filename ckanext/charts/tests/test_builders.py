from __future__ import annotations

import json

import pytest

from ckanext.charts import exception, utils


@pytest.mark.ckan_config("ckan.plugins", "datastore charts_view")
@pytest.mark.usefixtures("clean_db", "with_plugins")
class TestPlotlyBuilder:
    """Tests for PlotlyBuilder"""

    def test_build_bar(self, data_frame):
        result = utils.build_chart_for_data(
            {
                "type": "Bar",
                "engine": "plotly",
                "x": "name",
                "y": "age",
            },
            data_frame,
        )

        assert result
        assert "data" in result
        assert "layout" in result

    def test_horizontal_bar(self, data_frame):
        result = utils.build_chart_for_data(
            {
                "type": "Horizontal Bar",
                "engine": "plotly",
                "x": "age",
                "y": "name",
            },
            data_frame,
        )

        assert result
        assert "data" in result
        assert "layout" in result

    def test_build_line(self, data_frame):
        result = utils.build_chart_for_data(
            {
                "type": "Line",
                "engine": "plotly",
                "x": "name",
                "y": ["age"],
            },
            data_frame,
        )

        assert result
        assert "data" in result
        assert "layout" in result

    def test_build_multi_y_line(self, data_frame):
        result = utils.build_chart_for_data(
            {
                "type": "Line",
                "engine": "plotly",
                "x": "name",
                "y": ["age", "surname"],
            },
            data_frame,
        )

        assert result
        assert "data" in result
        assert "layout" in result

        layout = json.loads(result)["layout"]

        assert "yaxis" in layout
        assert "yaxis2" in layout

    def test_build_scatter(self, data_frame):
        result = utils.build_chart_for_data(
            {
                "type": "Scatter",
                "engine": "plotly",
                "x": "name",
                "y": "age",
                "size": "age",
            },
            data_frame,
        )

        assert result
        assert "data" in result
        assert "layout" in result

    def test_build_scatter_no_size(self, data_frame):
        with pytest.raises(
            exception.ChartBuildError,
            match="The 'Size' source should be a field of numeric type",
        ):
            utils.build_chart_for_data(
                {
                    "type": "Scatter",
                    "engine": "plotly",
                    "x": "name",
                    "y": "age",
                },
                data_frame,
            )

    def test_build_pie(self, data_frame):
        result = utils.build_chart_for_data(
            {
                "type": "Pie",
                "engine": "plotly",
                "names": "name",
                "values": "age",
            },
            data_frame,
        )

        assert result
        assert "data" in result
        assert "layout" in result

    def test_build_choropleth(self, map_data_frame):
        result = utils.build_chart_for_data(
            {
                "type": "Choropleth",
                "engine": "plotly",
                "x": "country",
                "y": "population",
            },
            map_data_frame,
        )

        assert result
        assert "data" in result
        assert "layout" in result

    def test_not_supported_chart_type(self, data_frame):
        with pytest.raises(
            exception.ChartTypeNotImplementedError,
            match="Chart type not implemented",
        ):
            utils.build_chart_for_data(
                {"type": "Unknown", "engine": "plotly"},
                data_frame,
            )


@pytest.mark.ckan_config("ckan.plugins", "charts_view")
@pytest.mark.usefixtures("clean_db", "with_plugins")
class TestChartJsBuilder:
    """Tests for ChartJsBuilder"""

    def test_build_bar(self, data_frame):
        result = utils.build_chart_for_data(
            {
                "type": "Bar",
                "engine": "chartjs",
                "x": "name",
                "y": ["age"],
            },
            data_frame,
        )

        assert result
        assert "type" in result
        assert "data" in result
        assert "options" in result

    def test_horizontal_bar(self, data_frame):
        result = utils.build_chart_for_data(
            {
                "type": "Horizontal Bar",
                "engine": "chartjs",
                "x": "name",
                "y": ["age"],
            },
            data_frame,
        )

        assert result
        assert "type" in result
        assert "data" in result
        assert "options" in result

    def test_build_line(self, data_frame):
        result = utils.build_chart_for_data(
            {
                "type": "Line",
                "engine": "chartjs",
                "x": "name",
                "y": ["age"],
            },
            data_frame,
        )

        assert result
        assert "type" in result
        assert "data" in result
        assert "options" in result

    def test_build_multi_y_line(self, data_frame):
        result = utils.build_chart_for_data(
            {
                "type": "Line",
                "engine": "chartjs",
                "x": "name",
                "y": ["age", "surname"],
            },
            data_frame,
        )

        assert result
        assert "type" in result
        assert "data" in result
        assert "options" in result

    def test_build_pie(self, data_frame):
        result = utils.build_chart_for_data(
            {
                "type": "Pie",
                "engine": "chartjs",
                "names": "name",
                "values": "age",
            },
            data_frame,
        )

        assert result
        assert "type" in result
        assert "data" in result
        assert "options" in result

    def test_build_doughnut(self, data_frame):
        result = utils.build_chart_for_data(
            {
                "type": "Doughnut",
                "engine": "chartjs",
                "names": "name",
                "values": "age",
            },
            data_frame,
        )

        assert result
        assert "type" in result
        assert "data" in result
        assert "options" in result

    def test_scatter(self, data_frame):
        result = utils.build_chart_for_data(
            {
                "type": "Scatter",
                "engine": "chartjs",
                "x": "name",
                "y": "age",
            },
            data_frame,
        )

        assert result
        assert "type" in result
        assert "data" in result
        assert "options" in result

    def test_bubble(self, data_frame):
        result = utils.build_chart_for_data(
            {
                "type": "Bubble",
                "engine": "chartjs",
                "x": "name",
                "y": "age",
                "size": "age",
            },
            data_frame,
        )

        assert result
        assert "type" in result
        assert "data" in result
        assert "options" in result

    def test_bubble_not_numeric_column(self, data_frame):
        with pytest.raises(
            exception.ChartBuildError,
            match="Column 'surname' is not numeric",
        ):
            utils.build_chart_for_data(
                {
                    "type": "Bubble",
                    "engine": "chartjs",
                    "x": "name",
                    "y": "age",
                    "size": "surname",
                },
                data_frame,
            )

    def test_not_supported_chart_type(self, data_frame):
        with pytest.raises(
            exception.ChartTypeNotImplementedError,
            match="Chart type not implemented",
        ):
            utils.build_chart_for_data(
                {"type": "Unknown", "engine": "chartjs"},
                data_frame,
            )


@pytest.mark.ckan_config("ckan.plugins", "charts_view")
@pytest.mark.usefixtures("clean_db", "with_plugins")
class TestObservableBuilder:
    """Tests for ObservableBuilder"""

    def test_build_bar(self, data_frame):
        result = utils.build_chart_for_data(
            {
                "type": "Bar",
                "engine": "observable",
                "x": "name",
                "y": ["age"],
            },
            data_frame,
        )

        assert result
        assert "data" in result
        assert "plot" in result
        assert "settings" in result
        assert "bar" in result


    def test_horizontal_bar(self, data_frame):
        result = utils.build_chart_for_data(
            {
                "type": "Horizontal Bar",
                "engine": "observable",
                "x": "name",
                "y": ["age"],
            },
            data_frame,
        )

        assert result
        assert "data" in result
        assert "plot" in result
        assert "settings" in result
        assert "horizontal-bar" in result


    def test_build_line(self, data_frame):
        result = utils.build_chart_for_data(
            {
                "type": "Line",
                "engine": "observable",
                "x": "name",
                "y": ["age"],
            },
            data_frame,
        )

        assert result
        assert "data" in result
        assert "plot" in result
        assert "settings" in result
        assert "line" in result

    def test_build_multi_y_line(self, data_frame):
        result = utils.build_chart_for_data(
            {
                "type": "Line",
                "engine": "observable",
                "x": "name",
                "y": ["age", "surname"],
            },
            data_frame,
        )

        assert result
        assert "data" in result
        assert "plot" in result
        assert "settings" in result
        assert "line" in result

    def test_build_pie(self, data_frame):
        result = utils.build_chart_for_data(
            {
                "type": "Pie",
                "engine": "observable",
                "names": "name",
                "values": "age",
            },
            data_frame,
        )

        assert result
        assert "data" in result
        assert "settings" in result
        assert "pie" in result

    def test_build_scatter(self, data_frame):
        result = utils.build_chart_for_data(
            {
                "type": "Scatter",
                "engine": "observable",
                "x": "name",
                "y": "age",
                "size": "age",
            },
            data_frame,
        )

        assert result
        assert "data" in result
        assert "plot" in result
        assert "settings" in result
        assert "scatter" in result

    def test_not_supported_chart_type(self, data_frame):
        with pytest.raises(
            exception.ChartTypeNotImplementedError,
            match="Chart type not implemented",
        ):
            utils.build_chart_for_data(
                {"type": "Unknown", "engine": "observable"},
                data_frame,
            )
