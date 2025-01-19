from __future__ import annotations

import json
import pandas as pd
from typing import Any

from ckanext.charts import exception
from ckanext.charts.chart_builders.base import BaseChartBuilder, BaseChartForm


class ObservableBuilder(BaseChartBuilder):
    DEFAULT_AXIS_TICKS_NUMBER = 12
    DEFAULT_DATETIME_FORMAT = "ISO8601"
    ISO_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S"
    YEAR_DATETIME_FORMAT = "%Y"
    DEFAULT_PLOT_HEIGHT = 400
    DEFAULT_NAN_FILL_VALUE = 0
    MAX_DOT_RADIUS = 30

    @classmethod
    def get_supported_forms(cls) -> list[type[Any]]:
        return [
            ObservableBarForm,
            ObservableHorizontalBarForm,
            ObservableLineForm,
            ObservablePieForm,
            ObservableScatterForm,
        ]

    def _set_chart_global_settings(
        self, data: dict[str, Any]) -> dict[str, Any]:
        """Set chart's global settings and plot configs.

        Args:
            data (dict[str, Any]): settings data dictionary

        Returns:
            Updated settings data dictionary
        """
        if "settings" not in data:
            data["settings"] = {}

        if "plot" not in data:
            data["plot"] = {}

        if chart_title := self.settings.get("chart_title"):
            data["plot"].update({"title": chart_title})

        if self.settings["sort_x"]:
            data["settings"].update({"sort": {"y": "x"}})

        if self.settings["sort_y"]:
            data["settings"].update({"sort": {"x": "y"}})

        data["settings"]["tip"] = True

        data["plot"].update(
            {
                "x": {
                    "label": (
                        self.settings.get("x_axis_label") or
                        self.settings.get("x")
                    ),
                    "reverse": self.settings.get("invert_x", False),
                },
                "y": {
                    "label": (
                        self.settings.get("y_axis_label") or
                        self.settings.get("y")
                    ),
                    "reverse": self.settings.get("invert_y", False),
                },
                "color": {
                    "legend": True,
                },
                "marks": [],
            },
        )


class ObservableBarBuilder(ObservableBuilder):
    def _prepare_data(self) -> dict[str, Any]:
        """Prepare bar chart data before serializing to JSON formatted string.

        Returns:
            Bar chart data dictionary
        """
        # Fill NA/NaN values in the incoming data/dataframe
        if self.settings.get("skip_null_values"):
            self.df = self.df.dropna(subset=self.settings["y"]).fillna("null")
        else:
            self.df = self.df.fillna(self.DEFAULT_NAN_FILL_VALUE)

        # Set global chart settings
        data: dict[str, Any] = {
            "type": "bar",
            "data": self.df.to_dict(orient="records"),
            "settings": self.settings,
        }
        self._set_chart_global_settings(data)

        # Set additional chart settings
        data["plot"]["y"]["grid"] = True

        return data


    def to_json(self) -> str:
        return json.dumps(self._prepare_data())


class ObservableBarForm(BaseChartForm):
    name = "Bar"
    builder = ObservableBarBuilder

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
            self.engine_details_field(),
            self.x_axis_field(columns),
            self.y_axis_field(columns),
            self.more_info_button_field(),
            self.sort_x_field(),
            self.sort_y_field(),
            self.invert_x_field(),
            self.invert_y_field(),
            self.skip_null_values_field(),
            self.limit_field(maximum=1000000),
            self.chart_title_field(),
            self.x_axis_label_field(),
            self.y_axis_label_field(),
            self.fill_field(columns),
            self.opacity_field(),
            self.filter_field(columns),
        ]


class ObservableHorizontalBarBuilder(ObservableBuilder):
    def _prepare_data(self) -> dict[str, Any]:
        """Prepare horizontal bar chart data before serializing to JSON
        formatted string.

        Returns:
            Horizontal bar chart data dictionary
        """
        # Fill NA/NaN values in the incoming data/dataframe
        if self.settings.get("skip_null_values"):
            self.df = self.df.dropna(subset=self.settings["x"]).fillna("null")
        else:
            self.df = self.df.fillna(self.DEFAULT_NAN_FILL_VALUE)

        # Set global chart settings
        data: dict[str, Any] = {
            "type": "horizontal-bar",
            "data": self.df.to_dict(orient="records"),
            "settings": self.settings,
        }
        self._set_chart_global_settings(data)

        # Set additional chart settings
        data["plot"]["height"] = self.DEFAULT_PLOT_HEIGHT
        data["plot"]["x"]["grid"] = True

        return data


    def to_json(self) -> str:
        return json.dumps(self._prepare_data())


