# Caching

The extension implement a cache strategy to store the data fetched from the different sources.

There are three cache strategies available:

1. `redis`
2. `file_orc`
3. `file_csv`.

## File cache

The file cache works by storing the data in an `orc` or `csv` file in the filesystem. The redis cache stores the data in a Redis database. The cache strategy can be changed at the CKAN configuration level through the admin interface or in a configuration file.

The `file-type` cache strategy stores the data in a file in the filesystem. The file cache is stored in the `ckanext-charts` directory in the CKAN storage path. The file cache is stored in an `orc` or `csv` file format.

???+ Warning
    Using `file_orc` cache strategy requires the `pyarrow` python library to be installed.

## Redis cache

The `redis` cache strategy stores the data in a Redis database.

Each redis key has a `ckanext-charts:*` prefix and store the data as a CSV string.

???+ Note
    You need to have a Redis server running to use the `redis` cache strategy.

## Cache TTL

The cache TTL can be set in the CKAN configuration file. The default value is 3600 seconds (1 hour).

The `redis` and `file-type` cache has separate TTL settings:

* The `redis` cache TTL can be set with the `ckanext.charts.redis_cache_ttl` configuration option.
* The `file` cache TTL can be set with the `ckanext.charts.file_cache_ttl` configuration option.

## Disable cache

Cache could be disabled by setting `ckanext.charts.enable_cache` to `false`. In this case the data will be fetched from the source every time the chart is rendered. It could be useful for debugging purposes. But using it in production is not recommended, as it could lead to performance issues.

