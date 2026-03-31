from __future__ import annotations

from typing import Any, cast

import pandas as pd
import plotly.graph_objects as go
from pandas.core.frame import DataFrame
from pandas.errors import ParserError
from plotly.subplots import make_subplots

from .base import BasePlotlyForm, PlotlyBuilder
from ckanext.charts.const import FORM_GROUP_DATA

# silence SettingWithCopyWarning
pd.options.mode.chained_assignment = None

# A non-leap reference year used to generate a stable 365-day MM-DD index.
_REFERENCE_YEAR = 2001


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

    def _aggregate_data_to_daily(self, column_name: str) -> DataFrame:
        """Aggregate sub-daily readings to one value per calendar day per year.

        Uses the aggregation method chosen by the user (min / max / average).
        The result index is ``MM-DD`` strings so all years share the same
        positional x-axis labels.

        Args:
            column_name: The Y-axis column to aggregate.

        Returns:
            DataFrame with columns ``[_year_, _day_of_year_, <column_name>]``.
        """
        x_col = self.settings["x"]
        method = self.settings.get("daily_aggregation", "mean")

        df = cast(pd.DataFrame, self.df[[x_col, column_name]].copy())
        df[x_col] = pd.to_datetime(df[x_col])
        df["_year_"] = df[x_col].dt.year
        df["_day_of_year_"] = df[x_col].dt.strftime("%m-%d")

        func = {"min": "min", "max": "max", "mean": "mean"}.get(method, "mean")

        aggregated = (
            df.groupby(["_year_", "_day_of_year_"])[column_name].agg(func).reset_index()
        )
        return aggregated

    def _split_data_by_year_fixed(self) -> None:
        """Prepare data for a fixed 365-day X-axis line chart.

        Aggregates all sub-daily readings to one value per calendar day,
        then reindexes every year against a full 365-slot ``MM-DD`` grid.
        Missing days become ``NaN`` (rendered as whitespace when
        ``break_chart`` is enabled, or silently skipped when it is not).
        """
        x_col = self.settings["x"]
        y_col = self.settings["y"][0]

        aggregated = self._aggregate_data_to_daily(y_col)

        # Build the canonical 365-day index from a stable non-leap reference year.
        full_year_index = (
            pd.date_range(
                start=f"{_REFERENCE_YEAR}-01-01",
                end=f"{_REFERENCE_YEAR}-12-31",
                freq="D",
            )
            .strftime("%m-%d")
            .tolist()
        )

        # Pivot: rows = MM-DD, columns = year, values = aggregated Y
        pivot = cast(
            pd.DataFrame,
            aggregated.pivot(
                index="_day_of_year_",
                columns="_year_",
                values=y_col,
            ),
        )

        # Reindex to the full 365-day grid; days with no data become NaN.
        pivot = cast(pd.DataFrame, pivot.reindex(full_year_index))

        self.settings["y"] = pivot.columns.tolist()
        self.df = pivot
        self.df[x_col] = pivot.index

    def _prepare_data(self, column_name: str) -> DataFrame:
        """Prepare line chart data before serializing to JSON formatted string.

        When ``fixed_365_days`` is active the dataframe has already been
        aggregated and pivoted by :meth:`_split_data_by_year_fixed`, so we
        only need to select the right year column and apply gap logic.

        Returns:
            Line chart dataframe
        """
        x_col = self.settings["x"]

        # fixed_365_days path: data is already on the MM-DD grid
        if (
            self.settings.get("fixed_365_days")
            and self.settings.get("split_data")
            and self._is_column_datetime(x_col)
        ):
            df = cast(pd.DataFrame, self.df[[x_col, column_name]].copy())
            # NaN rows already represent missing days — leave them for
            # Plotly to render as breaks (connectgaps=False) or skip them.
            if not self.settings.get("skip_null_values"):
                df[column_name].fillna(self.DEFAULT_NAN_FILL_VALUE, inplace=True)

            return df

        # Remove unnecessary columns and duplicates from x-axis column
        df = self.df[[x_col, column_name]]
        df.drop_duplicates(subset=[x_col], inplace=True)

        if self.settings.get("split_data") and self._is_column_datetime(x_col):
            # Split dataframe by years
            df = df[
                df[x_col].dt.strftime(self.YEAR_DATETIME_FORMAT) == str(column_name)
            ]
            # Convert original datetime column to the format `01-01 00:00`
            # to be able to split the graph by year on the same layout
            df[x_col] = df[x_col].dt.strftime(self.DATETIME_TICKS_FORMAT)

        if self.settings.get("skip_null_values"):
            if self._is_column_datetime(x_col) and self.settings.get("break_chart"):
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

        x_col = self.settings["x"]
        is_datetime = self._is_column_datetime(x_col)
        split_data = self.settings.get("split_data")
        fixed_365 = self.settings.get("fixed_365_days") and split_data and is_datetime

        if is_datetime and split_data:
            if fixed_365:
                self._split_data_by_year_fixed()
            else:
                self._split_data_by_year()

        # Create instance of plotly graph
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        for column in self.settings["y"]:
            dataset = self._prepare_data(column)

            fig.add_trace(
                go.Scatter(
                    x=dataset[self.settings["x"]],
                    y=dataset[column],
                    name=str(column),
                    connectgaps=not self.settings.get("break_chart"),
                ),
            )

        # Prepare global chart settings
        self._set_chart_global_settings(fig)

        # Prepare additional chart settings
        if fixed_365:
            # Pin the x-axis to the exact 365 MM-DD sequence so every month
            # always occupies the same proportion of horizontal space.
            full_year_index = (
                pd.date_range(
                    start=f"{_REFERENCE_YEAR}-01-01",
                    end=f"{_REFERENCE_YEAR}-12-31",
                    freq="D",
                )
                .strftime("%m-%d")
                .tolist()
            )
            fig.update_layout(
                xaxis={
                    "type": "category",
                    "categoryorder": "array",
                    "categoryarray": full_year_index,
                },
            )
        elif split_data and len(self.settings["years"]) > 1:
            ## Set categorized x-axis for the data splitted by year to be able to
            ## split the graph by year on the same layout
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

    def fixed_365_days_field(self) -> dict[str, Any]:
        """Checkbox that enables the fixed 365-day X-axis.

        Only meaningful when *Split by years* is also enabled; the field
        definition carries a ``show_if`` hint so the generic conditional-
        visibility JS module can hide it when the prerequisite is unset.
        """
        return {
            "field_name": "fixed_365_days",
            "label": "Fixed 365 days",
            "form_snippet": "chart_checkbox.html",
            "group": FORM_GROUP_DATA,
            "validators": [
                self.get_validator("chart_checkbox"),
                self.get_validator("default")(False),
                self.get_validator("boolean_validator"),
            ],
            "help_text": (
                "Always display a full 365-day X-axis so every month occupies "
                'equal horizontal space. Requires "Split by years" to be enabled.'
            ),
            "type": "bool",
            "default": False,
            "show_if": [{"field": "split_data", "value": "true"}],
        }

    def daily_aggregation_field(self) -> dict[str, Any]:
        """Select the aggregation method applied when collapsing sub-daily data
        to one value per calendar day.

        Shown only when *Fixed 365 days* is enabled.
        """
        return {
            "field_name": "daily_aggregation",
            "label": "Daily aggregation",
            "form_snippet": "chart_select.html",
            "group": FORM_GROUP_DATA,
            "choices": [
                {"value": "mean", "label": "Average"},
                {"value": "min", "label": "Minimum"},
                {"value": "max", "label": "Maximum"},
            ],
            "validators": [
                self.get_validator("default")("mean"),
                self.get_validator("unicode_safe"),
            ],
            "help_text": (
                "When multiple readings exist for the same day, use this value. "
                'Active only with "Fixed 365 days" enabled.'
            ),
            "type": "str",
            "default": "mean",
            "show_if": [
                {"field": "split_data", "value": "true"},
                {"field": "fixed_365_days", "value": "true"},
            ],
        }

    def get_form_fields(self) -> list[dict[str, Any]]:
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
            self.fixed_365_days_field(),
            self.daily_aggregation_field(),
            self.skip_null_values_field(),
            self.break_chart_field(),
            self.limit_field(default=1000, maximum=1000000),
            self.chart_title_field(),
            self.x_axis_label_field(),
            self.y_axis_label_field(),
            self.y_axis_label_right_field(),
            self.filter_field(columns),
        ]
