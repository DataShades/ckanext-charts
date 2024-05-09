from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, cast

import pandas as pd
import plotly.express as px

import ckan.plugins.toolkit as tk
from ckan import types

from ckanext.charts import fetchers
from ckanext.charts.chart_builders.base import BaseChartBuilder


class PlotlyBuilder(BaseChartBuilder):
    def __init__(self, df: pd.DataFrame, settings: dict[str, Any]) -> None:
        super().__init__(df, settings)

        self.settings = self.drop_view_fields(self.drop_empty_values(self.settings))

        if self.settings.pop("sort_x", False):
            self.df.sort_values(by=self.settings["x"], inplace=True)

        if self.settings.pop("sort_y", False):
            self.df.sort_values(by=self.settings["y"], inplace=True)

        if limit := self.settings.pop("limit", 0):
            self.df = self.df.head(int(limit))

        self.settings.pop("query", None)

    def drop_view_fields(self, settings: dict[str, Any]) -> dict[str, Any]:
        view_fields = ["title", "notes", "engine", "type"]

        return {k: v for k, v in settings.items() if k not in view_fields}

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
    def to_json(self) -> Any:
        return px.bar(self.df, **self.settings).to_json()

    def to_html(self) -> str:
        return px.bar(self.df, **self.settings).to_html()


class PlotlyHorizontalBarBuilder(PlotlyBuilder):
    def __init__(self, df: pd.DataFrame, settings: dict[str, Any]) -> None:
        super().__init__(df, settings)
        self.settings["orientation"] = "h"

    def to_json(self) -> Any:
        return px.bar(self.df, **self.settings).to_json()

    def to_html(self) -> str:
        return px.bar(self.df, **self.settings).to_html()


class PlotlyPieBuilder(PlotlyBuilder):
    def to_json(self) -> Any:
        return px.pie(self.df, **self.settings).to_json()

    def to_html(self) -> str:
        return px.pie(self.df, **self.settings).to_html()


class PlotlyLineBuilder(PlotlyBuilder):
    def to_json(self) -> Any:
        return px.line(self.df, **self.settings).to_json()

    def to_html(self) -> str:
        return px.line(self.df, **self.settings).to_html()


class PlotlyScatterBuilder(PlotlyBuilder):
    def to_json(self) -> Any:
        return px.scatter(self.df, **self.settings).to_json()

    def to_html(self) -> str:
        return px.scatter(self.df, **self.settings).to_html()


