from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from pandas.core.frame import DataFrame
from pandas.errors import ParserError

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

    def _create_zoom_and_title_options(self, options: dict[str, Any]) -> dict[str, Any]:
        """Add zoom and title plugin options to the provided options dictionary"""
        if "plugins" not in options:
            options["plugins"] = {}

        options["plugins"].update(
            {
                "zoom": {
                    "zoom": {
                        "wheel": {"enabled": True},
                        "pinch": {"enabled": True},
                        "drag": {"enabled": True},
                        "mode": "xy",
                    },
                    "pan": {
                        "enabled": True,
                        "modifierKey": "shift",
                        "mode": "xy",
                    },
                },
                "title": {
                    "display": True,
                    "position": "bottom",
                },
            },
        )
        return options


    def _set_chart_global_options(self, options: dict[str, Any]) -> dict[str, Any]:
        """Set chart's global options on the base of certain config fields values.

        Args:
            options (dict[str, Any]): options data dictionary

        Returns:
            dict[str, Any]: updated options
        """
        if "plugins" not in options:
            options["plugins"] = {}

        if "scales" not in options:
            options["scales"] = {
                "x": {},
                "y": {},
            }

        if chart_title := self.settings.get("chart_title"):
            options["plugins"]["subtitle"] = {
                "display": True,
                "position": "top",
                "text": chart_title,
            }

        if chart_xlabel := self.settings.get("chart_xlabel"):
            options["scales"]["x"]["title"] = {
                "display": True,
                "text": chart_xlabel,
            }
        else:
            options["scales"]["x"]["title"] = {
                "display": True,
                "text": self.settings["x"],
            }

        if chart_ylabel := self.settings.get("chart_ylabel"):
            options["scales"]["y"]["title"] = {
                "display": True,
                "text": chart_ylabel,
            }
        else:
            options["scales"]["y"]["title"] = {
                "display": True,
                "text": (
                    self.settings["y"]
                    if type(self.settings["y"]) is str
                    else self.settings["y"][0]),
            }

        if chart_ylabel_right := self.settings.get("chart_ylabel_right"):
            options["scales"]["y1"] = {
                "type": "linear",
                "display": True,
                "position": "right",
                "title": {
                    "display": True,
                    "text": chart_ylabel_right,
                },
            }


