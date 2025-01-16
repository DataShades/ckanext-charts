from __future__ import annotations

from typing import Any

from ckanext.charts.chart_builders.base import BaseChartBuilder, BaseChartForm


class PlotlyBuilder(BaseChartBuilder):
    """Base class for Plotly chart builders.

    Defines supported chart types for Plotly engine.
    """

    DEFAULT_NAN_FILL_VALUE = 0

    @classmethod
    def get_supported_forms(cls) -> list[type[Any]]:
        from ckanext.charts.chart_builders.plotly.choropleth import PlotlyChoroplethForm
        from ckanext.charts.chart_builders.plotly.line import PlotlyLineForm
        from ckanext.charts.chart_builders.plotly.pie import PlotlyPieForm
        from ckanext.charts.chart_builders.plotly.scatter import PlotlyScatterForm
        from ckanext.charts.chart_builders.plotly.bar import (
            PlotlyBarForm,
            PlotlyHorizontalBarForm,
        )

        return [
            PlotlyBarForm,
            PlotlyHorizontalBarForm,
            PlotlyPieForm,
            PlotlyLineForm,
            PlotlyScatterForm,
            PlotlyChoroplethForm,
        ]


class BasePlotlyForm(BaseChartForm):
    pass
