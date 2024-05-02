from __future__ import annotations

from typing import Any
from abc import ABC, abstractmethod

import pandas as pd


class BaseChartBuilder(ABC):
    def __init__(self, dataframe: pd.DataFrame, user_settings: dict[str, Any]) -> None:
        self.df = dataframe
        self.user_settings = user_settings

    @abstractmethod
    def get_settings(self) -> dict[str, Any]:
        pass


class PlotlyBuilder(BaseChartBuilder):
    pass
