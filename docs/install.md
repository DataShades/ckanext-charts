# Installation

## Requirements

Requires **Redis 7+**

Compatibility with core CKAN versions:

| CKAN version    | Compatible?   |
| --------------- | ------------- |
| 2.9 and earlier | no            |
| 2.10+           | yes           |

## Installation

1. Install the extension from `PyPI`:
    ```sh
    pip install ckanext-charts
    ```

    If you want to use `ORC` file cache, you have to install the extension with the `pyarrow` extra:
    ```sh
    pip install ckanext-charts[pyarrow]
    ```

2. Enable the view and builder plugins in your CKAN configuration file (e.g. `ckan.ini` or `production.ini`):

    ```ini
    ckan.plugins = ... charts_view charts_builder_view ...
    ```

## Dependencies

The extension requires the following CKAN extensions to be installed and enabled:

1. [ckanext-scheming](https://github.com/ckan/ckanext-scheming):
We're using the scheming extension to create custom forms for the chart builders.

2. [ckanext-admin-panel](https://github.com/DataShades/ckanext-admin-panel) (__optional__):
If you want to use the admin configuration page, you need to install and enable this extension. The admin panel is a separate extension that provides an alternative admin interface for CKAN. It allows you to manage CKAN settings and other extensions settings through the web interface and significantly extends the default CKAN admin interface.
