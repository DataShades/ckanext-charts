from __future__ import annotations

from typing import Any

import plotly.express as px

from .base import PlotlyBuilder, BasePlotlyForm


class PlotlyBarBuilder(PlotlyBuilder):
    def to_json(self) -> str:
        return self.build_bar_chart()

    def build_bar_chart(self) -> Any:
        if self.settings.get("skip_null_values"):
            self.df = self.df[self.df[self.settings["y"]].notna()]

        # Create an instance of the scatter graph
        fig = px.bar(
            data_frame=self.df,
            x=self.settings["x"],
            y=self.settings["y"],
            log_x=self.settings.get("log_x", False),
            log_y=self.settings.get("log_y", False),
            opacity=self.settings.get("opacity"),
            animation_frame=self.settings.get("animation_frame"),
            color=self.settings.get("color"),
        )

        # Prepare global chart settings
        self._set_chart_global_settings(fig)

        # Prepare additional chart settings
        fig.update_xaxes(
            type="category",
        )

        return fig.to_json()


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
            self.limit_field(maximum=1000000),
            self.chart_title_field(),
            self.x_axis_label_field(),
            self.y_axis_label_field(),
            self.color_field(columns),
            self.animation_frame_field(columns),
            self.opacity_field(),
            self.filter_field(columns),
        ]


class PlotlyHorizontalBarBuilder(PlotlyBuilder):
    def to_json(self) -> Any:
        return self.build_horizontal_bar_chart()

    def build_horizontal_bar_chart(self) -> Any:
        if self.settings.get("skip_null_values"):
            self.df = self.df[self.df[self.settings["y"]].notna()]

        # Create an instance of the scatter graph
        fig = px.bar(
            data_frame=self.df,
            x=self.settings["y"],
            y=self.settings["x"],
            log_x=self.settings.get("log_y", False),
            log_y=self.settings.get("log_x", False),
            opacity=self.settings.get("opacity"),
            animation_frame=self.settings.get("animation_frame"),
            color=self.settings.get("color"),
            orientation="h",
        )

        # Prepare global chart settings
        self._set_chart_global_settings(fig)

        # Prepare additional chart settings
        fig.update_yaxes(
            type="category",
        )

        if not self.settings.get("x_axis_label"):
            fig.update_xaxes(title_text=self.settings["y"])

        if not self.settings.get("y_axis_label"):
            fig.update_yaxes(title_text=self.settings["x"])

        return fig.to_json()


class PlotlyHorizontalBarForm(PlotlyBarForm):
    name = "Horizontal Bar"
    builder = PlotlyHorizontalBarBuilder
