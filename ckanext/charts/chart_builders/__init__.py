from __future__ import annotations

from .base import BaseChartBuilder
from .chartjs import ChartJSBuilder
from .plotly import PlotlyBuilder, PlotlyBarForm


def get_chart_engines() -> dict[str, type[BaseChartBuilder]]:
    return {
        "plotly": PlotlyBuilder,
    }
