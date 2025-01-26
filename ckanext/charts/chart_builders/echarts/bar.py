from __future__ import annotations

import json

from ckanext.charts.chart_builders.echarts.base import (
    EChartsBuilder,
    EchartsFormBuilder,
)


class EChartsBarBuilder(EChartsBuilder):
    def to_json(self) -> str:
        options = {
            "xAxis": {
                "data": self.df[self.settings["x"]].tolist(),
            },
            "yAxis": {},
            "series": [
                {
                    "type": "bar",
                    "data": self.df[self.settings["y"]].tolist(),
                }
            ],
        }
        return json.dumps(options)


class EChartsBarForm(EchartsFormBuilder):
    name = "Bar"
    builder = EChartsBarBuilder

    def get_form_fields(self):
        columns = [{"value": col, "label": col} for col in self.df.columns]
        chart_types = [
            {"value": form.name, "label": form.name}
            for form in self.builder.get_supported_forms()
        ]

        return [
            self.title_field(),
            self.description_field(),
            self.engine_field(),
            self.type_field(chart_types),
            self.x_axis_field(columns),
            self.y_axis_field(columns),
            self.limit_field(),
        ]
