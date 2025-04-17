from __future__ import annotations

from typing import Any

from ckanext.charts.chart_builders.base import BaseChartBuilder, BaseChartForm


class EChartsBuilder(BaseChartBuilder):
    @classmethod
    def get_supported_forms(cls) -> list[type[Any]]:
        from .bar import EChartsBarForm
        from .line import EChartsLineForm
        from .pie import EChartsPieForm

        return [
            EChartsBarForm,
            EChartsLineForm,
            EChartsPieForm,
        ]


class EchartsFormBuilder(BaseChartForm):
    pass
