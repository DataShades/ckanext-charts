from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.graph_objects as go
from pandas.core.frame import DataFrame
from pandas.errors import ParserError
from plotly.subplots import make_subplots

from .base import PlotlyBuilder, BasePlotlyForm

# silence SettingWithCopyWarning
pd.options.mode.chained_assignment = None


class PlotlyLineBuilder(PlotlyBuilder):
    def to_json(self) -> Any:
        return self.build_line_chart()

    def _split_data_by_year(self) -> None:
        """Prepare data for a line chart. It splits the data by year stated
        in the date format column which is used for x-axis.
        """
        # Remove unnecessary columns and duplicates from x-axis column
        self.df = self.df[[self.settings["x"], self.settings["y"][0]]]
        self.df.drop_duplicates(subset=[self.settings["x"]], inplace=True)

        # Create a new column with years on the base of the original
        # datetime column
        self.df["_year_"] = pd.to_datetime(self.df[self.settings["x"]]).dt.year

        # Reshape dataframe to be readable by Plotly
        self.df = self.df.pivot(
            index=self.settings["x"],
            columns="_year_",
            values=self.settings["y"][0],
        )

        self.settings["y"] = self.df.columns.tolist()
        self.df[self.settings["x"]] = pd.to_datetime(self.df.index)

    def _prepare_data(self, column_name: str) -> DataFrame:
        """Prepare line chart data before serializing to JSON formatted string.

        Returns:
            Line chart dataframe
        """
        # Remove unnecessary columns and duplicates from x-axis column
        df = self.df[[self.settings["x"], column_name]]
        df.drop_duplicates(subset=[self.settings["x"]], inplace=True)

        if self.settings.get("split_data") and self._is_column_datetime(
            self.settings["x"],
        ):
            # Split dataframe by years
            df = df[
                df[self.settings["x"]].dt.strftime(self.YEAR_DATETIME_FORMAT)
                == str(column_name)
            ]
            # Convert original datetime column to the format `01-01 00:00`
            # to be able to split the graph by year on the same layout
            df[self.settings["x"]] = df[self.settings["x"]].dt.strftime(
                self.DATETIME_TICKS_FORMAT,
            )

        if self.settings.get("skip_null_values"):
            if self._is_column_datetime(self.settings["x"]) and self.settings.get(
                "break_chart",
            ):
                # Handle with missing dates
                df = self._break_chart_by_missing_data(df)
        else:
            # Fill NaN/NULL values with 0
            df.fillna(self.DEFAULT_NAN_FILL_VALUE, inplace=True)

        return df

    def _break_chart_by_missing_data(self, df: DataFrame) -> DataFrame:
        """Find gaps in date column and fill them with missing dates.

        Args:
            df: dataframe to transform

        Returns:
            Processed line chart dataframe
        """
        if self.settings.get("split_data"):
            df[self.settings["x"]] = df.index

        # Create a new column with date values e.g. `2025-01-01`
        df["_temp_date_"] = pd.to_datetime(df[self.settings["x"]]).dt.date

        # Create range of dates from min date to max date with daily frequency
        # and of the date format e.g. `2025-01-01`
        all_dates = pd.date_range(
            start=df["_temp_date_"].min(),
            end=df["_temp_date_"].max(),
            unit="ns",
        ).date

        # Merge the date range of all dates to the temporal date column in order
        # to extend original range of dates with missing dates
        date_range_df = pd.DataFrame({"_temp_date_": all_dates})
        df = pd.merge(date_range_df, df, on="_temp_date_", how="left")

        # Fill null dates of the original datetime column with missing dates
        df[self.settings["x"]].fillna(df["_temp_date_"], inplace=True)

        if self.settings.get("split_data"):
            df[self.settings["x"]] = pd.to_datetime(
                df[self.settings["x"]],
                format=self.DEFAULT_DATETIME_FORMAT,
            ).dt.strftime(self.DATETIME_TICKS_FORMAT)

        # Remove temporal date column
        df.drop(["_temp_date_"], axis=1, inplace=True)

        return df

    def build_line_chart(self) -> Any:
        """
        Build a line chart. It supports multi columns for y-axis
        to display on the line chart.
        """
        # Check if the column representing x axis contains values of datetime
        # format, get these values and create a new settings `years` with unique
        # year values based on this column
        try:
            self.settings["years"] = (
                pd.to_datetime(
                    self.df[self.settings["x"]],
                    format=self.DEFAULT_DATETIME_FORMAT,
                )
                .dt.strftime(self.YEAR_DATETIME_FORMAT)
                .unique()
                .tolist()
            )
        except (ParserError, ValueError):
            self.settings["years"] = []

        if self._is_column_datetime(self.settings["x"]) and self.settings.get(
            "split_data",
        ):
            self._split_data_by_year()

        # Create instance of plotly graph
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        for column in self.settings["y"]:
            dataset = self._prepare_data(column)

            fig.add_trace(
                go.Scatter(
                    x=dataset[self.settings["x"]],
                    y=dataset[column],
                    name=column,
                    connectgaps=not self.settings.get("break_chart"),
                ),
            )

        # Prepare global chart settings
        self._set_chart_global_settings(fig)

        # Prepare additional chart settings
        ## Set categorized x-axis for the data splitted by year to be able to
        ## split the graph by year on the same layout
        if self.settings.get("split_data") and len(self.settings["years"]) > 1:
            fig.update_layout(xaxis={"categoryorder": "category ascending"})

        if y_axis_label := self.settings.get("y_axis_label"):
            fig.update_yaxes(title_text=y_axis_label)
        else:
            fig.update_yaxes(title_text=self.settings["y"][0])

        ## If length y-axis columns is more than 1, display right side y-axis
        if len(self.settings["y"]) > 1:
            if y_axis_label_right := self.settings.get("y_axis_label_right"):
                fig.update_yaxes(
                    title_text=y_axis_label_right,
                    secondary_y=True,
                )
            else:
                fig.update_yaxes(
                    title_text=self.settings["y"][1],
                    secondary_y=True,
                )

        return fig.to_json()


class PlotlyLineForm(BasePlotlyForm):
    name = "Line"
    builder = PlotlyLineBuilder

    def plotly_y_multi_axis_field(
        self,
        columns: list[dict[str, str]],
        max_y: int = 0,
    ) -> dict[str, Any]:
        """Plotly line chart supports multi columns for y-axis"""
        field = self.y_multi_axis_field(columns, max_y)

        field["help_text"] = "Select the columns for the Y axis."

        return field

    def get_form_fields(self):
        """Get the form fields for the Plotly line chart."""
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
            self.limit_field(default=1000, maximum=1000000),
            self.chart_title_field(),
            self.x_axis_label_field(),
            self.y_axis_label_field(),
            self.y_axis_label_right_field(),
            self.filter_field(columns),
        ]
