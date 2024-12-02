# Custom chart engine

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

## Vendor and custom JS

Another step is to register JS/CSS vendor libraries of the chart you want to use. Refer to [CKAN documentation](https://docs.ckan.org/en/latest/theming/webassets.html) to read about adding CSS and JavaScript files using Webassets.

You also will need a CKAN JS module, that will be responsible for rendering the Chart. This module will work with the vendor library and will be responsible for rendering the chart in the container.

This module must be registered inside a `webassets.yml` as well.
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

## HTML container

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
