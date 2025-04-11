from __future__ import annotations

import json
from typing import Any

from ckanext.charts.chart_builders.echarts.base import (
    EChartsBuilder,
    EchartsFormBuilder,
)


class EChartsPieBuilder(EChartsBuilder):
    def to_json(self) -> str:
        options = {
            "tooltip": {"trigger": "item"},
            "toolbox": {
                "show": True,
                "orient": "horizontal",
                "left": "left",
                "bottom": "bottom",
                "feature": {
                    "dataView": {"readOnly": False},
                    "saveAsImage": {},
                },
            },
            "series": [
                {
                    "type": "pie",
                    "radius": [
                        self.settings["inner_radius"],
                        self.settings["outer_radius"],
                    ],
                    "data": self.df.apply(
                        lambda row: {
                            "value": self.convert_to_native_types(
                                row[self.settings["values"]]
                            ),
                            "name": self.convert_to_native_types(
                                row[self.settings["names"]]
                            ),
                        },
                        axis=1,
                    ).tolist(),
                }
            ],
        }

        if self.settings["rose_chart"]:
            options["series"][0]["roseType"] = "area"

        return json.dumps(options)


class EChartsPieForm(EchartsFormBuilder):
    name = "Pie"
    builder = EChartsPieBuilder

    def get_form_fields(self):
        columns = [{"value": col, "label": col} for col in self.get_all_column_names()]
        chart_types = [
            {"value": form.name, "label": form.name}
            for form in self.builder.get_supported_forms()
        ]

        return [
            self.title_field(),
            self.description_field(),
            self.engine_field(),
            self.type_field(chart_types),
            self.names_field(columns),
            self.values_field(columns),
            self.rose_chart_field(),
            self.inner_radius_field(),
            self.outer_radius_field(),
            self.limit_field(),
        ]

    def rose_chart_field(self) -> dict[str, Any]:
        return {
            "field_name": "rose_chart",
            "label": "Rose chart",
            "group": "Style",
            "help_text": "Render chart as a rose chart",
            "form_snippet": "chart_checkbox.html",
            "validators": [
                self.get_validator("chart_checkbox"),
                self.get_validator("default")(False),
                self.get_validator("boolean_validator"),
            ],
            "type": "bool",
            "default": False,
        }

    def inner_radius_field(self) -> dict[str, Any]:
        return {
            "field_name": "inner_radius",
            "label": "Inner radius",
            "group": "Style",
            "help_text": "Set the inner radius of the pie chart",
            "form_snippet": "chart_text.html",
            "input_type": "number",
            "validators": [
                self.get_validator("default")(0),
                self.get_validator("int_validator"),
                self.get_validator("limit_to_configured_maximum")("", 100),  # type: ignore
            ],
            "type": "int",
            "default": 0,
        }

    def outer_radius_field(self) -> dict[str, Any]:
        return {
            "field_name": "outer_radius",
            "label": "Outer radius",
            "group": "Style",
            "help_text": "Set the outer radius of the pie chart",
            "form_snippet": "chart_text.html",
            "input_type": "number",
            "validators": [
                self.get_validator("default")(200),
                self.get_validator("int_validator"),
            ],
            "type": "int",
            "default": 200,
        }
