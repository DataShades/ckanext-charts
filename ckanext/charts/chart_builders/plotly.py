from __future__ import annotations

from typing import Any, cast

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

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
        return self.build_line_chart()

    def split_data_by_year(self) -> dict[str, Any]:
        """
        Prepare data for a line chart. It splits the data by year stated
        in the date format column which is used for x-axis.
        """
        self.df["date"] = pd.to_datetime(self.df[self.settings["x"]]).dt.date
        self.df = self.df[["date", self.settings["y"][0]]].set_index(["date"])
        self.df = self.df[[self.settings["y"][0]]].groupby(["date"]).mean()

        self.df.index = [pd.to_datetime(self.df.index).strftime("%m/%d"), pd.to_datetime(self.df.index).strftime("%Y")]
        self.df = self.df[self.settings["y"][0]].unstack()

        self.settings["y"] = self.df.columns.to_list()
        self.df["date_time"] = self.df.index

        return self

    def build_line_chart(self) -> Any:
        """
        Build a line chart. It supports multi columns for y-axis
        to display on the line chart.
        """
        if self.settings.get("split_data", False):
            self.split_data_by_year()

        fig = make_subplots(specs=[[{"secondary_y": True}]])

        fig.add_trace(
            go.Scatter(
                x=self.df[self.settings["x"]],
                y=self.df[self.settings["y"][0]],
                name=self.settings["y"][0],
            ),
            secondary_y=False,
        )

        if len(self.settings["y"]) > 1:
            for column in self.settings["y"][1:]:
                fig.add_trace(
                    go.Scatter(
                        x=self.df[self.settings["x"]],
                        y=self.df[column],
                        name=column,
                    ),
                    secondary_y=True,
                )

        if chart_title := self.settings.get("chart_title"):
            fig.update_layout(title_text=chart_title)

        if chart_xlabel := self.settings.get("chart_xlabel"):
            fig.update_xaxes(title_text=chart_xlabel)
        else:
            fig.update_xaxes(title_text=self.settings["x"])

        if chart_ylabel_left := self.settings.get("chart_ylabel_left"):
            fig.update_yaxes(title_text=chart_ylabel_left)
        else:
            fig.update_yaxes(title_text=self.settings["y"][0])

        if len(self.settings["y"]) > 1:
            if chart_ylabel_right := self.settings.get("chart_ylabel_right"):
                fig.update_yaxes(
                    secondary_y=True,
                    title_text=chart_ylabel_right,
                )
            else:
                fig.update_yaxes(
                    secondary_y=True,
                    title_text=self.settings["y"][1],
                )

        if self.settings.get("invert_x", False):
            fig.update_xaxes(autorange="reversed")

        if self.settings.get("invert_y", False):
            fig.update_yaxes(autorange="reversed")

        return fig.to_json()


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
            self.engine_details_field(),
            self.x_axis_field(columns),
            self.y_axis_field(columns),
            self.more_info_button_field(),
            self.log_x_field(),
            self.log_y_field(),
            self.sort_x_field(),
            self.sort_y_field(),
            self.color_field(columns),
            self.animation_frame_field(columns),
            self.opacity_field(),
            self.limit_field(),
            self.filter_field(columns),
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
            self.engine_details_field(),
            self.values_field(columns),
            self.names_field(columns),
            self.more_info_button_field(),
            self.opacity_field(),
            self.limit_field(),
            self.filter_field(columns),
        ]


class PlotlyHoriontalBarForm(PlotlyBarForm):
    name = "Horizontal Bar"
    builder = PlotlyHorizontalBarBuilder


class PlotlyLineForm(BasePlotlyForm):
    name = "Line"
    builder = PlotlyLineBuilder

    def plotly_y_multi_axis_field(
        self, columns: list[dict[str, str]], max_y: int = 0
    ) -> dict[str, Any]:
        """Plotly line chart supports multi columns for y-axis"""
        field = self.y_multi_axis_field(columns, max_y)

        field["help_text"] = (
            "Select the columns for the Y axis."
        )

        return field

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
            self.engine_details_field(),
            self.x_axis_field(columns),
            self.plotly_y_multi_axis_field(columns),
            self.more_info_button_field(),
            self.invert_x_field(),
            self.invert_y_field(),
            self.sort_x_field(),
            self.sort_y_field(),
            self.split_data_field(),
            self.limit_field(maximum=1000000),
            self.chart_title_field(),
            self.chart_xlabel_field(),
            self.chart_ylabel_left_field(),
            self.chart_ylabel_right_field(),
            self.filter_field(columns),
        ]


class PlotlyScatterForm(BasePlotlyForm):
    name = "Scatter"
    builder = PlotlyScatterBuilder

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
            self.engine_details_field(),
            self.x_axis_field(columns),
            self.y_axis_field(columns),
            self.more_info_button_field(),
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
            self.filter_field(columns),
        ]
