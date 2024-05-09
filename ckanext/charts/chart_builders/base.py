from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import pandas as pd

from ckanext.charts.exception import ChartTypeNotImplementedError


class BaseChartBuilder(ABC):
    def __init__(
        self,
        dataframe: pd.DataFrame,
        settings: dict[str, Any],
    ) -> None:
        self.df = dataframe
        self.settings = settings

    # def columns(self) -> list[str]:
    #     return self.df.columns.tolist()

    @classmethod
    @abstractmethod
    def get_supported_forms(cls) -> list[type[Any]]:
        pass

    @classmethod
    def get_builder_for_type(cls, chart_type: str) -> type[BaseChartBuilder]:
        form_builder = cls.get_form_for_type(chart_type)

        return form_builder.builder

    @classmethod
    def get_form_for_type(cls, chart_type: str) -> Any:
        for form_builder in cls.get_supported_forms():
            if chart_type == form_builder.name:
                return form_builder

        raise ChartTypeNotImplementedError("Chart type not implemented")

    @abstractmethod
    def to_html(self) -> str:
        pass

    @abstractmethod
    def to_json(self) -> str:
        pass

    # def set_type(self, chart_type: str) -> Self:
    #     self.type = chart_type

    #     return self

    # def set_x_axis(self, x: str) -> Self:
    #     if not x:
    #         self.x = ""
    #         return self

    #     if not isinstance(x, str):
    #         raise ValueError("X axis must be a string")

    #     if x not in self.columns():
    #         raise ValueError(f"Column {x} does not exist in the dataframe")

    #     self.x = x

    #     return self

    # def set_y_axis(self, y: str) -> Self:
    #     if not y:
    #         self.y = ""
    #         return self

    #     if not isinstance(y, str):
    #         raise ValueError("Y axis must be a string")

    #     if y not in self.columns():
    #         raise ValueError(f"Column {y} does not exist in the dataframe")

    #     self.y = y

    #     return self

    # def set_x_label(self, x_label: str) -> Self:
    #     if not x_label:
    #         self.x_label = ""
    #         return self

    #     if not isinstance(x_label, str):
    #         raise ValueError("X label must be a string")

    #     self.x_label = x_label

    #     return self

    # def set_y_label(self, y_label: str) -> Self:
    #     if not y_label:
    #         self.y_label = ""
    #         return self

    #     if not isinstance(y_label, str):
    #         raise ValueError("Y label must be a string")

    #     self.y_label = y_label

    #     return self

    # def set_title(self, title: str) -> Self:
    #     if not title:
    #         self.title = ""
    #         return self

    #     if not isinstance(title, str):
    #         raise ValueError("Title must be a string")

    #     self.title = title

    #     return self

    # def set_log_x(self, log_x: bool) -> Self:
    #     if not isinstance(log_x, bool):
    #         raise ValueError("log_x must be a boolean")

    #     self.log_x = log_x

    #     return self

    # def set_query(self, query: str) -> None:

    #     self.df.query(query, inplace=True)

    # def set_log_y(self, log_y: bool) -> Self:
    #     if not isinstance(log_y, bool):
    #         raise ValueError("log_y must be a boolean")

    #     self.log_y = log_y

    #     return self

    # def sort_by_x(self) -> Self:
    #     self.df.sort_values(by=self.x, inplace=True)

    #     return self

    # def sort_by_y(self) -> Self:
    #     self.df.sort_values(by=self.y, inplace=True)

    #     return self

    # def set_color(self, color: str | None) -> Self:
    #     if not color:
    #         self.color = ""
    #         return self

    #     if not isinstance(color, str):
    #         raise ValueError("Color must be a string")

    #     if color not in self.columns():
    #         raise ValueError(f"Column {color} does not exist in the dataframe")

    #     self.color = color

    #     return self

    # def set_opacity(self, opacity: float) -> Self:
    #     if opacity < 0 or opacity > 1:
    #         raise ValueError("Opacity must be between 0 and 1")

    #     self.opacity = opacity

    #     return self

    # def set_animation_frame(self, animation_frame: str) -> Self:
    #     if not animation_frame:
    #         self.animation_frame = ""
    #         return self

    #     if not isinstance(animation_frame, str):
    #         raise ValueError("Animation frame must be a string")

    #     if animation_frame not in self.columns():
    #         raise ValueError(
    #             f"Column {animation_frame} does not exist in the dataframe"
    #         )

    #     self.animation_frame = animation_frame

    #     return self

    def drop_empty_values(self, data: dict[str, Any]) -> dict[str, Any]:
        """Remove empty values from the dictionary"""
        result = {}

        for key, value in data.items():
            if not isinstance(value, pd.DataFrame) and value == "":
                continue

            result[key] = value

        return result
