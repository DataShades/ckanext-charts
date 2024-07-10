CACHE_FILE_ORC = "file_orc"
CACHE_FILE_CSV = "file_csv"
CACHE_REDIS = "redis"

DEFAULT_CACHE_STRATEGY = CACHE_REDIS

SUPPORTED_CACHE_STRATEGIES = [
    CACHE_FILE_CSV,
    CACHE_FILE_ORC,
    CACHE_REDIS
]

REDIS_PREFIX = "ckanext-charts:*"
CHART_DEFAULT_ROW_LIMIT = 100
