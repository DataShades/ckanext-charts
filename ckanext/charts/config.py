import ckan.plugins.toolkit as tk


CONF_CACHE_STRATEGY = "ckanext.charts.cache_strategy"
CONF_REDIS_CACHE_TTL = "ckanext.charts.redis_cache_ttl"
CONF_FILE_CACHE_TTL = "ckanext.charts.file_cache_ttl"


def get_cache_strategy():
    """Get an active cache strategy from the configuration."""
    return tk.config[CONF_CACHE_STRATEGY]


def get_redis_cache_ttl():
    """Get the redis cache time-to-live from the configuration."""
    return tk.asint(tk.config[CONF_REDIS_CACHE_TTL])


def get_file_cache_ttl():
    """Get the file cache time-to-live from the configuration."""
    return tk.asint(tk.config[CONF_FILE_CACHE_TTL])
