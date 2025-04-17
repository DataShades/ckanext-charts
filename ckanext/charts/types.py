from __future__ import annotations

from typing import Any, Union

import pandas as pd
from dataclasses import dataclass, field


@dataclass
class ChartData:
    """Data structure for cached chart data."""

    df: pd.DataFrame = field(default_factory=pd.DataFrame)
    settings: dict[str, Any] = field(default_factory=dict)
    columns: list[str] = field(default_factory=list)


SerializableType = Union[
    None,
    bool,
    int,
    float,
    str,
    bytes,
    list[Any],
    dict[Any, Any],
    tuple[Any, ...],
    set[Any],
    ChartData,
]
