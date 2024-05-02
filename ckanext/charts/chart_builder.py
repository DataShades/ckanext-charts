from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import pandas as pd
import plotly.express as px
from plotly.graph_objs import Figure


class BaseChartBuilder(ABC):
    def __init__(self, dataframe: pd.DataFrame, options: dict[str, Any]) -> None:
        self.df = dataframe
        self.options = options

    @abstractmethod
    def bar_chart(self) -> dict[str, Any] | Figure:
        pass

    @abstractmethod
    def pie_chart(self) -> dict[str, Any] | Figure:
        pass


class PlotlyBuilder(BaseChartBuilder):
    def bar_chart(self) -> Figure:
        return px.bar(
            self.df,
            x=self.options.get("x"),
            y=self.options.get("y"),
            color=self.options.get("color"),
        )

    def pie_chart(self) -> Figure:
        return px.pie(
            self.df,
            names=self.options.get("names"),
            values=self.options.get("values"),
            color=self.options.get("color"),
        )
