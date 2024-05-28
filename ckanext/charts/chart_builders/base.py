from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, cast

import pandas as pd

import ckan.types as types
import ckan.plugins.toolkit as tk

from ckanext.charts.exception import ChartTypeNotImplementedError
from ckanext.charts import fetchers


class BaseChartBuilder(ABC):
    def __init__(
        self,
        dataframe: pd.DataFrame,
        settings: dict[str, Any],
    ) -> None:
        self.df = dataframe
        self.settings = settings

        if self.settings.pop("sort_x", False):
            self.df.sort_values(by=self.settings["x"], inplace=True)

        if self.settings.pop("sort_y", False):
            self.df.sort_values(by=self.settings["y"], inplace=True)

        if limit := self.settings.pop("limit", 0):
            self.df = self.df.head(int(limit))

        self.settings.pop("query", None)

        self.settings = self.drop_view_fields(self.drop_empty_values(self.settings))

    @classmethod
    @abstractmethod
    def get_supported_forms(cls) -> list[type[BaseChartForm]]:
        pass

    @classmethod
    def get_builder_for_type(cls, chart_type: str) -> type[BaseChartBuilder]:
        form_builder = cls.get_form_for_type(chart_type)

        return form_builder.builder

    @classmethod
    def get_form_for_type(cls, chart_type: str) -> Any:
        supported_forms = cls.get_supported_forms()

        if not chart_type:
            return supported_forms[0]

        for form_builder in cls.get_supported_forms():
            if chart_type == form_builder.name:
                return form_builder

        raise ChartTypeNotImplementedError("Chart type not implemented")

    @abstractmethod
    def to_json(self) -> str:
        """This method should return the chart data as a dumped JSON data. It
        will be passed to a JS script, that will render a chart based on this
        data."""
        pass

    def drop_empty_values(self, data: dict[str, Any]) -> dict[str, Any]:
        """Remove empty values from the dictionary"""
        result = {}

        for key, value in data.items():
            if not isinstance(value, pd.DataFrame) and value == "":
                continue

            result[key] = value

        return result

    def drop_view_fields(self, settings: dict[str, Any]) -> dict[str, Any]:
        """Drop fields not related to chart settings."""
        return {
            k: v
            for k, v in settings.items()
            if k
            not in (
                "title",
                "description",
                "engine",
                "type",
                "id",
                "notes",
                "package_id",
                "resource_id",
                "view_type",
            )
        }


class BaseChartForm(ABC):
    name = ""

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
        """The list for a specific chart could be defined similar to a scheming
        dataset schema fields."""

    def get_form_tabs(self) -> list[str]:
        return ["General", "Structure", "Data", "Styles"]

    def get_expanded_form_fields(self):
        """Expands the presets."""
        return self.expand_schema_fields(
            self.drop_validators(
                self.get_form_fields(),
            ),
        )

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

    def get_fields_by_tab(self, tab: str) -> list[dict[str, Any]]:
        fields = self.get_expanded_form_fields()

        return [field for field in fields if field["group"] == tab]

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
            "validators": [
                self.get_validator("ignore_empty"),
                self.get_validator("unicode_safe"),
            ],
        }

    def description_field(self) -> dict[str, Any]:
        return {
            "field_name": "description",
            "label": "Description",
            "form_snippet": "markdown.html",
            "form_placeholder": "Information about my view",
            "group": "General",
            "validators": [
                self.get_validator("ignore_empty"),
                self.get_validator("unicode_safe"),
            ],
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
            "form_attrs": {
                "hx-get": tk.h.url_for("charts_view.update_form", reset_engine=1),
                "hx-trigger": "change",
                "hx-include": "closest form",
                "hx-target": ".charts-view--form",
            },
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
                self.get_validator("charts_if_empty_same_as")("values"),
                self.get_validator("unicode_safe"),
            ],
        }

    def y_axis_field(self, choices: list[dict[str, str]]) -> dict[str, Any]:
        field = self.column_field(choices)
        field.update(
            {
                "field_name": "y",
                "label": "Y Axis",
                "validators": [
                    self.get_validator("charts_if_empty_same_as")("names"),
                    self.get_validator("unicode_safe"),
                ],
            }
        )

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
            "form_snippet": "chart_text.html",
            "input_type": "number",
            "validators": [
                self.get_validator("default")(100),
                self.get_validator("int_validator"),
                self.get_validator("limit_to_configured_maximum")("", 10000),
            ],
            "group": "Data",
        }

    def values_field(self, choices: list[dict[str, str]]) -> dict[str, Any]:
        field = self.column_field(choices)
        field.update(
            {
                "field_name": "values",
                "label": "Values",
                "validators": [
                    self.get_validator("charts_if_empty_same_as")("y"),
                    self.get_validator("unicode_safe"),
                ],
            },
        )

        return field

    def names_field(self, choices: list[dict[str, str]]) -> dict[str, Any]:
        field = self.column_field(choices)
        field.update(
            {
                "field_name": "names",
                "label": "Names",
                "validators": [
                    self.get_validator("charts_if_empty_same_as")("x"),
                    self.get_validator("unicode_safe"),
                ],
            },
        )

        return field

    def width_field(self) -> dict[str, Any]:
        """The limit field represent an amount of rows to show in the chart."""
        return {
            "field_name": "width",
            "label": "Width",
            "form_snippet": "chart_text.html",
            "input_type": "number",
            "validators": [
                self.get_validator("default")(640),
                self.get_validator("int_validator"),
                self.get_validator("limit_to_configured_maximum")("", 1000),
            ],
            "group": "Data",
        }

    def height_field(self) -> dict[str, Any]:
        """The limit field represent an amount of rows to show in the chart."""
        return {
            "field_name": "height",
            "label": "Height",
            "form_snippet": "chart_text.html",
            "input_type": "number",
            "validators": [
                self.get_validator("default")(400),
                self.get_validator("int_validator"),
                self.get_validator("limit_to_configured_maximum")("", 1000),
            ],
            "group": "Data",
        }
