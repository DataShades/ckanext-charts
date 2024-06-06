from __future__ import annotations

import json
from typing import Any

from ckanext.charts.chart_builders.base import BaseChartBuilder, BaseChartForm


class ChartJsBuilder(BaseChartBuilder):
    @classmethod
    def get_supported_forms(cls) -> list[type[Any]]:
        return [ChartJSBarForm, ChartJSLineForm, ChartJSPieForm, ChartJSScatterForm]


class ChartJSBarBuilder(ChartJsBuilder):
    def to_json(self) -> str:
        data = {
            "type": "bar",
            "data": {"labels": self.df[self.settings["x"]].to_list()},
            "options": self.settings,
        }

        datasets = []

        for field in [self.settings["y"]]:
            dataset = {
                "label": field,
                "data": self.df[field].tolist(),
                # "backgroundColor": "rgba(75, 192, 192, 0.2)",
                # "borderColor": "rgba(75, 192, 192, 1)",
                # "borderWidth": 1,
            }

            datasets.append(dataset)

        data["data"]["datasets"] = datasets

        return json.dumps(data)


class ChartJSBarForm(BaseChartForm):
    name = "Bar"
    builder = ChartJSBarBuilder

    def fill_field(self, choices: list[dict[str, str]]) -> dict[str, str]:
        field = self.color_field(choices)
        field.update({"field_name": "fill", "label": "Fill"})

        return field

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
            self.sort_x_field(),
            self.sort_y_field(),
            self.limit_field(),
        ]


class ChartJSLineBuilder(ChartJsBuilder):
    def to_json(self) -> str:
        data = {
            "type": "line",
            "data": {"labels": self.df[self.settings["x"]].to_list()},
            "options": self.settings,
        }

        datasets = []

        for field in self.settings["y"]:
            dataset = {
                "label": field,
                "data": self.df[field].tolist(),
                # "backgroundColor": "rgba(75, 192, 192, 0.2)",
                # "borderColor": "rgba(75, 192, 192, 1)",
                # "borderWidth": 1,
            }

            datasets.append(dataset)

        data["data"]["datasets"] = datasets

        return json.dumps(data)


class ChartJSLineForm(BaseChartForm):
    name = "Line"
    builder = ChartJSLineBuilder

    def fill_field(self, choices: list[dict[str, str]]) -> dict[str, str]:
        field = self.color_field(choices)
        field.update({"field_name": "fill", "label": "Fill"})

        return field

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
            self.sort_x_field(),
            self.sort_y_field(),
            self.limit_field(),
        ]


class ChartJSPieBuilder(ChartJsBuilder):
    def to_json(self) -> str:
        data = {
            "type": "pie",
            "data": {"labels": self.df[self.settings["names"]].to_list()},
            "options": self.settings,
        }

        datasets = []

        for field in [self.settings["values"]]:
            dataset = {"label": field, "data": self.df[field].tolist()}

            datasets.append(dataset)

        data["data"]["datasets"] = datasets

        return json.dumps(data)


class ChartJSPieForm(BaseChartForm):
    name = "Pie"
    builder = ChartJSPieBuilder

    def fill_field(self, choices: list[dict[str, str]]) -> dict[str, str]:
        field = self.color_field(choices)
        field.update({"field_name": "fill", "label": "Fill"})

        return field

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
            self.values_field(columns),
            self.names_field(columns),
            self.limit_field(),
        ]


class ChartJSScatterBuilder(ChartJsBuilder):
    def to_json(self) -> str:
        data = {
            "type": "scatter",
            "data": {"labels": self.df[self.settings["x"]].to_list()},
            "options": self.settings,
        }

        data["data"]["datasets"] = [{
            "label": 'Scatter Dataset',
            "data": [
                {"x": -10, "y": 0},
                {"x": 0, "y": 10},
                {"x": 10, "y": 5},
                {"x": 0.5, "y": 5.5},
            ]
        }]

        return json.dumps(data)

class ChartJSScatterForm(BaseChartForm):
    name = "Scatter"
    builder = ChartJSScatterBuilder

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
            self.sort_x_field(),
            self.sort_y_field(),
            self.limit_field(),
        ]
