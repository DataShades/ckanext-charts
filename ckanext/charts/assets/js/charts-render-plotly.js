ckan.module("charts-render-plotly", function($, _) {
    "use strict";

    return {
        options: {
            config: null
        },

        initialize: function() {
            $.proxyAll(this, /_/);

            this.chartControl = this.el.next(".chart-control");

            window.charts_plotly = window.charts_plotly || {};

            if (!this.options.config) {
                console.error("No configuration provided");
                return;
            }

            if (!this.chartControl.length) {
                console.error("No chart control found");
                return;
            }

            Plotly.newPlot(this.el[0], this.options.config).then(
                (chart) => {
                    window.charts_plotly[chart.id] = chart;

                    this.chartControl.find("#makeSnapshot").on("click", (e) => this._makeSnapshot(e, chart.id));
                }
            );
        },

        _makeSnapshot: function(event, chartId) {
            event.preventDefault();

            Plotly.toImage(
                    window.charts_plotly[chartId], {
                        height: window.charts_plotly[chartId].clientHeight,
                        width: window.charts_plotly[chartId].clientWidth
                    })
                .then(
                    function(dataUrl) {
                        var link = document.createElement('a')
                        link.download = 'view-snapshot-' + Date.now() + '.png';
                        link.href = dataUrl;
                        link.click()
                    }
                )
        }
    };
});
