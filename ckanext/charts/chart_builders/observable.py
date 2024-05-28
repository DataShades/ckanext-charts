from __future__ import annotations

import json
from typing import Any

from ckanext.charts.chart_builders.base import BaseChartBuilder, BaseChartForm


class ObservableBuilder(BaseChartBuilder):
    @classmethod
    def get_supported_forms(cls) -> list[type[Any]]:
        return [
            ObservableBarForm,
            ObservableHoriontalBarForm,
            ObservableLineForm,
            ObservablePieForm,
            ObservableScatterForm,
            ObservableAutoForm,
        ]


class ObservableBarBuilder(ObservableBuilder):
    def to_json(self) -> str:
        return json.dumps(
            {
                "type": "bar",
                "data": self.df.to_dict(orient="records"),
                "settings": self.settings,
            }
        )


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
            self.x_axis_field(columns),
            self.y_axis_field(columns),
            self.sort_x_field(),
            self.sort_y_field(),
            self.fill_field(columns),
            self.opacity_field(),
            self.limit_field(),
        ]


class ObservableHorizontalBarBuilder(ObservableBuilder):
    def to_json(self) -> str:
        return json.dumps(
            {
                "type": "horizontal-bar",
                "data": self.df.to_dict(orient="records"),
                "settings": self.settings,
            }
        )


class ObservableHoriontalBarForm(ObservableBarForm):
    name = "Horizontal Bar"
    builder = ObservableHorizontalBarBuilder


class ObservableLineBuilder(ObservableBuilder):
    def to_json(self) -> str:
        return json.dumps(
            {
                "type": "line",
                "data": self.df.to_dict(orient="records"),
                "settings": self.settings,
            }
        )


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
            self.x_axis_field(columns),
            self.y_axis_field(columns),
            self.sort_x_field(),
            self.sort_y_field(),
            self.limit_field(),
        ]


class ObservablePieBuilder(ObservableBuilder):
    def to_json(self) -> str:
        return json.dumps(
            {
                "type": "pie",
                "data": self.df.to_dict(orient="records"),
                "settings": self.settings,
            }
        )


class ObservablePieForm(BaseChartForm):
    name = "Pie"
    builder = ObservablePieBuilder

    def inner_radius_field(self) -> dict[str, Any]:
        return {
            "field_name": "innerRadius",
            "label": "Inner Radius",
            "input_type": "number",
            "group": "Styles",
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
            self.values_field(columns),
            self.names_field(columns),
            self.opacity_field(),
            self.inner_radius_field(),
            self.stroke_width_field(),
            self.font_size_field(),
            self.limit_field(),
            self.width_field(),
            self.height_field(),
        ]


class ObservableScatterBuilder(ObservableBuilder):
    def to_json(self) -> str:
        return json.dumps(
            {
                "type": "scatter",
                "data": self.df.to_dict(orient="records"),
                "settings": self.settings,
            }
        )


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
            self.x_axis_field(columns),
            self.y_axis_field(columns),
            self.sort_x_field(),
            self.sort_y_field(),
            self.color_field(columns),
            self.opacity_field(),
            self.limit_field(),
        ]


class ObservableAutoBuilder(ObservableBuilder):
    def to_json(self) -> str:
        return json.dumps(
            {
                "type": "auto",
                "data": self.df.to_dict(orient="records"),
                "settings": self.settings,
            }
        )


class ObservableAutoForm(BaseChartForm):
    name = "Auto"
    builder = ObservableAutoBuilder

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
            self.x_axis_field(columns),
            self.y_axis_field(columns),
            self.sort_x_field(),
            self.sort_y_field(),
            self.color_field(columns),
            self.opacity_field(),
            self.limit_field(),
        ]
