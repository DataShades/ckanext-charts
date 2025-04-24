# Base Cache Strategy

To implement a custom cache strategy, you need to create a new class that extends the `CacheStrategy` class and implement the abstract methods.

See a naive implementation of a memcached cache strategy below:
```python
import pickle

from pymemcache.client import base

import ckanext.charts.config as config
from ckanext.charts.cache import CacheStrategy
from ckanext.charts import types

class MemcachedCache(CacheStrategy):
    """Cache data to Memcached"""

    def __init__(self):
        self.client = base.Client(('localhost', 11211))

    def get_data(self, key: str) -> types.ChartData | None:
        """Return data from cache if exists"""
        try:
            raw_data = self.client.get(key)

            if not raw_data:
                return None

            return pickle.loads(raw_data)
        except Exception:
            log.exception(f"Failed to get data for key: {key}")
            return None

    def set_data(self, key: str, data: types.ChartData):
        """Serialize data and save to Memcached"""
        cache_ttl = config.get_memcached_cache_ttl()
        payload = pickle.dumps(data)

        try:
            self.client.set(key, payload, expire=cache_ttl)
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