class ObservableHorizontalBarForm(ObservableBarForm):
    name = "Horizontal Bar"
    builder = ObservableHorizontalBarBuilder


class ObservableLineBuilder(ObservableBuilder):
    def _break_chart_by_missing_data(self) -> None:
        """Find gaps in date column and fill them with missing dates.
        """
        # Create a new column with date values e.g. `2025-01-01`
        self.df["_temp_date_"] = pd.to_datetime(
            self.df[self.settings["x"]],
        ).dt.date

        # Create range of dates from min date to max date with daily frequency
        # and of the date format e.g. `2025-01-01`
        all_dates = pd.date_range(
            start=self.df["_temp_date_"].min(),
            end=self.df["_temp_date_"].max(),
            freq="D",
            unit="ns",
        ).date

        # Merge the date range of all dates to the temporal date column in order
        # to add missing dates
        date_range_df = pd.DataFrame({"_temp_date_": all_dates})
        self.df = pd.merge(date_range_df, self.df, on="_temp_date_", how="left")
        # Fill NAN or NULL dates in the original datetime column with missing
        # dates in ISO8601 format
        self.df[self.settings["x"]].fillna(
            pd.to_datetime(
                self.df["_temp_date_"],
                utc=True,
                format=self.DEFAULT_DATETIME_FORMAT,
            ).dt.strftime(self.ISO_DATETIME_FORMAT),
            inplace=True,
        )

        # Remove temporal date column and create categorical `_year_` column
        self.df.drop(["_temp_date_"], axis=1, inplace=True)
        self.df["_year_"] = pd.to_datetime(
            self.df[self.settings["x"]],
        ).dt.strftime(self.YEAR_DATETIME_FORMAT)

    def _prepare_data(self) -> dict[str, Any]:
        """Prepare line chart data before serializing to JSON formatted string.

        Returns:
            Line chart data dictionary
        """
        if self._is_column_datetime(self.settings["x"]):
            # Remove unnecessary columns and duplicates from x-axis column
            self.df = self.df[[self.settings["x"], self.settings["y"][0]]]
            self.df.drop_duplicates(subset=[self.settings["x"]], inplace=True)

            if self.settings.get("split_data"):
                # Create a new column with years on the base of the original
                # datetime column
                self.df["_year_"] = pd.to_datetime(
                    self.df[self.settings["x"]],
                ).dt.strftime(self.YEAR_DATETIME_FORMAT)

            if self.settings.get("break_chart"):
                self._break_chart_by_missing_data()
        else:
            # Unpivot the dataframe/create a `long table` dataframe with
            # categorical column `category`
            self.df = pd.melt(
                self.df,
                id_vars=self.settings["x"],
                value_vars=self.settings["y"],
                var_name="_category_",
            )

        # Fill NA/NaN values in the incoming data/dataframe
        if self.settings.get("skip_null_values"):
            self.df = self.df.fillna("null")
        else:
            self.df = self.df.fillna(self.DEFAULT_NAN_FILL_VALUE)

        # Chart global settings
        data: dict[str, Any] = {
            "type": "line",
            "data": self.df.to_dict(orient="records"),
            "settings": self.settings,
        }
        self._set_chart_global_settings(data)

        # Chart additional settings
        if "settings" not in data:
            data["settings"] = {}

        if "plot" not in data:
            data["plot"] = {}

        data["plot"]["grid"] = True
        data["plot"]["x"]["ticks"] = self.DEFAULT_AXIS_TICKS_NUMBER

        if self._is_column_datetime(self.settings["x"]):
            data["plot"]["x"]["type"] = "utc"
            data["settings"]["y"] = self.settings["y"][0]
            if self.settings.get("split_data"):
                data["settings"].update(
                    {
                        "stroke": "_year_",
                        "marker": False,
                    },
                )
            else:
                data["plot"].pop("color")
        else:
            data["settings"].update(
            {
                "y": "value",
                "stroke": "_category_",
                "marker": True,
            },
        )

        return data

    def to_json(self) -> str:
        return json.dumps(self._prepare_data())


