from __future__ import annotations

import json
from typing import Any

from ckanext.charts.chart_builders.echarts.base import (
    EChartsBuilder,
    EchartsFormBuilder,
)


class EChartsLineBuilder(EChartsBuilder):
    def to_json(self) -> str:
        options = {
            "xAxis": {
                "type": "category",
                "data": self.df[self.settings["x"]].tolist(),
            },
            "yAxis": {"type": "value"},
            "series": [],
        }

        for column in self.settings["y"]:
            data = {"type": "line", "data": self.df[column].tolist()}

            # render chart as an area chart
            if self.settings["area_chart"]:
                data["areaStyle"] = {"opacity": 0.5}

            # smooth the line
            if self.settings["smooth"]:
                data["smooth"] = True

            # use horizontal and vertical lines to connect points
            if self.settings["step"] != "normal":
                data["step"] = self.settings["step"]

            options["series"].append(data)

        return json.dumps(options)


class EChartsLineForm(EchartsFormBuilder):
    name = "Line"
    builder = EChartsLineBuilder

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
            self.y_multi_axis_field(columns),
            self.step_field(),
            self.area_chart_field(),
            self.smooth_field(),
            self.limit_field(),
        ]

    def area_chart_field(self) -> dict[str, Any]:
        return {
            "field_name": "area_chart",
            "label": "Area chart",
            "group": "Style",
            "help_text": "Render chart as an area chart",
            "form_snippet": "chart_checkbox.html",
            "validators": [
                self.get_validator("chart_checkbox"),
                self.get_validator("default")(False),
                self.get_validator("boolean_validator"),
            ],
            "type": "bool",
            "default": False,
        }

    def smooth_field(self) -> dict[str, Any]:
        return {
            "field_name": "smooth",
            "label": "Smooth",
            "group": "Style",
            "help_text": "Smooth the line",
            "form_snippet": "chart_checkbox.html",
            "validators": [
                self.get_validator("chart_checkbox"),
                self.get_validator("default")(False),
                self.get_validator("boolean_validator"),
            ],
            "type": "bool",
            "default": False,
        }

    def step_field(self) -> dict[str, Any]:
        return {
            "field_name": "step",
            "label": "Step",
            "group": "Style",
            "form_snippet": "chart_select.html",
            "help_text": "Render chart as a step chart",
            "choices": [
                {"value": "normal", "label": "Normal"},
                {"value": "start", "label": "Start"},
                {"value": "middle", "label": "Middle"},
                {"value": "end", "label": "End"},
            ],
            "validators": [
                self.get_validator("default")("normal"),
                self.get_validator("unicode_safe"),
            ],
            "required": True,
            "default": "Normal",
            "type": "str",
        }
