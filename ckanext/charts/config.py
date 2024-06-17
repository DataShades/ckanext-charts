import ckan.plugins.toolkit as tk

CONF_CACHE_STRATEGY = "ckanext.charts.cache_strategy"
CONF_REDIS_CACHE_TTL = "ckanext.charts.redis_cache_ttl"
CONF_FILE_CACHE_TTL = "ckanext.charts.file_cache_ttl"
CONF_ENABLE_CACHE = "ckanext.charts.enable_cache"
CONF_SERVERSIDE_RENDER = "ckanext.charts.use_serverside_rendering"
CONF_ENABLE_HTMX = "ckanext.charts.include_htmx_asset"
CONF_REINIT_JS = "ckanext.charts.reinit_ckan_js_modules"


def get_cache_strategy() -> str:
    """Get an active cache strategy from the configuration."""
    return tk.config[CONF_CACHE_STRATEGY]


def get_redis_cache_ttl() -> int:
    """Get the redis cache time-to-live from the configuration."""
    return tk.asint(tk.config[CONF_REDIS_CACHE_TTL])


def get_file_cache_ttl() -> int:
    """Get the file cache time-to-live from the configuration."""
    return tk.asint(tk.config[CONF_FILE_CACHE_TTL])


def is_cache_enabled() -> bool:
    """Check if the cache is enabled."""
    return tk.asbool(tk.config[CONF_ENABLE_CACHE])


def use_serverside_rendering() -> bool:
    """Check if the server-side rendering is enabled."""
    return tk.asbool(tk.config[CONF_SERVERSIDE_RENDER])


def include_htmx_asset() -> bool:
    """Include HTMX library asset. Disable it, if no other library do it."""
    return tk.config[CONF_ENABLE_HTMX]


def reinit_ckan_js_modules() -> bool:
    """Reinitialize CKAN JS modules."""
    return tk.config[CONF_REINIT_JS]
