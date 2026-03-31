CACHE_FILE_ORC = "file_orc"
CACHE_FILE_CSV = "file_csv"
CACHE_REDIS = "redis"

DEFAULT_CACHE_STRATEGY = CACHE_REDIS

SUPPORTED_CACHE_STRATEGIES = [
    CACHE_FILE_CSV,
    CACHE_FILE_ORC,
    CACHE_REDIS,
]

REDIS_PREFIX = "ckanext-charts:*"
CHART_DEFAULT_ROW_LIMIT = 1000

# Form field group names
FORM_GROUP_GENERAL = "General"
FORM_GROUP_STRUCTURE = "Structure"
FORM_GROUP_DATA = "Data"
FORM_GROUP_STYLES = "Styles"
FORM_GROUP_FILTER = "Filter"

# All available form groups in order
FORM_GROUPS = [
    FORM_GROUP_GENERAL,
    FORM_GROUP_STRUCTURE,
    FORM_GROUP_DATA,
    FORM_GROUP_STYLES,
    FORM_GROUP_FILTER,
]

# DateTime Format Constants
# Standard datetime format name used as reference
DEFAULT_DATETIME_FORMAT = "ISO8601"

# Datetime format string patterns
DATETIME_FORMAT_ISO8601 = "%Y-%m-%dT%H:%M:%S"
DATETIME_FORMAT_YEAR = "%Y"
DATETIME_FORMAT_TICKS = "%m-%d %H:%M"

# Chart Builder Constants
DEFAULT_AXIS_TICKS_NUMBER = 12
DEFAULT_PLOT_HEIGHT = 400
DEFAULT_NAN_FILL_VALUE = 0
