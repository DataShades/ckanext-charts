[![Tests](https://github.com/DataShades/ckanext-charts/actions/workflows/test.yml/badge.svg)](https://github.com/DataShades/ckanext-charts/actions/workflows/test.yml)

# ckanext-charts

This extension, ckanext-charts, provides additional functionality for working with charts in CKAN. It allows users to create, manage, and visualize charts based on data stored in CKAN datasets.

The extension includes features such as chart creation, chart editing, chart embedding, and chart sharing. It also supports various chart types, including bar charts, line charts, pie charts, and more.

With ckanext-charts, users can easily generate interactive and visually appealing charts to enhance data analysis and presentation in CKAN.

See the [documentation](https://datashades.github.io/ckanext-charts/) for more information.

## Quick start

- Install it with `PyPi` with `pip install ckanext-charts[pyarrow]`
- Add `charts_view` to the list of plugins in your CKAN config (`ckan.plugins = charts_view charts_builder_view`)



## Developer installation

To install `ckanext-charts` for development, activate your CKAN virtualenv and
do:

    git clone https://github.com/DataShades/ckanext-charts.git
    cd ckanext-charts
    pip install -e '.[dev]'

## Tests

To run the tests, do:

    pytest --ckan-ini=test.ini


## Building the documentation

We are using `mkdocs` to build the documentation. To build and deploy the documentation, do:

    CHARTS_FIELDS=1 mkdocs build && mkdocs gh-deploy

We need to set the `CHARTS_FIELDS` for our custom handler, that autogenerate documentation
for chart types fields.

The CKAN instance will be initialized, because we will call validators and helpers in this code. Therefore, you'll need
another environment variable to set the CKAN configuration file path:

    export CKAN_INI=$PWD/config/ckan.ini

The config file must enable the `ckanext-charts` plugin:

    ckan.plugins = ... charts_view charts_builder_view ...

If you're working on the documentation, you can run the following command to start a live-reloading server without
gathering the chart types fields data. It will speed up the process significantly, as we won't need to wait for the
CKAN initialization:

    mkdocs serve -a 127.0.0.1:8001

## License

[AGPL](https://www.gnu.org/licenses/agpl-3.0.en.html)
