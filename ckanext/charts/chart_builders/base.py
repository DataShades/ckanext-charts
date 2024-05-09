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

        if self.settings.pop("sort_x", False):
            self.df.sort_values(by=self.settings["x"], inplace=True)

        if self.settings.pop("sort_y", False):
            self.df.sort_values(by=self.settings["y"], inplace=True)

        if limit := self.settings.pop("limit", 0):
            self.df = self.df.head(int(limit))

        self.settings.pop("query", None)

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

    def drop_empty_values(self, data: dict[str, Any]) -> dict[str, Any]:
        """Remove empty values from the dictionary"""
        result = {}

        for key, value in data.items():
            if not isinstance(value, pd.DataFrame) and value == "":
                continue

            result[key] = value

        return result
