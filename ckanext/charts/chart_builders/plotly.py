from __future__ import annotations

from typing import Any, cast

import pandas as pd
import plotly.express as px


from ckanext.charts import exception
from ckanext.charts.chart_builders.base import BaseChartBuilder, BaseChartForm


class PlotlyBuilder(BaseChartBuilder):
    @classmethod
    def get_supported_forms(cls) -> list[type[Any]]:
        return [
            PlotlyBarForm,
            PlotlyHoriontalBarForm,
            PlotlyPieForm,
            PlotlyLineForm,
            PlotlyScatterForm,
        ]


class PlotlyBarBuilder(PlotlyBuilder):
    def to_json(self) -> str:
        return cast(str, px.bar(self.df, **self.settings).to_json())


class PlotlyHorizontalBarBuilder(PlotlyBuilder):
    def __init__(self, df: pd.DataFrame, settings: dict[str, Any]) -> None:
        super().__init__(df, settings)
        self.settings["orientation"] = "h"

    def to_json(self) -> Any:
        return px.bar(self.df, **self.settings).to_json()


class PlotlyPieBuilder(PlotlyBuilder):
    def to_json(self) -> Any:
        return px.pie(self.df, **self.settings).to_json()


class PlotlyLineBuilder(PlotlyBuilder):
    def to_json(self) -> Any:
        return px.line(self.df, **self.settings).to_json()


class PlotlyScatterBuilder(PlotlyBuilder):
    def to_json(self) -> Any:
        try:
            return px.scatter(self.df, **self.settings).to_json()
        except Exception as e:
            raise exception.ChartBuildError(f"Error building the chart: {e}")


class BasePlotlyForm(BaseChartForm):
    pass


class PlotlyBarForm(BasePlotlyForm):
    name = "Bar"
    builder = PlotlyBarBuilder

    def get_form_fields(self):
        """Get the form fields for the Plotly bar chart."""
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
            self.query_field(),
            self.x_axis_field(columns),
            self.y_axis_field(columns),
            self.log_x_field(),
            self.log_y_field(),
            self.sort_x_field(),
            self.sort_y_field(),
            self.color_field(columns),
            self.animation_frame_field(columns),
            self.opacity_field(),
            self.limit_field(),
        ]


class PlotlyPieForm(BasePlotlyForm):
    name = "Pie"
    builder = PlotlyPieBuilder

    def get_form_fields(self):
        """Get the form fields for the Plotly pie chart."""
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
            self.query_field(),
            self.values_field(columns),
            self.names_field(columns),
            self.opacity_field(),
            self.limit_field(),
        ]


class PlotlyHoriontalBarForm(PlotlyBarForm):
    name = "Horizontal Bar"
    builder = PlotlyHorizontalBarBuilder


class PlotlyLineForm(BasePlotlyForm):
    name = "Line"
    builder = PlotlyLineBuilder

    def get_form_fields(self):
        """Get the form fields for the Plotly line chart."""
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
            self.query_field(),
            self.x_axis_field(columns),
            self.y_axis_field(columns),
            self.log_x_field(),
            self.log_y_field(),
            self.sort_x_field(),
            self.sort_y_field(),
            self.color_field(columns),
            self.animation_frame_field(columns),
            self.limit_field(),
        ]


class PlotlyScatterForm(BasePlotlyForm):
    name = "Scatter"
    builder = PlotlyScatterBuilder

    def size_field(self, choices: list[dict[str, str]]) -> dict[str, Any]:
        field = self.column_field(choices)
        field.update({"field_name": "size", "label": "Size", "group": "Structure"})

        return field

    def size_max_field(self) -> dict[str, Any]:
        return {
            "field_name": "size_max",
            "label": "Size Max",
            "form_snippet": "chart_range.html",
            "min": 0,
            "max": 100,
            "step": 1,
            "group": "Structure",
            "validators": [
                self.get_validator("default")(100),
                self.get_validator("int_validator"),
            ],
        }

    def get_form_fields(self):
        """Get the form fields for the Plotly scatter chart."""
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
            self.query_field(),
            self.x_axis_field(columns),
            self.y_axis_field(columns),
            self.log_x_field(),
            self.log_y_field(),
            self.sort_x_field(),
            self.sort_y_field(),
            self.size_field(columns),
            self.size_max_field(),
            self.limit_field(),
            self.color_field(columns),
            self.animation_frame_field(columns),
            self.opacity_field(),
        ]
