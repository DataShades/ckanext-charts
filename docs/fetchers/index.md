# Fetchers

Fetchers are responsible for fetching data from different sources (DataStore, URL, file system, hardcoded data).

For the current implementation, we're working with resources that are uploaded to the DataStore, so the fetcher will be responsible for fetching the data from the DataStore.

But it might come in handy to have fetchers for other sources, like URL, file system, etc.

## Implementing new fetchers

To register new fetchers, you need to create a new class that inherits from `DataFetcherStrategy` and implements the `fetch_data` and `make_cache_key` methods.

The `fetch_data` method should return a `pandas` `DataFrame` object with the data that should be displayed in the chart.

The `make_cache_key` method should return a unique string that will be used as a key to store the data in the cache.

See the [base class](./base.md) `DataFetcherStrategy` for more information.
