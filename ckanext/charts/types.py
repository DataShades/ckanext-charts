from __future__ import annotations

from typing import Any
from collections.abc import Iterable

from typing_extensions import TypedDict
import pandas as pd


class ChartJsDataset(TypedDict):
    label: str
    data: Iterable[Any]


class ChartJsData(TypedDict):
    labels: Iterable[str]
    datasets: Iterable[ChartJsDataset]


class CachedChartData(TypedDict):
    df: pd.DataFrame
    settings: dict[str, Any] | None
