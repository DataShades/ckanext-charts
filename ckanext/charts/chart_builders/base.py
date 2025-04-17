from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, cast

import numpy as np
import pandas as pd

import ckan.plugins.toolkit as tk
from ckan import types

from ckanext.charts import const, fetchers, utils
from ckanext.charts.exception import ChartBuildError, ChartTypeNotImplementedError


class FilterDecoder:
    def __init__(
        self,
        filter_input: str,
        pair_divider: str = "|",
        key_value_divider: str = ":",
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
    DEFAULT_DATETIME_FORMAT = "ISO8601"

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

            for column, values in filter_params.items():
                column_type = self.df[column].convert_dtypes().dtype.type

                # TODO: requires more work here...
                # I'm not sure about other types, that column can have
                if column_type == np.int64:
                    converted_values = [int(value) for value in values]
                elif column_type == np.float64:
                    converted_values = [float(value) for value in values]
                else:
                    converted_values = values

                # Apply filter in-place
                self.df = self.df[self.df[column].isin(converted_values)]

        # Return only the requested rows if limit is less than cached data size
        limit = self.get_limit()
        if limit < self.df.shape[0]:
            self.df = self.df.head(limit)

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

    def _is_column_datetime(self, column_name: str) -> bool:
        """Check if string values of the certain column are convertible
        to datetime type.

        Args:
            column (str): name of the column to check

        Returns:
            True if values can be converted to datetime type, otherwise - False
        """
        try:
            pd.to_datetime(self.df[column_name], format=self.DEFAULT_DATETIME_FORMAT)
        except ValueError:
            return False
        return True


class BaseChartForm(ABC):
    name = ""

    def __init__(
        self,
        resource_id: str | None = None,
        dataframe: pd.DataFrame | None = None,
        settings: dict[str, Any] | None = None,
    ) -> None:
        self.resource_id = resource_id

        if dataframe is not None:
            self.df = dataframe
        else:
            if not resource_id:
                raise ChartBuildError("Resource ID is required")

            try:
                self.df = fetchers.DatastoreDataFetcher(
                    resource_id,
                    settings=settings,
                ).fetch_data()
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
        result: list[str] = []

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
        from ckanext.scheming.plugins import _expand_schemas  # type: ignore

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

        try:
            validation_schema = {
                field["field_name"]: (
                    field["validators"]
                    if not for_show
                    else field.get("output_validators", field["validators"])
                )
                for field in fields
                if "validators" in field
            }
        except KeyError:
            raise ChartBuildError("Form field missing 'field_name' key") from None

        return validation_schema

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
            "type": "str",
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
            "type": "str",
            "default": "Chart",
            "help_text": "Title of the chart view",
            "validators": [
                self.get_validator("default")("Chart"),
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
            "type": "str",
            "help_text": "Title of the chart itself",
            "validators": [
                self.get_validator("default")(" "),
                self.get_validator("unicode_safe"),
            ],
        }

    def x_axis_label_field(self) -> dict[str, Any]:
        return {
            "field_name": "x_axis_label",
            "label": "Chart X axe label",
            "form_placeholder": "X label",
            "group": "Styles",
            "type": "str",
            "help_text": "Label for the X-axis",
            "validators": [
                self.get_validator("ignore_empty"),
                self.get_validator("unicode_safe"),
            ],
        }

    def y_axis_label_field(self) -> dict[str, Any]:
        return {
            "field_name": "y_axis_label",
            "label": "Chart Y axe label",
            "form_placeholder": "Y label",
            "group": "Styles",
            "type": "str",
            "help_text": "Label for the Y-axis",
            "validators": [
                self.get_validator("ignore_empty"),
                self.get_validator("unicode_safe"),
            ],
        }

    def y_axis_label_right_field(self) -> dict[str, Any]:
        return {
            "field_name": "y_axis_label_right",
            "label": "Chart Y axe right label",
            "form_placeholder": "Right Y label",
            "group": "Styles",
            "type": "str",
            "help_text": "Label for the Y-axis on the right side",
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
            "type": "str",
            "help_text": "Description of the chart view",
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
            "type": "str",
            "help_text": "Select the chart engine to use",
            "default": "plotly",
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
            "help_text": "Select the type of the chart, e.g. Line, Bar, Scatter, etc.",
            "type": "str",
            "default": "Line",
        }

    def x_axis_field(self, choices: list[dict[str, str]]) -> dict[str, Any]:
        return {
            "field_name": "x",
            "label": "X Axis",
            "form_snippet": "chart_select.html",
            "required": True,
            "choices": choices,
            "group": "Data",
            "type": "str",
            "help_text": "Select a column for the X-axes",
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
                "help_text": "Select a column for the Y-axis",
            },
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
            "type": "List[str]",
            "help_text": help_text,
        }

        if max_items:
            field["validators"].append(
                self.get_validator("charts_list_length_validator")(max_items),
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
            },
        )

        return field

    def split_data_field(self) -> dict[str, Any]:
        return {
            "field_name": "split_data",
            "label": "Split by years",
            "form_snippet": "chart_checkbox.html",
            "group": "Data",
            "validators": [
                self.get_validator("chart_checkbox"),
                self.get_validator("default")(False),
                self.get_validator("boolean_validator"),
            ],
            "help_text": (
                "Split data into different columns by years based on datetime "
                "column stated for the x-axis"
            ),
            "type": "bool",
            "default": False,
        }

    def skip_null_values_field(self) -> dict[str, Any]:
        return {
            "field_name": "skip_null_values",
            "label": "Skip N/A and NULL values",
            "form_snippet": "chart_checkbox.html",
            "group": "Data",
            "validators": [
                self.get_validator("chart_checkbox"),
                self.get_validator("default")(False),
                self.get_validator("boolean_validator"),
            ],
            "help_text": """Entries of the data with missing values will not be
                            graphed or will be skipped""",
            "type": "bool",
        }

    def break_chart_field(self) -> dict[str, Any]:
        return {
            "field_name": "break_chart",
            "label": "Break the chart",
            "form_snippet": "chart_checkbox.html",
            "group": "Data",
            "validators": [
                self.get_validator("chart_checkbox"),
                self.get_validator("default")(False),
                self.get_validator("boolean_validator"),
            ],
            "help_text": "Break the graph at missing values",
            "type": "bool",
        }

    def sort_x_field(self) -> dict[str, Any]:
        return {
            "field_name": "sort_x",
            "label": "Sort X-axis",
            "form_snippet": "chart_checkbox.html",
            "group": "Data",
            "validators": [
                self.get_validator("chart_checkbox"),
                self.get_validator("default")(False),
                self.get_validator("boolean_validator"),
            ],
            "help_text": "Sort the X-axis values",
            "type": "bool",
            "default": False,
        }

    def sort_y_field(self) -> dict[str, Any]:
        return {
            "field_name": "sort_y",
            "label": "Sort Y-axis",
            "form_snippet": "chart_checkbox.html",
            "group": "Data",
            "validators": [
                self.get_validator("chart_checkbox"),
                self.get_validator("default")(False),
                self.get_validator("boolean_validator"),
            ],
            "help_text": "Sort the Y-axis values",
            "type": "bool",
            "default": False,
        }

    def invert_x_field(self) -> dict[str, Any]:
        return {
            "field_name": "invert_x",
            "label": "Invert X-axis",
            "form_snippet": "chart_checkbox.html",
            "group": "Data",
            "validators": [
                self.get_validator("chart_checkbox"),
                self.get_validator("default")(False),
                self.get_validator("boolean_validator"),
            ],
            "help_text": "Invert the X-axis",
            "type": "bool",
            "default": False,
        }

    def invert_y_field(self) -> dict[str, Any]:
        return {
            "field_name": "invert_y",
            "label": "Invert Y-axis",
            "form_snippet": "chart_checkbox.html",
            "group": "Data",
            "validators": [
                self.get_validator("chart_checkbox"),
                self.get_validator("default")(False),
                self.get_validator("boolean_validator"),
            ],
            "help_text": "Invert the Y-axis",
            "type": "bool",
            "default": False,
        }

    def log_x_field(self) -> dict[str, Any]:
        return {
            "field_name": "log_x",
            "label": "Log-scale X-axis",
            "form_snippet": "chart_checkbox.html",
            "group": "Data",
            "validators": [
                self.get_validator("chart_checkbox"),
                self.get_validator("default")(False),
                self.get_validator("boolean_validator"),
            ],
            "help_text": "Use log scale for the X-axis",
            "type": "bool",
            "default": False,
        }

    def log_y_field(self) -> dict[str, Any]:
        return {
            "field_name": "log_y",
            "label": "Log-scale Y-axis",
            "form_snippet": "chart_checkbox.html",
            "group": "Data",
            "validators": [
                self.get_validator("chart_checkbox"),
                self.get_validator("default")(False),
                self.get_validator("boolean_validator"),
            ],
            "help_text": "Use log scale for the Y-axis",
            "type": "bool",
            "default": False,
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
            "help_text": "Select a column for the color",
            "type": "str",
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
            "help_text": "Select a column for the animation frame",
            "type": "str",
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
            "help_text": "Opacity level of the chart",
            "type": "float",
            "default": 1,
        }

    def limit_field(self, default: int = 1000, maximum: int = 10000) -> dict[str, Any]:
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
            "help_text": "Limit the number of rows to show in the chart",
            "type": "int",
            "default": default,
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
                "help_text": "Select a column for the values",
                "type": "str",
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
                "help_text": "Select a column for the names",
                "type": "str",
            },
        )

        return field

    def width_field(self) -> dict[str, Any]:
        """Width of the chart."""
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
            "help_text": "Width of the chart",
            "type": "int",
            "default": 640,
        }

    def height_field(self) -> dict[str, Any]:
        """Height of the chart."""
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
            "help_text": "Height of the chart",
            "type": "int",
            "default": 400,
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
            "exclude_from_mkdocs": True,
        }

    def size_field(self, choices: list[dict[str, str]]) -> dict[str, Any]:
        field = self.column_field(choices)
        field.update(
            {
                "field_name": "size",
                "label": "Size",
                "group": "Structure",
                "help_text": "Select a column for the size",
                "type": "str",
            },
        )

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
            "exclude_from_mkdocs": True,
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
            "exclude_from_mkdocs": True,
        }

    def size_max_field(self) -> dict[str, Any]:
        return {
            "field_name": "size_max",
            "label": "Size Max",
            "form_snippet": "chart_range.html",
            "min": 0,
            "max": 100,
            "step": 1,
            "group": "Structure",
            "validators": [
                self.get_validator("default")(100),
                self.get_validator("int_validator"),
            ],
            "type": "int",
            "help_text": "Maximum size of dots or bubbles",
        }

    def color_picker_field(self) -> dict[str, Any]:
        return {
            "field_name": "color_picker",
            "label": "Color Picker",
            "form_snippet": "chart_color_picker.html",
            "group": "Styles",
            "type": "str",
            "validators": [
                self.get_validator("default")("#ffffff"),
                self.get_validator("unicode_safe"),
            ],
            "help_text": "Select a color",
            "default": "#ffffff",
        }

    def get_all_column_names(self) -> list[str]:
        """Get all usable column names (excluding system columns)."""
        if self.resource_id:
            return utils.get_datastore_column_names(self.resource_id)

        return self.df.columns.to_list()
