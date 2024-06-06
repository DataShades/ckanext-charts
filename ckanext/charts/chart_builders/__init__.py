from __future__ import annotations

from .base import BaseChartBuilder
from .plotly import PlotlyBuilder, PlotlyBarForm
from .observable import ObservableBuilder
from .chartjs import ChartJSBarBuilder


DEFAULT_CHART_FORM = PlotlyBarForm


def get_chart_engines() -> dict[str, type[BaseChartBuilder]]:
    return {
        "plotly": PlotlyBuilder,
        "observable": ObservableBuilder,
        "chartjs": ChartJSBarBuilder,
    }
