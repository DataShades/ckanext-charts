from __future__ import annotations

from typing import Any, cast

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from pandas.core.frame import DataFrame
from pandas.errors import ParserError
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
        return self.build_bar_chart()

    def build_bar_chart(self) -> Any:
        if self.settings.get("skip_null_values"):
            self.df = self.df[self.df[self.settings["y"]].notna()]

        fig = px.bar(
            data_frame = self.df,
            x = self.settings["x"],
            y = self.settings["y"],
        )

        fig.update_xaxes(
            type="category",
        )

        return fig.to_json()


class PlotlyHorizontalBarBuilder(PlotlyBuilder):
    def to_json(self) -> Any:
        return self.build_horizontal_bar_chart()

    def build_horizontal_bar_chart(self) -> Any:
        if self.settings.get("skip_null_values"):
            self.df = self.df[self.df[self.settings["y"]].notna()]

        fig = px.bar(
            data_frame = self.df,
            y = self.settings["x"],
            x = self.settings["y"],
            orientation="h",
        )

        fig.update_yaxes(
            type="category",
        )

        return fig.to_json()


class PlotlyPieBuilder(PlotlyBuilder):
    def to_json(self) -> Any:
        return px.pie(self.df, **self.settings).to_json()


class PlotlyLineBuilder(PlotlyBuilder):
    def to_json(self) -> Any:
        return self.build_line_chart()


    def _split_data_by_year(self) -> dict[str, Any]:
        """
        Prepare data for a line chart. It splits the data by year stated
        in the date format column which is used for x-axis.
        """
        if len(self.settings["years"]) > 1:
            self.df.drop_duplicates(subset=[self.settings["x"]], inplace=True)
            self.df = self.df[[self.settings["x"], self.settings["y"][0]]]
            self.df["year"] = pd.to_datetime(self.df[self.settings["x"]]).dt.year

            self.df = self.df.pivot(
                index=self.settings["x"],
                columns="year",
                values=self.settings["y"][0],
            )

            self.settings["y"] = self.df.columns.to_list()
            self.df[self.settings["x"]] = self.df.index
            self.df[self.settings["x"]] = pd.to_datetime(
                self.df[self.settings["x"]],
                unit="ns",
            ).dt.strftime("%m-%d %H:%M")

        return self


    def _skip_null_values(self, column: str) -> tuple[Any]:
        """
        Return values for x-axis and y-axis after removing missing values.
        """
        if self.settings.get("split_data") and len(self.settings["years"]) > 1:
            df = self.df.dropna(subset=column)
        else:
            df = self.df

        if self.settings.get("skip_null_values"):
            if self.settings.get("break_chart"):
                x, y = self._break_chart_by_missing_data(df, column)
            else:
                x = df[self.settings["x"]]
                y = df[column]
        else:
            x = df[self.settings["x"]]
            y = df[column].fillna(0)

        return x, y


    def _break_chart_by_missing_data(self, df: DataFrame, column: str) -> tuple[Any]:
        """
        Find gaps in date column and fill them with missing dates.
        """
        if len(self.settings["years"]) > 1:
            df["xaxis"] = df[self.settings["x"]]

            if self.settings.get("split_data"):
                df[self.settings["x"]] = df.index

            df["date"] = pd.to_datetime(df[self.settings["x"]]).dt.date

            all_dates = pd.date_range(
                start=df["date"].min(),
                end=df["date"].max(),
                unit="ns",
            ).date
            date_range_df = pd.DataFrame({"date": all_dates})
            df = pd.merge(date_range_df, df, on="date", how="left")

            x = df["xaxis"]
            y = df[column]
        else:
            x = df[self.settings["x"]]
            y = df[column]

        return x, y


    def build_line_chart(self) -> Any:
        """
        Build a line chart. It supports multi columns for y-axis
        to display on the line chart.
        """
        try:
            dates = pd.to_datetime(self.df[self.settings["x"]], unit="ns")
            self.settings["years"] = dates.dt.year.unique()
        except (ParserError, ValueError):
            self.settings["years"] = []

        if self.settings.get("split_data", False):
            self._split_data_by_year()

        x, y = self._skip_null_values(self.settings["y"][0])

        fig = make_subplots(specs=[[{"secondary_y": True}]])

        fig.add_trace(
            go.Scatter(
                x=x,
                y=y,
                name=self.settings["y"][0],
                connectgaps=not self.settings.get("break_chart"),
            ),
            secondary_y=False,
        )

        if len(self.settings["y"]) > 1:
            for column in self.settings["y"][1:]:
                x, y = self._skip_null_values(column)

                fig.add_trace(
                    go.Scatter(
                        x=x,
                        y=y,
                        name=column,
                        connectgaps=not self.settings.get("break_chart"),
                    ),
                    secondary_y=True,
                )

        if self.settings.get("split_data") and len(self.settings["years"]) > 1:
            fig.update_layout(xaxis={"categoryorder": "category ascending"})

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
        return self.build_scatter_chart()


    def build_scatter_chart(self) -> Any:
        self.df = self.df.fillna(0)

        if self.settings.get("skip_null_values"):
            self.df = self.df.loc[self.df[self.settings["y"]] != 0]

        size_column = self.df[self.settings.get("size", self.df.columns[0])]
        is_numeric = pd.api.types.is_numeric_dtype(size_column)
        if not is_numeric:
            raise exception.ChartBuildError(
                "The 'Size' source should be a field of numeric type.",
            )

        fig = px.scatter(
            data_frame = self.df,
            x = self.settings["x"],
            y = self.settings["y"],
            size = self.settings["size"],
            size_max = self.settings["size_max"],
        )

        fig.update_xaxes(
            type="category",
        )

        return fig.to_json()


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
            self.skip_null_values_field(),
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
            self.skip_null_values_field(),
            self.break_chart_field(),
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
            self.skip_null_values_field(),
            self.size_field(columns),
            self.size_max_field(),
            self.limit_field(),
            self.color_field(columns),
            self.animation_frame_field(columns),
            self.opacity_field(),
            self.filter_field(columns),
        ]