class BasePlotlyForm(ABC):
    def __init__(self, resource_id: str) -> None:
        try:
            self.df = fetchers.DatastoreDataFetcher(resource_id).fetch_data()
        except tk.ValidationError:
            return

    def get_validator(self, name: str) -> types.ValueValidator:
        """Get the validator by name. Replaces the tk.get_validator to get rid
        of annoying typing error"""
        return cast(types.ValueValidator, tk.get_validator(name))

    @abstractmethod
    def get_form_fields(self) -> list[dict[str, Any]]:
        pass

    def get_expanded_form_fields(self):
        return self.expand_schema_fields(self.drop_validators(self.get_form_fields()))

    def expand_schema_fields(
        self,
        fields: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Expand the schema fields presets."""
        from ckanext.scheming.plugins import _expand_schemas

        expanded_schemas = _expand_schemas({"schema": {"fields": fields}})

        return expanded_schemas["schema"]["fields"]

    def drop_validators(self, fields: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Drop the validators from the fields, because we don't need this information
        to render a form."""
        for field in fields:
            if "validators" not in field:
                continue

            field.pop("validators")

        return fields

    def get_validation_schema(self) -> dict[str, Any]:
        fields = self.get_form_fields()

        return {
            field["field_name"]: field["validators"]
            for field in fields
            if "validators" in field
        }

    def get_form_tabs(self) -> list[str]:
        return ["General", "Structure", "Data", "Styles"]

    def column_field(self, choices: list[dict[str, str]]) -> dict[str, Any]:
        return {
            "field_name": "column",
            "label": "Column",
            "preset": "select",
            "required": True,
            "choices": choices,
            "group": "Data",
            "validators": [
                self.get_validator("ignore_empty"),
                self.get_validator("unicode_safe"),
            ],
        }

    def title_field(self) -> dict[str, Any]:
        return {
            "field_name": "title",
            "label": "Title",
            "preset": "title",
            "form_placeholder": "Chart title",
            "group": "General",
        }

    def description_field(self) -> dict[str, Any]:
        return {
            "field_name": "notes",
            "label": "Description",
            "form_snippet": "markdown.html",
            "form_placeholder": "Information about my view",
            "group": "General",
        }

    def engine_field(self) -> dict[str, Any]:
        return {
            "field_name": "engine",
            "label": "Engine",
            "preset": "select",
            "required": True,
            "choices": tk.h.get_available_chart_engines_options(),
            "group": "Structure",
            "validators": [
                self.get_validator("default")("plotly"),
                self.get_validator("unicode_safe"),
            ],
        }

    def type_field(self, choices: list[dict[str, str]]) -> dict[str, Any]:
        return {
            "field_name": "type",
            "label": "Type",
            "preset": "select",
            "required": True,
            "choices": choices,
            "group": "Structure",
            "validators": [
                self.get_validator("default")("Bar"),
                self.get_validator("unicode_safe"),
            ],
            "form_attrs": {
                "hx-get": tk.h.url_for("charts_view.update_form"),
                "hx-trigger": "change",
                "hx-include": "closest form",
                "hx-target": ".charts-view--form",
            },
        }

    def x_axis_field(self, choices: list[dict[str, str]]) -> dict[str, Any]:
        return {
            "field_name": "x",
            "label": "X Axis",
            "preset": "select",
            "required": True,
            "choices": choices,
            "group": "Data",
            "validators": [
                self.get_validator("ignore_empty"),
                self.get_validator("unicode_safe"),
            ],
        }

    def y_axis_field(self, choices: list[dict[str, str]]) -> dict[str, Any]:
        field = self.column_field(choices)
        field.update({"field_name": "y", "label": "Y Axis"})

        return field

    def sort_x_field(self) -> dict[str, Any]:
        return {
            "field_name": "sort_x",
            "label": "Sort X-axis",
            "form_snippet": "chart_checkbox.html",
            "group": "Data",
            "validators": [
                self.get_validator("default")(False),
                self.get_validator("boolean_validator"),
            ],
        }

    def sort_y_field(self) -> dict[str, Any]:
        return {
            "field_name": "sort_y",
            "label": "Sort Y-axis",
            "form_snippet": "chart_checkbox.html",
            "group": "Data",
            "validators": [
                self.get_validator("default")(False),
                self.get_validator("boolean_validator"),
            ],
        }

    def query_field(self) -> dict[str, Any]:
        return {
            "field_name": "query",
            "label": "Query",
            "form_snippet": "textarea.html",
            "group": "Structure",
            "form_attrs": {"disabled": 5},
            "validators": [
                self.get_validator("ignore_empty"),
                self.get_validator("unicode_safe"),
            ],
        }

    def log_x_field(self) -> dict[str, Any]:
        return {
            "field_name": "log_x",
            "label": "Log-scale X-axis",
            "form_snippet": "chart_checkbox.html",
            "group": "Data",
            "validators": [
                self.get_validator("default")(False),
                self.get_validator("boolean_validator"),
            ],
        }

    def log_y_field(self) -> dict[str, Any]:
        return {
            "field_name": "log_y",
            "label": "Log-scale Y-axis",
            "form_snippet": "chart_checkbox.html",
            "group": "Data",
            "validators": [
                self.get_validator("default")(False),
                self.get_validator("boolean_validator"),
            ],
        }

    def color_field(self, choices: list[dict[str, str]]) -> dict[str, Any]:
        return {
            "field_name": "color",
            "label": "Color",
            "preset": "select",
            "choices": choices,
            "group": "Styles",
            "validators": [
                self.get_validator("ignore_empty"),
                self.get_validator("unicode_safe"),
            ],
        }

    def animation_frame_field(self, choices: list[dict[str, str]]) -> dict[str, Any]:
        return {
            "field_name": "animation_frame",
            "label": "Animation Frame",
            "preset": "select",
            "choices": choices,
            "group": "Styles",
            "validators": [
                self.get_validator("ignore_empty"),
                self.get_validator("unicode_safe"),
            ],
        }

    def opacity_field(self) -> dict[str, Any]:
        """The opacity field represent the opacity level of the chart."""
        return {
            "field_name": "opacity",
            "label": "Opacity",
            "form_snippet": "chart_range.html",
            "group": "Styles",
            "validators": [
                self.get_validator("default")(1),
                self.get_validator("float_validator"),
            ],
        }

    def limit_field(self) -> dict[str, Any]:
        """The limit field represent an amount of rows to show in the chart."""
        return {
            "field_name": "limit",
            "label": "Limit",
            "validators": [
                self.get_validator("default")(100),
                self.get_validator("int_validator"),
                self.get_validator("limit_to_configured_maximum")("", 10000),
            ],
            "group": "Data",
        }


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
            self.query_field(),
            self.x_axis_field(columns),
            self.y_axis_field(columns),
            self.log_x_field(),
            self.log_y_field(),
            self.sort_x_field(),
            self.sort_y_field(),
            self.color_field(columns),
            self.animation_frame_field(columns),
            self.opacity_field(),
            self.limit_field(),
        ]


