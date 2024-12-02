The `Observable Plot` chart engine supports the following chart types:

- Bar chart
- Horizontal bar chart
- Pie chart
- Line chart
- Scatter plot
- Auto chart

::: charts.chart_builders.observable.ObservableBuilder
    options:
      show_source: true
      show_bases: false

## Bar chart

The bar chart is a chart with rectangular bars with lengths proportional to the values that they represent. The bars can be plotted vertically or horizontally. For a horizontal bar chart, use the `Horizontal bar chart` chart type.

::: Chart form fields
    handler: ChartFieldsHandler
    options:
      engine: observable
      chart_type: Bar

## Horizontal bar chart

The horizontal bar chart is a chart with rectangular bars with lengths proportional to the values that they represent. The bars are plotted horizontally.

::: Chart form fields
    handler: ChartFieldsHandler
    options:
      engine: observable
      chart_type: Horizontal Bar

## Line chart

The line chart is a chart that displays information as a series of data points called 'markers' connected by straight line segments. It is useful for showing trends over time.

::: Chart form fields
    handler: ChartFieldsHandler
    options:
      engine: observable
      chart_type: Line

## Pie chart

The pie chart is a circular statistical graphic that is divided into slices to illustrate numerical proportions. The arc length of each slice is proportional to the quantity it represents.

::: Chart form fields
    handler: ChartFieldsHandler
    options:
      engine: observable
      chart_type: Pie

## Scatter plot

The scatter plot is a chart that uses Cartesian coordinates to display values for two variables for a set of data. The data points are represented as individual dots.

::: Chart form fields
    handler: ChartFieldsHandler
    options:
      engine: observable
      chart_type: Scatter

## Auto chart

The auto chart is a chart that automatically selects the best chart type based on the data. It is useful for quickly visualizing data without having to manually select a chart type.

::: Chart form fields
    handler: ChartFieldsHandler
    options:
      engine: observable
      chart_type: Auto
