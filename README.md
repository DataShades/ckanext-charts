[![Tests](https://github.com/DataShades/ckanext-charts/workflows/Tests/badge.svg?branch=main)](https://github.com/DataShades/ckanext-charts/actions)

# ckanext-charts

This extension, ckanext-charts, provides additional functionality for working with charts in CKAN. It allows users to create, manage, and visualize charts based on data stored in CKAN datasets.

The extension includes features such as chart creation, chart editing, chart embedding, and chart sharing. It also supports various chart types, including bar charts, line charts, pie charts, and more.

With ckanext-charts, users can easily generate interactive and visually appealing charts to enhance data analysis and presentation in CKAN.


## Requirements

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
