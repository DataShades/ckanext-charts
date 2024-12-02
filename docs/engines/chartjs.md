The `Chart.JS` chart engine supports the following chart types:

- Bar chart
- Horizontal bar chart
- Line chart
- Pie chart
- Doughnut chart
- Scatter plot
- Bubble chart
- Radar chart

::: charts.chart_builders.chartjs.ChartJsBuilder
    options:
      show_source: true
      show_bases: false

## Bar chart

The bar chart is a chart with rectangular bars with lengths proportional to the values that they represent. The bars can be plotted vertically or horizontally. For a horizontal bar chart, use the `Horizontal bar chart` chart type.

::: Chart form fields
    handler: ChartFieldsHandler
    options:
      engine: chartjs
      chart_type: Bar

## Horizontal bar chart

The horizontal bar chart is a chart with rectangular bars with lengths proportional to the values that they represent. The bars are plotted horizontally.

::: Chart form fields
    handler: ChartFieldsHandler
    options:
      engine: chartjs
      chart_type: Horizontal Bar

## Line chart

The line chart is a chart that displays information as a series of data points called 'markers' connected by straight line segments. It is useful for showing trends over time.

::: Chart form fields
    handler: ChartFieldsHandler
    options:
      engine: chartjs
      chart_type: Line

## Pie chart

The pie chart is a circular statistical graphic that is divided into slices to illustrate numerical proportions. The arc length of each slice is proportional to the quantity it represents.

::: Chart form fields
    handler: ChartFieldsHandler
    options:
      engine: chartjs
      chart_type: Pie

## Doughnut chart

The doughnut chart is a variant of the pie chart, with a hole in the center. It is useful for showing the relationship of parts to a whole.

::: Chart form fields
    handler: ChartFieldsHandler
    options:
      engine: chartjs
      chart_type: Doughnut

## Scatter plot

The scatter plot is a chart that uses Cartesian coordinates to display values for two variables for a set of data. The data points are represented as individual dots.

::: Chart form fields
    handler: ChartFieldsHandler
    options:
      engine: chartjs
      chart_type: Scatter

## Bubble chart

The bubble chart is a chart that displays data points as bubbles. The size of the bubble represents a third dimension of the data.

::: Chart form fields
    handler: ChartFieldsHandler
    options:
      engine: chartjs
      chart_type: Bubble

## Radar chart

The radar chart is a chart that displays multivariate data in the form of a two-dimensional chart of three or more quantitative variables represented on axes starting from the same point. The data points are connected by a line to form a polygon.

::: Chart form fields
    handler: ChartFieldsHandler
    options:
      engine: chartjs
      chart_type: Radar
