from __future__ import annotations

from typing import Any

import pandas as pd
from typing_extensions import TypedDict


class CachedChartData(TypedDict):
    df: pd.DataFrame
    settings: dict[str, Any] | None