class ChartJSBarBuilder(ChartJsBuilder):
    def _prepare_data(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "type": "bar",
            "options": self.settings,
        }

        data["options"].update(
            {
                "indexAxis": "x",
                "elements": {
                    "bar": {"borderWidth": 1},
                },
                "plugins": {
                    "legend": {"position": "top"},
                },
                "scales": {
                    "x": {},
                    "y": {
                        "beginAtZero": True,
                    },
                },
            },
        )

        datasets = []

        for field in self.settings["y"]:
            dataset_data = []

            if len(self.settings["y"]) == 1:
                if self.settings.get("skip_null_values"):
                    self.df = self.df[self.df[field].notna()]

                if self.settings.get("sort_x", False):
                    self.df.sort_values(by=self.settings["x"], inplace=True)

                if self.settings.get("sort_y", False):
                    self.df.sort_values(by=field, inplace=True)

            data["data"] = {
                "labels": self.df[self.settings["x"]].to_list(),
            }

            for label in data["data"]["labels"]:
                try:
                    aggregate_value = int(
                        self.df[self.df[self.settings["x"]] == label][field].sum(),
                    )
                except ValueError as e:
                    raise ChartBuildError(f"Column '{field}' is not numeric") from e

                dataset_data.append(aggregate_value)

            datasets.append(
                {
                    "label": field,
                    "data": dataset_data,
                },
            )

        data["data"]["datasets"] = datasets
        self._set_chart_global_options(data["options"])
        data["options"] = self._create_zoom_and_title_options(data["options"])

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
            self.engine_details_field(),
            self.x_axis_field(columns),
            self.y_multi_axis_field(columns),
            self.more_info_button_field(),
            self.log_x_field(),
            self.log_y_field(),
            self.sort_x_field(),
            self.sort_y_field(),
            self.skip_null_values_field(),
            self.limit_field(maximum=1000000),
            self.chart_title_field(),
            self.chart_xlabel_field(),
            self.chart_ylabel_field(),
            self.color_field(columns),
            self.animation_frame_field(columns),
            self.opacity_field(),
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
    def _split_data_by_year(self) -> None:
        """
        Prepare data for a line chart. It splits the data by year stated
        in the date format column used for x-axis.
        """
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
        ).dt.strftime("%b %d %H:%M")


    def _skip_null_values(self) -> DataFrame:
        """
        Return dataframe after removing missing values.
        """
        df = self.df

        if self.settings.get("skip_null_values"):
            if self.settings.get("break_chart") and len(self.settings["years"]) > 1:
                df = self._break_chart_by_missing_data(df)
            df = df.fillna("null")
        else:
            df = df.fillna(0)

        return df


    def _break_chart_by_missing_data(self, df: DataFrame) -> DataFrame:
        """
        Find gaps in date column and fill them with missing dates.
        """
        if self.settings.get("split_data"):
            df[self.settings["x"]] = df.index

        df["temp_date"] = pd.to_datetime(df[self.settings["x"]]).dt.date

        all_dates = pd.date_range(
            start=df["temp_date"].min(),
            end=df["temp_date"].max(),
            freq="D",
            unit="ns",
        ).date

        date_range_df = pd.DataFrame({"temp_date": all_dates})
        df = pd.merge(date_range_df, df, on="temp_date", how="left")
        df[self.settings["x"]].fillna(
            pd.to_datetime(df["temp_date"]).dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            inplace=True,
        )

        if self.settings.get("split_data"):
            df[self.settings["x"]] = pd.to_datetime(
                df[self.settings["x"]],
                utc=True,
                format="ISO8601",
            ).dt.strftime("%b %d %H:%M")

        return df


    def _set_line_chart_options(self, options: dict[str, Any]) -> None:
        """Set chart's options on the base of certain config fields values.

        Args:
            options (dict[str, Any]): chart options data dictionary
        """
        options["scales"] = {
            "x": {
                "reverse": self.settings.get("invert_x", False),
                "type": "time",
                "time": {
                    "unit": "day",
                },
            },
            "y": {
                "reverse": self.settings.get("invert_y", False),
            },
        }

        if self.settings.get("split_data") and len(self.settings["years"]) > 1:
            options["scales"]["x"]["time"]["tooltipFormat"] = "MMM DD HH:mm"

        self._set_chart_global_options(options)
        options = self._create_zoom_and_title_options(options)


    def to_json(self) -> str:
        try:
            dates = pd.to_datetime(self.df[self.settings["x"]], unit="ns")
            self.settings["years"] = list(dates.dt.strftime("%Y").unique())
        except (ParserError, ValueError):
            self.settings["years"] = []

        if self.settings.get("split_data", False) and len(self.settings["years"]) > 1:
            self._split_data_by_year()

        data: dict[str, Any] = {
            "type": "line",
            "options": self.settings,
            "plugins": {},
        }

        datasets = []

        for idx, column in enumerate(self.settings["y"]):
            df = self._skip_null_values()

            data["data"] = {
                "labels": df[self.settings["x"]].tolist(),
            }

            dataset: dict[str, Any] = {
                "label": column,
                "data": df[column].tolist(),
                "spanGaps": not self.settings.get("break_chart"),
            }

            if len(self.settings["y"]) > 1 and \
                self.settings.get("chart_ylabel_right"):
                if idx == 0:
                    dataset["yAxisID"] = "y"
                if idx == 1:
                    dataset["yAxisID"] = "y1"

            datasets.append(dataset)

        data["data"]["datasets"] = datasets

        self._set_line_chart_options(data["options"])

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
            self.engine_details_field(),
            self.x_axis_field(columns),
            self.y_multi_axis_field(columns),
            self.more_info_button_field(),
            self.sort_x_field(),
            self.sort_y_field(),
            self.invert_x_field(),
            self.invert_y_field(),
            self.split_data_field(),
            self.skip_null_values_field(),
            self.break_chart_field(),
            self.limit_field(maximum=1000000),
            self.chart_title_field(),
            self.chart_xlabel_field(),
            self.chart_ylabel_field(),
            self.chart_ylabel_right_field(),
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
                        self.df[self.df[self.settings["names"]] == label][field].sum(),
                    ),
                )

        data["data"]["datasets"] = [
            {
                "label": field,
                "data": dataset_data,
            },
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
            self.engine_details_field(),
            self.values_field(columns),
            self.names_field(columns),
            self.more_info_button_field(),
            self.opacity_field(),
            self.limit_field(maximum=1000000),
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

        if self.settings.get("skip_null_values"):
            self.df = self.df.fillna("null")
        else:
            self.df = self.df.fillna(0)

        dataset_data = []
        for _, data_series in self.df.iterrows():
            for field in [self.settings["y"]]:
                dataset_data.append(
                    {
                        "x": self.convert_to_native_types(
                            data_series[self.settings["x"]],
                        ),
                        "y": self.convert_to_native_types(data_series[field]),
                    },
                )

        data["data"]["datasets"] = [
            {
                "label": self.settings["y"],
                "data": dataset_data,
            },
        ]

        self._set_chart_global_options(data["options"])
        data["options"] = self._create_zoom_and_title_options(data["options"])

        return json.dumps(self._configure_date_axis(data))


    def _configure_date_axis(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Configure date settings for the x-axis if it uses 'date_time'.
        """
        x_axis = data["options"]["x"]
        scales = data["options"].get("scales", {})

        if x_axis == "date_time":
            x_scale = scales.get("x", {})
            x_scale.update(
                {
                    "type": "time",
                    "time": {
                        "unit": "day",
                        "displayFormats": {"day": "YYYY-MM-DD"},
                    },
                },
            )
            scales["x"] = x_scale

        if scales:
            data["options"]["scales"] = scales

        return data


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
            self.engine_details_field(),
            self.x_axis_field(columns),
            self.y_axis_field(columns),
            self.more_info_button_field(),
            self.sort_x_field(),
            self.sort_y_field(),
            self.skip_null_values_field(),
            self.limit_field(maximum=1000000),
            self.chart_title_field(),
            self.chart_xlabel_field(),
            self.chart_ylabel_field(),
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

        size_max = self.df[self.settings["size"]].max()

        if self.settings.get("skip_null_values"):
            self.df = self.df.fillna("null")
        else:
            self.df = self.df.fillna(0)

        dataset_data = []
        for _, data_series in self.df.iterrows():
            for field in [self.settings["y"]]:
                dataset_data.append(
                    {
                        "x": self.convert_to_native_types(
                            data_series[self.settings["x"]],
                        ),
                        "y": self.convert_to_native_types(data_series[field]),
                        "r": self._calculate_bubble_radius(data_series, size_max),
                    },
                )

        data["data"]["datasets"] = [
            {
                "label": self.settings["y"],
                "data": dataset_data,
            },
        ]

        self._set_chart_global_options(data["options"])
        data["options"] = self._create_zoom_and_title_options(data["options"])

        return json.dumps(self._configure_date_axis(data))


    def _calculate_bubble_radius(self, data_series: pd.Series, size_max: int) -> int:
        """Calculate bubble radius based on the size column"""
        size_column: str = self.settings["size"]

        # Handle cases where size_max is zero or NaN values are present
        # or the column is not numeric
        try:
            pd.to_numeric(size_max)
        except ValueError as e:
            raise ChartBuildError(f"Column '{size_column}' is not numeric") from e

        data_series_size = np.nan_to_num(data_series[size_column], nan=0)
        try:
            bubble_radius = (data_series_size / size_max) * 30
        except (ZeroDivisionError, TypeError):
            bubble_radius = self.min_bubble_radius

        bubble_radius = max(bubble_radius, self.min_bubble_radius)

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
                        self.df[self.df[self.settings["names"]] == label][value].item(),
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
            self.engine_details_field(),
            self.names_field(columns),
            self.values_multi_field(
                columns,
                help_text=(
                    "Select 3 or more different categorical variables (dimensions)"
                ),
            ),
            self.more_info_button_field(),
            self.limit_field(maximum=1000000),
            self.filter_field(columns),
        ]
