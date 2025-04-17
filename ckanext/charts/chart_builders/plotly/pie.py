from __future__ import annotations

from typing import Any

import plotly.express as px

from .base import BasePlotlyForm, PlotlyBuilder


class PlotlyPieBuilder(PlotlyBuilder):
    def to_json(self) -> Any:
        # does not accept a limit keyword argument
        self.settings.pop("limit", None)
        return px.pie(self.df, **self.settings).to_json()


class PlotlyPieForm(BasePlotlyForm):
    name = "Pie"
    builder = PlotlyPieBuilder

    def get_form_fields(self):
        """Get the form fields for the Plotly pie chart."""
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
            self.values_field(columns),
            self.names_field(columns),
            self.more_info_button_field(),
            self.opacity_field(),
            self.limit_field(maximum=1000000),
            self.filter_field(columns),
        ]
