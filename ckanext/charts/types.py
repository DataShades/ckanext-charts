from __future__ import annotations

from typing import Any

import pandas as pd
from dataclasses import dataclass, field


@dataclass
class ChartData:
    """Data structure for cached chart data."""

    df: pd.DataFrame = field(default_factory=pd.DataFrame)
    settings: dict[str, Any] = field(default_factory=dict)
    columns: list[str] = field(default_factory=list)
