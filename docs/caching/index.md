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

## Removing expired file cache

Expired file cache entries are ignored when read, but the files themselves stay
on disk until they are pruned. The extension provides a CLI command to remove
all expired files from the file cache:

```sh
ckan charts clear-expired-cache
```

There is also a command to drop **all** chart caches (both Redis and file):

```sh
ckan charts clear-cache
```

???+ Tip
    It's a good idea to run `ckan charts clear-expired-cache` periodically via a
    cronjob so the file cache doesn't grow unbounded. For example, to prune
    expired files every hour:

    ```cron
    0 * * * * /usr/lib/ckan/default/bin/ckan -c /etc/ckan/default/ckan.ini charts clear-expired-cache
    ```

    Adjust the paths to the `ckan` binary and configuration file to match your
    deployment, and pick an interval that suits your `ckanext.charts.file_cache_ttl`.

## Disable cache

Cache could be disabled by setting `ckanext.charts.enable_cache` to `false`. In this case the data will be fetched from the source every time the chart is rendered. It could be useful for debugging purposes. But using it in production is not recommended, as it could lead to performance issues.

