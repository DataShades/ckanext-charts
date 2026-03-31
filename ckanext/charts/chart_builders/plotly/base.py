from __future__ import annotations

from typing import Any

from plotly.graph_objects import Figure

from ckanext.charts.chart_builders.base import BaseChartBuilder, BaseChartForm
from ckanext.charts.const import (
    DEFAULT_NAN_FILL_VALUE,
    DATETIME_FORMAT_ISO8601,
    DATETIME_FORMAT_TICKS,
    DATETIME_FORMAT_YEAR,
)


class PlotlyBuilder(BaseChartBuilder):
    """Base class for Plotly chart builders.

    Defines supported chart types for Plotly engine.
    """

    DEFAULT_NAN_FILL_VALUE = DEFAULT_NAN_FILL_VALUE
    YEAR_DATETIME_FORMAT = DATETIME_FORMAT_YEAR
    DATETIME_TICKS_FORMAT = DATETIME_FORMAT_TICKS
    ISO_DATETIME_FORMAT = DATETIME_FORMAT_ISO8601

    @classmethod
    def get_supported_forms(cls) -> list[type[Any]]:
        from ckanext.charts.chart_builders.plotly.bar import (  # noqa: PLC0415
            PlotlyBarForm,
            PlotlyHorizontalBarForm,
        )
        from ckanext.charts.chart_builders.plotly.choropleth import PlotlyChoroplethForm  # noqa: PLC0415
        from ckanext.charts.chart_builders.plotly.line import PlotlyLineForm  # noqa: PLC0415
        from ckanext.charts.chart_builders.plotly.pie import PlotlyPieForm  # noqa: PLC0415
        from ckanext.charts.chart_builders.plotly.scatter import PlotlyScatterForm  # noqa: PLC0415

        return [
            PlotlyBarForm,
            PlotlyHorizontalBarForm,
            PlotlyPieForm,
            PlotlyLineForm,
            PlotlyScatterForm,
            PlotlyChoroplethForm,
        ]

    def _set_chart_global_settings(self, fig: Figure) -> None:
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
