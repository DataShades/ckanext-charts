from __future__ import annotations

from plotly.graph_objects import Figure
from typing import Any

from ckanext.charts.chart_builders.base import BaseChartBuilder, BaseChartForm


class PlotlyBuilder(BaseChartBuilder):
    """Base class for Plotly chart builders.

    Defines supported chart types for Plotly engine.
    """

    DEFAULT_NAN_FILL_VALUE = 0
    YEAR_DATETIME_FORMAT = "%Y"
    DATETIME_TICKS_FORMAT = "%m-%d %H:%M"
    ISO_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S"

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

    def _set_chart_global_settings(
        self, fig: Figure) -> None:
        """Set chart's global settings and plot configs.

        Args:
            fig: plotly graph object Figure

        Returns:
            Updated plotly graph object
        """
        if chart_title := self.settings.get("chart_title"):
            fig.update_layout(title_text=chart_title)

        if x_axis_label := self.settings.get("x_axis_label"):
            fig.update_xaxes(title_text=x_axis_label)
        elif isinstance(self.settings["x"], list):
            fig.update_yaxes(title_text=self.settings["x"][0])
        else:
            fig.update_xaxes(title_text=self.settings["x"])

        if y_axis_label := self.settings.get("y_axis_label"):
            fig.update_yaxes(title_text=y_axis_label)
        elif isinstance(self.settings["y"], list):
            fig.update_yaxes(title_text=self.settings["y"][0])
        else:
            fig.update_yaxes(title_text=self.settings["y"])

        if self.settings.get("invert_x", False):
            fig.update_xaxes(autorange="reversed")

        if self.settings.get("invert_y", False):
            fig.update_yaxes(autorange="reversed")


class BasePlotlyForm(BaseChartForm):
    pass
