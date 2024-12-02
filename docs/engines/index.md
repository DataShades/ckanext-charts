The `ckanext-charts` implements supports different chart engines, such as `plotly`, `observable` and `chartjs`.

Each engine consists of two classes - chart builder and form builder. The chart builder is responsible for generating a JSON-string representation of the chart data, that will be passed to a respective JS module, that will render a chart based on the data.

The form builder is responsible for generating a form that allows users to configure the chart from the UI.

Read more about how to create a custom chart engine in the [documentation](./custom.md).

