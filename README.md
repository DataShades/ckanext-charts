[![Tests](https://github.com/DataShades/ckanext-charts/workflows/Tests/badge.svg?branch=main)](https://github.com/DataShades/ckanext-charts/actions)

# ckanext-charts

This extension, ckanext-charts, provides additional functionality for working with charts in CKAN. It allows users to create, manage, and visualize charts based on data stored in CKAN datasets.

The extension includes features such as chart creation, chart editing, chart embedding, and chart sharing. It also supports various chart types, including bar charts, line charts, pie charts, and more.

With ckanext-charts, users can easily generate interactive and visually appealing charts to enhance data analysis and presentation in CKAN.


## Requirements

Requires Redis 7+

Compatibility with core CKAN versions:

| CKAN version    | Compatible?   |
| --------------- | ------------- |
| 2.9 and earlier | no            |
| 2.10+           | yes           |


## Installation

- Install it with `PyPi` with `pip install ckanext-charts`
- Add `charts_view` to the list of plugins in your CKAN config (`ckan.plugins = charts_view`)

## Config settings

List of config options:

	# Caching strategy for chart data (required, default: redis).
	ckanext.charts.cache_strategy = disk

    # Time to live for the Redis cache in seconds. Set 0 to disable cache (default: 3600)
    ckanext.charts.redis_cache_ttl = 7200
    
    # Time to live for the File cache in seconds. Set 0 to disable cache.
    ckanext.charts.file_cache_ttl = 0

## Cache

The extension implement a cache strategy to store the data fetched from the different sources. There are two cache strategies available: `redis` and `file`. The file cache works by storing the data in an `orc` file in the filesystem. The redis cache stores the data in a Redis database. The cache strategy can be changed at the CKAN configuration level through the admin interface or in a configuration file.

## Implementing new fetchers

Fetchers are responsible for fetching data from different sources (DataStore, URL, file system, hardcoded data).

To register new fetchers, you need to create a new class that inherits from `DataFetcherStrategy` and implements the `fetch_data` and `make_cache_key` methods.
The `fetch_data` method should return a `pandas` `DataFrame` object with the data that should be displayed in the chart.
The `make_cache_key` method should return a unique string that will be used as a key to store the data in the cache.

## Developer installation

To install ckanext-charts for development, activate your CKAN virtualenv and
do:

    git clone https://github.com/DataShades/ckanext-charts.git
    cd ckanext-charts
    python setup.py develop
    pip install -r dev-requirements.txt


## Tests

To run the tests, do:

    pytest --ckan-ini=test.ini


## License

[AGPL](https://www.gnu.org/licenses/agpl-3.0.en.html)