class ObservableLineForm(BaseChartForm):
    name = "Line"
    builder = ObservableLineBuilder

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
            self.invert_x_field(),
            self.invert_y_field(),
            self.sort_x_field(),
            self.sort_y_field(),
            self.split_data_field(),
            self.skip_null_values_field(),
            self.break_chart_field(),
            self.limit_field(maximum=1000000),
            self.chart_title_field(),
            self.x_axis_label_field(),
            self.y_axis_label_field(),
            self.y_axis_label_right_field(),
            self.filter_field(columns),
        ]


class ObservablePieBuilder(ObservableBuilder):
    def _prepare_data(self) -> dict[str, Any]:
        """Prepare pie chart data before serializing to JSON formatted string.

        Returns:
            Pie chart data dictionary
        """
        # Reduce dataframe by removing unnecessary columns
        self.df = self.df[[self.settings["names"], self.settings["values"]]]

        # Fill NA/NaN values in the incoming data/dataframe
        if self.settings.get("skip_null_values"):
            self.df = self.df.dropna(subset=self.settings["values"])
        else:
            self.df = self.df.fillna(self.DEFAULT_NAN_FILL_VALUE)

        # Chart global settings
        data: dict[str, Any] = {
            "type": "pie",
            "data": self.df.to_dict(orient="records"),
            "settings": self.settings,
        }

        return data

    def to_json(self) -> str:
        return json.dumps(self._prepare_data())


class ObservablePieForm(BaseChartForm):
    name = "Pie"
    builder = ObservablePieBuilder

    def inner_radius_field(self) -> dict[str, Any]:
        return {
            "field_name": "innerRadius",
            "label": "Inner Radius",
            "input_type": "number",
            "group": "Styles",
            "type": "number",
            "validators": [
                self.get_validator("default")(0),
                self.get_validator("float_validator"),
            ],
        }

    def stroke_width_field(self) -> dict[str, Any]:
        return {
            "field_name": "strokeWidth",
            "label": "Stroke Width",
            "input_type": "number",
            "group": "Styles",
            "help_text": "Works only if inner radius is lower than 0",
            "validators": [
                self.get_validator("default")(1),
                self.get_validator("float_validator"),
            ],
        }

    def font_size_field(self) -> dict[str, Any]:
        return {
            "field_name": "fontSize",
            "label": "Font Size",
            "input_type": "number",
            "group": "Styles",
            "validators": [
                self.get_validator("default")(12),
                self.get_validator("float_validator"),
            ],
        }

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
            self.skip_null_values_field(),
            self.opacity_field(),
            self.inner_radius_field(),
            self.stroke_width_field(),
            self.font_size_field(),
            self.limit_field(maximum=1000000),
            self.width_field(),
            self.height_field(),
            self.filter_field(columns),
        ]


class ObservableScatterBuilder(ObservableBuilder):
    def _prepare_data(self) -> dict[str, Any]:
        """Prepare scatter chart data before serializing to JSON formatted string.

        Returns:
            Scatter chart data dictionary
        """
        # Fill NA/NaN values in the incoming data/dataframe
        if self.settings.get("skip_null_values"):
            self.df = self.df.dropna(
                subset=[self.settings["x"], self.settings["y"]],
            ).fillna("null")
        else:
            self.df = self.df.fillna(self.DEFAULT_NAN_FILL_VALUE)

        # Chart global settings
        data: dict[str, Any] = {
            "type": "scatter",
            "data": self.df.to_dict(orient="records"),
            "settings": self.settings,
        }
        self._set_chart_global_settings(data)

        # Chart additional settings
        data["settings"]["r"] = self.settings["size_max"] * self.MAX_DOT_RADIUS / 100
        data["settings"]["fill"] = self.settings.get("color", "blue")
        data["plot"]["grid"] = True
        data["plot"]["x"]["ticks"] = self.DEFAULT_AXIS_TICKS_NUMBER

        return data

    def to_json(self) -> str:
        return json.dumps(self._prepare_data())


class ObservableScatterForm(BaseChartForm):
    name = "Scatter"
    builder = ObservableScatterBuilder

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
            self.size_max_field(),
            self.x_axis_field(columns),
            self.y_axis_field(columns),
            self.more_info_button_field(),
            self.sort_x_field(),
            self.sort_y_field(),
            self.skip_null_values_field(),
            self.limit_field(maximum=1000000),
            self.chart_title_field(),
            self.x_axis_label_field(),
            self.y_axis_label_field(),
            self.color_field(columns),
            self.opacity_field(),
            self.filter_field(columns),
        ]
