from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from ckanext.charts.chart_builders.base import BaseChartBuilder, BaseChartForm
from ckanext.charts.exception import ChartBuildError


class ChartJsBuilder(BaseChartBuilder):
    @classmethod
    def get_supported_forms(cls) -> list[type[Any]]:
        return [
            ChartJSBarForm,
            ChartJSHorizontalBarForm,
            ChartJSLineForm,
            ChartJSPieForm,
            ChartJSDoughnutForm,
            ChartJSScatterForm,
            ChartJSBubbleForm,
            ChartJSRadarForm,
        ]


class ChartJSBarBuilder(ChartJsBuilder):
    def _prepare_data(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "type": "bar",
            "data": {"labels": self.get_unique_values(self.df[self.settings["x"]])},
            "options": self.settings,
        }

        data["options"].update(
            {
                "indexAxis": "x",
                "elements": {"bar": {"borderWidth": 1}},
                "plugins": {"legend": {"position": "top"}},
                "scales": {"y": {"beginAtZero": True}},
            }
        )

        datasets = []

        for field in self.settings["y"]:
            dataset_data = []

            for label in data["data"]["labels"]:
                try:
                    aggregate_value = int(
                        self.df[self.df[self.settings["x"]] == label][field].sum()
                    )
                except ValueError:
                    raise ChartBuildError(f"Column '{field}' is not numeric")

                dataset_data.append(aggregate_value)

            datasets.append(
                {
                    "label": field,
                    "data": dataset_data,
                }
            )

        data["data"]["datasets"] = datasets

        return data

    def to_json(self) -> str:
        return json.dumps(self._prepare_data())


class ChartJSBarForm(BaseChartForm):
    name = "Bar"
    builder = ChartJSBarBuilder

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
            self.limit_field(),
            self.filter_field(columns),
        ]


class ChartJSHorizontalBarBuilder(ChartJSBarBuilder):
    def to_json(self) -> str:
        data = self._prepare_data()

        data["options"]["indexAxis"] = "y"
        data["options"]["plugins"]["legend"]["position"] = "right"

        return json.dumps(data)


class ChartJSHorizontalBarForm(ChartJSBarForm):
    name = "Horizontal Bar"
    builder = ChartJSHorizontalBarBuilder


class ChartJSLineBuilder(ChartJsBuilder):
    def to_json(self) -> str:
        data: dict[str, Any] = {
            "type": "line",
            "data": {"labels": self.df[self.settings["x"]].to_list()},
            "options": self.settings,
        }

        datasets = []

        for field in self.settings["y"]:
            dataset: dict[str, Any] = {"label": field, "data": self.df[field].tolist()}

            datasets.append(dataset)

        data["data"]["datasets"] = datasets

        return json.dumps(data)


class ChartJSLineForm(BaseChartForm):
    name = "Line"
    builder = ChartJSLineBuilder

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
            self.filter_field(columns),
        ]


class ChartJSPieBuilder(ChartJsBuilder):
    chart_type = "pie"

    def to_json(self) -> str:
        data = {
            "type": self.chart_type,
            "data": {"labels": self.get_unique_values(self.df[self.settings["names"]])},
            "options": self.settings,
        }

        dataset_data = []

        for field in [self.settings["values"]]:
            for label in data["data"]["labels"]:
                dataset_data.append(
                    self.convert_to_native_types(
                        self.df[self.df[self.settings["names"]] == label][field].sum()
                    )
                )

        data["data"]["datasets"] = [
            {
                "label": field,
                "data": dataset_data,
            }
        ]

        return json.dumps(data)


class ChartJSPieForm(BaseChartForm):
    name = "Pie"
    builder = ChartJSPieBuilder

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
            self.filter_field(columns),
        ]


class ChartJSDoughnutBuilder(ChartJSPieBuilder):
    chart_type = "doughnut"


