from __future__ import annotations

from .base import BaseChartBuilder
from .chartjs import ChartJSBarBuilder
from .observable import ObservableBuilder
from .plotly import PlotlyBuilder
from .plotly.bar import PlotlyBarForm
from .echarts import EChartsBuilder

DEFAULT_CHART_FORM = PlotlyBarForm


def get_chart_engines() -> dict[str, type[BaseChartBuilder]]:
    return {
        "plotly": PlotlyBuilder,
        "observable": ObservableBuilder,
        "chartjs": ChartJSBarBuilder,
        "echarts": EChartsBuilder
    }
