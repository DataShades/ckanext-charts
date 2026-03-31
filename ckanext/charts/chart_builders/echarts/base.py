from __future__ import annotations

from typing import Any

from ckanext.charts.chart_builders.base import BaseChartBuilder, BaseChartForm


class EChartsBuilder(BaseChartBuilder):
    @classmethod
    def get_supported_forms(cls) -> list[type[Any]]:
        from .bar import EChartsBarForm  # noqa: PLC0415
        from .line import EChartsLineForm  # noqa: PLC0415
        from .pie import EChartsPieForm  # noqa: PLC0415

        return [
            EChartsBarForm,
            EChartsLineForm,
            EChartsPieForm,
        ]


class EchartsFormBuilder(BaseChartForm):
    pass
