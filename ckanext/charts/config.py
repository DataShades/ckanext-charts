import ckan.plugins.toolkit as tk


CONF_CACHE_STRATEGY = "ckanext.charts.cache_strategy"


def get_cache_strategy():
    """Get an active cache strategy from the configuration."""
    return tk.config[CONF_CACHE_STRATEGY]
