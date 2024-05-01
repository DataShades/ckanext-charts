from __future__ import annotations

from typing import Any, Iterable

from typing_extensions import TypedDict, TypeAlias

ChartData: TypeAlias = "list[dict[str, int | str | float]]"


class ChartJsDataset(TypedDict):
    label: str
    data: Iterable[Any]


class ChartJsData(TypedDict):
    labels: Iterable[str]
    datasets: Iterable[ChartJsDataset]