class PlotlyPieForm(BasePlotlyForm):
    name = "Pie"
    builder = PlotlyPieBuilder

    def values_field(self, choices: list[dict[str, str]]) -> dict[str, Any]:
        field = self.column_field(choices)
        field.update({"field_name": "values", "label": "Values"})

        return field

    def names_field(self, choices: list[dict[str, str]]) -> dict[str, Any]:
        field = self.column_field(choices)
        field.update({"field_name": "names", "label": "Names"})

        return field

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
            self.query_field(),
            self.values_field(columns),
            self.names_field(columns),
            self.opacity_field(),
            self.limit_field(),
        ]


class PlotlyHoriontalBarForm(PlotlyBarForm):
    name = "Horizontal Bar"
    builder = PlotlyHorizontalBarBuilder


class PlotlyLineForm(BasePlotlyForm):
    name = "Line"
    builder = PlotlyLineBuilder

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
            self.query_field(),
            self.x_axis_field(columns),
            self.y_axis_field(columns),
            self.log_x_field(),
            self.log_y_field(),
            self.sort_x_field(),
            self.sort_y_field(),
            self.color_field(columns),
            self.animation_frame_field(columns),
            self.limit_field(),
        ]


class PlotlyScatterForm(BasePlotlyForm):
    name = "Scatter"
    builder = PlotlyScatterBuilder

    def size_field(self, choices: list[dict[str, str]]) -> dict[str, Any]:
        field = self.column_field(choices)
        field.update({"field_name": "size", "label": "Size", "group": "Structure"})

        return field

    def size_max_field(self) -> dict[str, Any]:
        return {
            "field_name": "size_max",
            "label": "Size Max",
            "form_snippet": "chart_range.html",
            "min": 0,
            "max": 100,
            "step": 1,
            "group": "Structure",
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
            self.query_field(),
            self.x_axis_field(columns),
            self.y_axis_field(columns),
            self.log_x_field(),
            self.log_y_field(),
            self.sort_x_field(),
            self.sort_y_field(),
            self.color_field(columns),
            self.animation_frame_field(columns),
            self.opacity_field(),
            self.size_field(columns),
            self.size_max_field(),
            self.limit_field(),
        ]
