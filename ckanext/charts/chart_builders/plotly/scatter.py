from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.express as px

from ckanext.charts import exception
from .base import PlotlyBuilder, BasePlotlyForm

# silence SettingWithCopyWarning
pd.options.mode.chained_assignment = None


class PlotlyScatterBuilder(PlotlyBuilder):
    def to_json(self) -> Any:
        return self.build_scatter_chart()

    def build_scatter_chart(self) -> Any:
        # Fill NaN or NULL values in dataframe with 0
        self.df = self.df.fillna(self.DEFAULT_NAN_FILL_VALUE)

        if self.settings.get("skip_null_values"):
            self.df = self.df.loc[self.df[self.settings["y"]] != 0]

        # Manage with size and size_max fields' values
        size_column = self.df[self.settings.get("size", self.df.columns[0])]
        is_numeric = pd.api.types.is_numeric_dtype(size_column)
        if not is_numeric:
            raise exception.ChartBuildError(
                "The 'Size' source should be a field of numeric type.",
            )

        # Create an instance of the scatter graph
        fig = px.scatter(
            data_frame=self.df,
            x=self.settings["x"],
            y=self.settings["y"],
            color=self.settings.get("color"),
            animation_frame=self.settings.get("animation_frame"),
            opacity=self.settings.get("opacity"),
            size=self.settings.get("size"),
            size_max=self.settings.get("size_max"),
        )

        # Prepare global chart settings
        self._set_chart_global_settings(fig)

        # Prepare additional chart settings
        fig.update_xaxes(
            type="category",
        )

        return fig.to_json()


class PlotlyScatterForm(BasePlotlyForm):
    name = "Scatter"
    builder = PlotlyScatterBuilder

    def get_form_fields(self):
        """Get the form fields for the Plotly scatter chart."""
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
            self.y_axis_field(columns),
            self.more_info_button_field(),
            self.log_x_field(),
            self.log_y_field(),
            self.sort_x_field(),
            self.sort_y_field(),
            self.skip_null_values_field(),
            self.size_field(columns),
            self.size_max_field(),
            self.limit_field(maximum=1000000),
            self.chart_title_field(),
            self.x_axis_label_field(),
            self.y_axis_label_field(),
            self.color_field(columns),
            self.animation_frame_field(columns),
            self.opacity_field(),
            self.filter_field(columns),
        ]
