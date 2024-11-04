from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, cast

import pandas as pd
import numpy as np

import ckan.types as types
import ckan.plugins.toolkit as tk

import ckanext.charts.const as const
from ckanext.charts.exception import ChartTypeNotImplementedError
from ckanext.charts import fetchers


class FilterDecoder:
    def __init__(
        self, filter_input: str, pair_divider: str = "|", key_value_divider: str = ":"
    ):
        self.filter_input = filter_input
        self.pair_divider = pair_divider
        self.key_value_divider = key_value_divider

    def decode_filter_params(self) -> dict[str, list[str]]:
        if not self.filter_input:
            return {}

        key_value_pairs = self.filter_input.split(self.pair_divider)

        parsed_data: dict[str, list[str]] = {}

        for pair in key_value_pairs:
            key, value = pair.split(self.key_value_divider)

            if key in parsed_data:
                parsed_data[key].append(value)
            else:
                parsed_data[key] = [value]

        return parsed_data


class BaseChartBuilder(ABC):
    def __init__(
        self,
        dataframe: pd.DataFrame,
        settings: dict[str, Any],
    ) -> None:
        self.df = dataframe
        self.settings = settings

        if filter_input := self.settings.pop("filter", None):
            filter_decoder = FilterDecoder(filter_input)
            filter_params = filter_decoder.decode_filter_params()

            filtered_df = self.df.copy()

            for column, values in filter_params.items():
                column_type = filtered_df[column].convert_dtypes().dtype.type

                # TODO: requires more work here...
                # I'm not sure about other types, that column can have
                if column_type == np.int64:
                    values = [int(value) for value in values]
                elif column_type == np.float64:
                    values = [float(value) for value in values]

                filtered_df = filtered_df[filtered_df[column].isin(values)]

            self.df = filtered_df

        if self.settings.pop("sort_x", False):
            self.df.sort_values(by=self.settings["x"], inplace=True)

        if self.settings.pop("sort_y", False):
            self.df.sort_values(by=self.settings["y"], inplace=True)

        self.df = self.df.head(self.get_limit())

        self.settings.pop("query", None)

        self.settings = self.drop_view_fields(self.drop_empty_values(self.settings))

    def get_limit(self) -> int:
        """Get the limit of rows to show in the chart."""
        if "limit" not in self.settings:
            return const.CHART_DEFAULT_ROW_LIMIT

        return int(self.settings.pop("limit"))

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

    def convert_to_native_types(self, value: Any) -> Any:
        """Convert numpy types to native python types."""
        if isinstance(value, np.generic):
            return value.item()

        return value

    def get_unique_values(self, column: pd.Series, sort: bool = True) -> list[Any]:
        """Get unique values from a pandas Series."""
        result = [
            self.convert_to_native_types(value) for value in column.unique().tolist()
        ]

        if not sort:
            return result

        return sorted(result)


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

    def get_form_tabs(self, exclude_tabs: list[str] | None = None) -> list[str]:
        result = []

        for field in self.get_form_fields():
            if "group" not in field:
                continue

            if field["group"] in result:
                continue

            result.append(field["group"])

        if exclude_tabs:
            result = [tab for tab in result if tab not in exclude_tabs]

        return result

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

    def get_validation_schema(self, for_show: bool = False) -> dict[str, Any]:
        fields = self.get_form_fields()

        return {
            field["field_name"]: (
                field["validators"]
                if not for_show
                else field.get("output_validators", field["validators"])
            )
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
            "form_snippet": "chart_select.html",
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

    def chart_title_field(self) -> dict[str, Any]:
        return {
            "field_name": "chart_title",
            "label": "Chart Title",
            "preset": "title",
            "form_placeholder": "Chart title",
            "group": "Styles",
            "validators": [
                self.get_validator("default")(" "),
                self.get_validator("unicode_safe"),
            ],
        }

    def chart_xlabel_field(self) -> dict[str, Any]:
        return {
            "field_name": "chart_xlabel",
            "label": "Chart X axe label",
            "form_placeholder": "X label",
            "group": "Styles",
            "validators": [
                self.get_validator("ignore_empty"),
                self.get_validator("unicode_safe"),
            ],
        }

    def chart_ylabel_field(self) -> dict[str, Any]:
        return {
            "field_name": "chart_ylabel",
            "label": "Chart Y axe label",
            "form_placeholder": "Y label",
            "group": "Styles",
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
            "form_snippet": "chart_select.html",
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
            "form_snippet": "chart_select.html",
            "required": True,
            "choices": choices,
            "group": "Structure",
            "validators": [
                self.get_validator("default")("Line"),
                self.get_validator("unicode_safe"),
            ],
            "form_attrs": {
                "hx-get": tk.h.url_for("charts_view.update_form"),
                "hx-trigger": "change",
                "hx-include": "closest form",
                "hx-target": ".charts-view--form",
                "data-module-clear-button": True,
            },
        }

    def x_axis_field(self, choices: list[dict[str, str]]) -> dict[str, Any]:
        return {
            "field_name": "x",
            "label": "X Axis",
            "form_snippet": "chart_select.html",
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

    def y_multi_axis_field(
        self,
        choices: list[dict[str, str]],
        max_items: int = 0,
        help_text: str = "Select one or more columns for the Y-axis",
    ) -> dict[str, Any]:
        field: dict[str, Any] = {
            "field_name": "y",
            "label": "Y Axis",
            "required": True,
            "choices": choices,
            "group": "Data",
            "form_snippet": "chart_select.html",
            "validators": [
                self.get_validator("charts_if_empty_same_as")("x"),
                self.get_validator("not_empty"),
                self.get_validator("charts_to_list_if_string"),
                self.get_validator("list_of_strings"),
            ],
            "output_validators": [
                self.get_validator("charts_if_empty_same_as")("x"),
                self.get_validator("not_empty"),
            ],
            "form_attrs": {
                "class": "tom-select",
                "data-module-multiple": "true",
                "multiple": 1,
            },
            "help_text": help_text,
        }

        if max_items:
            field["validators"].append(
                self.get_validator("charts_list_length_validator")(max_items)
            )
            field["form_attrs"]["maxItems"] = max_items

        return field

    def values_multi_field(
        self,
        choices: list[dict[str, str]],
        max_items: int = 0,
        help_text: str = "Select one or more values for the chart",
    ):
        field = self.y_multi_axis_field(choices, max_items)

        field.update(
            {
                "field_name": "values",
                "label": "Values",
                "validators": [
                    self.get_validator("charts_if_empty_same_as")("names"),
                    self.get_validator("not_empty"),
                    self.get_validator("charts_to_list_if_string"),
                    self.get_validator("list_of_strings"),
                ],
                "output_validators": [
                    self.get_validator("charts_if_empty_same_as")("names"),
                    self.get_validator("not_empty"),
                    self.get_validator("charts_to_list_if_string"),
                ],
                "help_text": help_text,
            }
        )

        return field

    def split_data_field(self) -> dict[str, Any]:
        return {
            "field_name": "split_data",
            "label": "Split by years",
            "form_snippet": "chart_checkbox.html",
            "group": "Data",
            "validators": [
                self.get_validator("default")(False),
                self.get_validator("boolean_validator"),
            ],
            "help_text":    """Split data into different columns by years based 
                            on datetime column stated for the x-axis"""
        }

    def skip_null_values_field(self) -> dict[str, Any]:
        return {
            "field_name": "skip_null_values",
            "label": "Skip N/A and NULL values",
            "form_snippet": "chart_checkbox.html",
            "group": "Data",
            "validators": [
                self.get_validator("boolean_validator"),
            ],
            "help_text":    """Entries in the data with N/A or NULL will not be 
                            graphed and will be skipped"""
        }

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

    def invert_x_field(self) -> dict[str, Any]:
        return {
            "field_name": "invert_x",
            "label": "Invert X-axis",
            "form_snippet": "chart_checkbox.html",
            "group": "Data",
            "validators": [
                self.get_validator("default")(False),
                self.get_validator("boolean_validator"),
            ],
        }

    def invert_y_field(self) -> dict[str, Any]:
        return {
            "field_name": "invert_y",
            "label": "Invert Y-axis",
            "form_snippet": "chart_checkbox.html",
            "group": "Data",
            "validators": [
                self.get_validator("default")(False),
                self.get_validator("boolean_validator"),
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
            "form_snippet": "chart_select.html",
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
            "form_snippet": "chart_select.html",
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

    def limit_field(self, default: int = 100, maximum: int = 10000) -> dict[str, Any]:
        """The limit field represent an amount of rows to show in the chart."""
        return {
            "field_name": "limit",
            "label": "Limit",
            "form_snippet": "chart_text.html",
            "input_type": "number",
            "validators": [
                self.get_validator("default")(default),
                self.get_validator("int_validator"),
                self.get_validator("limit_to_configured_maximum")("", maximum),
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

    def more_info_button_field(self) -> dict[str, Any]:
        """
        Adds a "More info" button to the Data tab in the form, which triggers a pop-up.
        This pop-up provides users with information about supported date formats.
        """
        return {
            "field_name": "more_info",
            "label": "More info",
            "form_snippet": "chart_more_info_button.html",
            "group": "Data",
        }

    def size_field(self, choices: list[dict[str, str]]) -> dict[str, Any]:
        field = self.column_field(choices)
        field.update({"field_name": "size", "label": "Size", "group": "Structure"})

        return field

    def filter_field(self, choices: list[dict[str, str]]) -> dict[str, Any]:
        return {
            "field_name": "filter",
            "label": "Filter",
            "form_snippet": "chart_filter.html",
            "choices": choices,
            "validators": [
                self.get_validator("ignore_empty"),
                self.get_validator("unicode_safe"),
            ],
            "group": "Filter",
        }

    def engine_details_field(self) -> dict[str, Any]:
        """
        Provides details about zoom functionality support in various charting libraries.
        """
        return {
            "field_name": "engine_details",
            "label": "Engine details",
            "form_snippet": "chart_engine_details.html",
            "group": "Structure",
        }
