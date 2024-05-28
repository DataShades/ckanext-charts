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

## Implementing new chart engines support

Implementing support for a new chart engine includes multiple steps and changes in Python, HTML, and JavaScript. Starting from the Python code:

1. Create a new builder class at `ckanext.charts.chart_builder` that inherits from `BaseChartBuilder` and implements the `get_supported_forms` method. This method must return a list of classes that represent supported chart types forms.
   
2. Each form type builder must be connected with a respective chart type builder.

3. The chart type builder must implement a `to_json` method that will return a dumped JSON data, which will be passed to a JS script.
   
4. The form type builder must implement a `get_form_fields` method that will return a list of all form fields that will be rendered for the user, allowing them to provide all the necessary information for a chart.

5. Register your chart engine by adding the builder class to `get_chart_engines` in `ckanext.charts.chart_builder.__init__.py`.

A full example of an implementation of `bar` chart for `obvervable plot` library.

```py
from __future__ import annotations

import json
from typing import Any

import ckanext.charts.exception as exception
from ckanext.charts.chart_builders.base import BaseChartBuilder, BaseChartForm


class ObservableBuilder(BaseChartBuilder):
    @classmethod
    def get_supported_forms(cls) -> list[type[Any]]:
        return [ObservableBarForm]


class ObservableBarBuilder(ObservableBuilder):
    def to_json(self) -> str:
        return json.dumps(
            {
                "type": "bar",
                "data": self.df.to_dict(orient="records"),
                "settings": self.settings,
            }
        )


class ObservableBarForm(BaseChartForm):
    name = "Bar"
    builder = ObservableBarBuilder

    def fill_field(self, choices: list[dict[str, str]]) -> dict[str, str]:
        field = self.color_field(choices)
        field.update({"field_name": "fill", "label": "Fill"})

        return field

    def get_form_fields(self):
        columns = [{"value": col, "label": col} for col in self.df.columns]
        chart_types = [
            {"value": form.name, "label": form.name}
            for form in self.builder.get_supported_forms()
        ]

        return [
            self.title_field(),
            self.description_field(),
            self.engine_field(),
            self.type_field(chart_types),
            self.x_axis_field(columns),
            self.y_axis_field(columns),
            self.fill_field(columns),
            self.opacity_field(),
            self.limit_field(),
        ]
```

Another step is to register JS/CSS vendor libraries of the chart you want to use. Refer to [CKAN documentation](https://docs.ckan.org/en/latest/theming/webassets.html) to read about adding CSS and JavaScript files using Webassets.

You also will need a CKAN JS module, that will be responsible for rendering the Chart. This module must be registered inside a `webassets.yml` as well.
```js
    ckan.module("charts-render-observable", function ($, _) {
        "use strict";

        return {
            options: {
                config: null
            },

            initialize: function () {
                $.proxyAll(this, /_/);

                if (!this.options.config) {
                    console.error("No configuration provided");
                    return;
                }

                var plot;

                switch (this.options.config.type) {
                    case "bar":
                        plot = Plot.barY(this.options.config.data, this.options.config.settings).plot();
                        break;
                    default:
                        return;
                }

                this.el[0].replaceChildren(plot);
            }
        };
    });
```

And an HTML file, that will provide a proper container and include your JS module with `data-module`.

```html
    {% asset "charts/observable" %}

    {% if chart %}
        <div id="chart-container" data-module="charts-render-observable" data-module-config="{{ chart }}"></div>
    {% else %}
        <p class="text-muted">
            {{ _("Cannot build chart with current settings") }}
        </p>
    {% endif %}
```

Note, that we should add `{% asset "charts/observable" %}` not only here, but in `charts_form.html` too.

The reason for having a separate `HTML` file and `JS` module is that different libraries may require different types of container elements (such as div, canvas, etc.) to initialize or may need additional boilerplate code to build a chart. There's no easy way to abstract this, so you have to implement these things yourself.

## Developer installation

To install ckanext-charts for development, activate your CKAN virtualenv and
do:

    git clone https://github.com/DataShades/ckanext-charts.git
    cd ckanext-charts
    python setup.py develop
    pip install -r dev-requirements.txt

## Troubleshooting

**ImportError: lxml.html.clean module is now a separate project lxml_html_clean**

Install `lxml[html_clean]` or `lxml_html_clean` directly using pip.

## Tests

To run the tests, do:

    pytest --ckan-ini=test.ini


## License

[AGPL](https://www.gnu.org/licenses/agpl-3.0.en.html)
