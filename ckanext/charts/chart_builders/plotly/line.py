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
        # Check if the datetime column contains dates for less than two years
        # and there is nothing to split
        if len(self.settings["years"]) <= 1:
            return

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

        self.settings["y"] = self.df.columns.to_list()
        self.df[self.settings["x"]] = self.df.index
        # Convert original datetime column to the format `Jan 01 00:00`
        # to be able to split the graph by year on the same layout
        self.df[self.settings["x"]] = pd.to_datetime(
            self.df[self.settings["x"]],
            unit="ns",
        ).dt.strftime("%m-%d %H:%M")

    def _skip_null_values(self, column: str) -> tuple[Any, Any]:
        """Return values for x-axis and y-axis after removing missing values.

        Args:
            column (str): column to handle with its NaN or NULL values

        Returns:
            Tuple of columns representing x and y axes
        """
        # If split_data_field is True and the datetime column contains dates
        # for more than one year remove records with NaN or NULL values in the
        # certain column
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
            y = df[column].fillna(self.DEFAULT_NAN_FILL_VALUE)

        return x, y

    def _break_chart_by_missing_data(
        self,
        df: DataFrame,
        column: str,
    ) -> tuple[Any, Any]:
        """Find gaps in date column and fill them with missing dates.

        Args:
            df (DataFrame): dataframe to transform
            column (str): dataframe column to manage with missing dates

        Returns:
            Tuple of two columns representing x and y axes
        """
        # If the datetime column contains dates for less than two years return
        # tuple of two columns for x and y axes from incoming dataframe
        if len(self.settings["years"]) <= 1:
            return df[self.settings["x"]], df[column]

        df["xaxis"] = df[self.settings["x"]]

        if self.settings.get("split_data"):
            df[self.settings["x"]] = df.index

        # Create a new column with date values e.g. `2025-01-01`
        df["date"] = pd.to_datetime(df[self.settings["x"]]).dt.date

        # Create range of dates from min date to max date with daily frequency
        # and of the date format e.g. `2025-01-01`
        all_dates = pd.date_range(
            start=df["date"].min(),
            end=df["date"].max(),
            unit="ns",
        ).date

        # Merge the date range of all dates to the temporal date column in order
        # to add missing dates
        date_range_df = pd.DataFrame({"date": all_dates})
        df = pd.merge(date_range_df, df, on="date", how="left")

        return df["xaxis"], df[column]

    def build_line_chart(self) -> Any:
        """
        Build a line chart. It supports multi columns for y-axis
        to display on the line chart.
        """
        # Check if the column representing x axis contains values of datetime
        # format, get these values and create a new settings `years` with unique
        # year values based on this column
        try:
            dates = pd.to_datetime(self.df[self.settings["x"]], unit="ns")
            self.settings["years"] = dates.dt.year.unique()
        except (ParserError, ValueError):
            self.settings["years"] = []

        # Prepare data for Plotly
        if self.settings.get("split_data", False):
            self._split_data_by_year()

        x, y = self._skip_null_values(self.settings["y"][0])

        # Create instance of plotly graph
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        fig.add_trace(
            go.Scatter(
                x=x,
                y=y,
                name=self.settings["y"][0],
                connectgaps=not self.settings.get("break_chart"),
            ),
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
                )

        # Prepare chart settings
        if self.settings.get("split_data") and len(self.settings["years"]) > 1:
            fig.update_layout(xaxis={"categoryorder": "category ascending"})

        if chart_title := self.settings.get("chart_title"):
            fig.update_layout(title_text=chart_title)

        if x_axis_label := self.settings.get("x_axis_label"):
            fig.update_xaxes(title_text=x_axis_label)
        else:
            fig.update_xaxes(title_text=self.settings["x"])

        if y_axis_label := self.settings.get("y_axis_label"):
            fig.update_yaxes(title_text=y_axis_label, secondary_y=False)
        else:
            fig.update_yaxes(title_text=self.settings["y"][0], secondary_y=False)

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

        if self.settings.get("invert_x", False):
            fig.update_xaxes(autorange="reversed")

        if self.settings.get("invert_y", False):
            fig.update_yaxes(autorange="reversed")

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
            self.x_axis_label_field(),
            self.y_axis_label_field(),
            self.y_axis_label_right_field(),
            self.filter_field(columns),
        ]
