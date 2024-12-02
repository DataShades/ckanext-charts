# Base Cache Strategy

To implement a custom cache strategy, you need to create a new class that extends the `CacheStrategy` class and implement the abstract methods.

See a naive implementation of a memcached cache strategy below:
```python
from io import BytesIO

from pymemcache.client import base
import pandas as pd

import ckanext.charts.config as config
from ckanext.charts.cache import CacheStrategy

class MemcachedCache(CacheStrategy):
    """Cache data to Memcached"""

    def __init__(self):
        self.client = base.Client(('localhost', 11211))

    def get_data(self, key: str) -> pd.DataFrame | None:
        """Return data from cache if exists"""
        try:
            raw_data = self.client.get(key)

            if not raw_data:
                return None

            return pd.read_csv(BytesIO(raw_data))
        except Exception:
            log.exception(f"Failed to get data for key: {key}")
            return None

    def set_data(self, key: str, data: pd.DataFrame):
        """Serialize data and save to Memcached"""
        cache_ttl = config.get_memcached_cache_ttl()

        try:
            serialized_data = data.to_csv(index=False).encode('utf-8')
            self.client.set(key, serialized_data, expire=cache_ttl)
        except Exception:
            log.exception(f"Failed to save data to Memcached for key: {key}")

    def invalidate(self, key: str):
        """Invalidate cache by key"""
        try:
            self.client.delete(key)
        except Exception:
            log.exception(f"Failed to invalidate cache for key: {key}")
```

::: charts.cache.CacheStrategy
    options:
      show_source: false