class ChartJSDoughnutForm(ChartJSPieForm):
    name = "Doughnut"
    builder = ChartJSDoughnutBuilder


class ChartJSScatterBuilder(ChartJsBuilder):
    def to_json(self) -> str:
        data: dict[str, Any] = {
            "type": "scatter",
            "data": {"datasets": []},
            "options": self.settings,
        }

        dataset_data = []

        for _, data_series in self.df.iterrows():
            for field in [self.settings["y"]]:
                dataset_data.append(
                    {
                        "x": self.convert_to_native_types(
                            data_series[self.settings["x"]]
                        ),
                        "y": self.convert_to_native_types(data_series[field]),
                    }
                )

        data["data"]["datasets"] = [
            {
                "label": self.settings["y"],
                "data": dataset_data,
            }
        ]

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
            self.filter_field(columns),
        ]


class ChartJSBubbleBuilder(ChartJSScatterBuilder):
    min_bubble_radius = 5

    def to_json(self) -> str:
        data: dict[str, Any] = {
            "type": "bubble",
            "data": {"datasets": []},
            "options": self.settings,
        }

        dataset_data = []
        max_size = self.df[self.settings["size"]].max()

        for _, data_series in self.df.iterrows():
            for field in [self.settings["y"]]:
                dataset_data.append(
                    {
                        "x": self.convert_to_native_types(
                            data_series[self.settings["x"]]
                        ),
                        "y": self.convert_to_native_types(data_series[field]),
                        "r": self._calculate_bubble_radius(data_series, max_size),
                    }
                )

        data["data"]["datasets"] = [
            {"label": self.settings["y"], "data": dataset_data},
        ]

        return json.dumps(data)

    def _calculate_bubble_radius(self, data_series: pd.Series, max_size: int) -> int:
        """Calculate bubble radius based on the size column"""
        size_column: str = self.settings["size"]

        # Handle cases where max_size is zero or NaN values are present
        # or the column is not numeric
        try:
            pd.to_numeric(max_size)
        except ValueError:
            raise ChartBuildError(f"Column '{size_column}' is not numeric")

        if max_size == 0 or np.isnan(max_size):
            bubble_radius = self.min_bubble_radius
        else:
            data_series_size = np.nan_to_num(data_series[size_column], nan=0)
            bubble_radius = (data_series_size / max_size) * 30

        if bubble_radius < self.min_bubble_radius:
            bubble_radius = self.min_bubble_radius

        return self.convert_to_native_types(bubble_radius)


class ChartJSBubbleForm(ChartJSScatterForm):
    name = "Bubble"
    builder = ChartJSBubbleBuilder

    def get_form_fields(self):
        """Almost same as scatter form, but with an additional field for bubble size"""
        columns = [{"value": col, "label": col} for col in self.df.columns]
        fields = super().get_form_fields()

        fields.append(self.size_field(columns))

        return fields


class ChartJSRadarBuilder(ChartJsBuilder):
    def to_json(self) -> str:
        data: dict[str, Any] = {
            "type": "radar",
            "data": {"labels": self.settings["values"]},
            "options": self.settings,
        }

        datasets = []

        for label in self.get_unique_values(self.df[self.settings["names"]]):
            dataset_data = []

            for value in self.settings["values"]:
                try:
                    dataset_data.append(
                        self.df[self.df[self.settings["names"]] == label][value].item()
                    )
                except ValueError:
                    # TODO: probably collision by name column, e.g two or more rows
                    # skip for now
                    continue

            datasets.append({"label": label, "data": dataset_data})

        data["data"]["datasets"] = datasets

        return json.dumps(data)


class ChartJSRadarForm(BaseChartForm):
    name = "Radar"
    builder = ChartJSRadarBuilder

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
            self.names_field(columns),
            self.values_multi_field(
                columns,
                help_text="Select 3 or more different categorical variables (dimensions)",
            ),
            self.limit_field(),
            self.filter_field(columns),
        ]
