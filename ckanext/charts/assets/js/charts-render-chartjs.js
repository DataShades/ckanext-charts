ckan.module("charts-render-chartjs", function($, _) {
    "use strict";

    return {
        const: {
            zoomUnsupportedTypes: ['pie', 'doughnut', 'radar']
        },
        options: {
            config: null,
            chartBg: 'white'
        },

        initialize: function() {
            $.proxyAll(this, /_/);

            this.chartControl = this.el.next(".chart-control");
            this.chartId = this.el[0].id;
            this.isZoomSupported = !this.const.zoomUnsupportedTypes.includes(this.options.config.type);

            window.charts_chartjs = window.charts_chartjs || {};

            if (!this.options.config) {
                console.error("No configuration provided");
                return;
            }

            this._registerChartBackground();
            this._destroyChartInAContainer(this.chartId);

            this.options.config.id = this.chartId;

            var chart = new Chart(this.el[0].getContext("2d"), this.options.config)

            window.charts_chartjs[chart.id] = chart;

            this._registerControlEvents(chart.id);
        },

        /**
         * Register a new chart background plugin that will draw a background
         * on the canvas before drawing the chart.
         *
         * We need it to have a white background on the chart when the chart
         * is being exported as an image. Otherwise, the background will be
         * transparent.
         */
        _registerChartBackground: function() {
            Chart.register({
                id: 'chartjs-chart-background',
                beforeDraw: (chart, args, opts) => {
                    const ctx = chart.canvas.getContext('2d');
                    ctx.save();
                    ctx.globalCompositeOperation = 'destination-over';
                    ctx.fillStyle = this.options.chartBg;
                    ctx.fillRect(0, 0, chart.width, chart.height);
                    ctx.restore();
                }
            })
        },

        /**
         * Destroy the chart in a container before rendering a new one.
         *
         * We're deleting reference only to the chart, that share the same
         * container id. It should still allow us to have multiple charts
         * on the same page.
         *
         * @param {String} containerId
         */
        _destroyChartInAContainer: function(containerId) {
            for (const [_, chart] of Object.entries(window.charts_chartjs)) {
                if (chart.canvas.id !== containerId) {
                    continue;
                }

                window.charts_chartjs[chart.id].destroy();
                delete window.charts_chartjs[chart.id];
                break;
            }
        },

        /**
         * Register control events for the chart.
         *
         * @param {String} chartId - The id of the chart
         */
        _registerControlEvents: function(chartId) {
            this.chartControl.toggle(this.isZoomSupported);

            if (this.isZoomSupported) {
                const zoomOptions = this.options.config.options.plugins.zoom;

                this.options.config.options.plugins.title.text = () => {
                    return 'Zoom: ' + this.getZoomStatus(zoomOptions) + ', Pan: ' + this.getPanStatus(
                        zoomOptions);
                };

                this.chartControl.find('#resetZoom').off().on('click', (e) => this.resetZoom(e, chartId));
                this.chartControl.find('#toggleZoom').off().on('click', (e) => this.toggleZoom(e, zoomOptions, chartId));
                this.chartControl.find('#togglePan').off().on('click', (e) => this.togglePan(e, zoomOptions, chartId));
            }

            this.chartControl.find("#makeSnapshot").off().on("click", (e) => this._makeSnapshot(e, chartId));
        },

        getZoomStatus: function(zoomOptions) {
            return zoomOptions.zoom.drag.enabled ? 'enabled' : 'disabled';
        },

        getPanStatus: function(zoomOptions) {
            return zoomOptions.pan.enabled ? 'enabled' : 'disabled';
        },

        resetZoom: function(event, chartId) {
            event.preventDefault();
            window.charts_chartjs[chartId].resetZoom();
        },

        toggleZoom: function(event, zoomOptions, chartId) {
            event.preventDefault();

            const zoomEnabled = zoomOptions.zoom.wheel.enabled;

            zoomOptions.zoom.wheel.enabled = !zoomEnabled;
            zoomOptions.zoom.pinch.enabled = !zoomEnabled;
            zoomOptions.zoom.drag.enabled = !zoomEnabled;

            window.charts_chartjs[chartId].update();
        },

        togglePan: function(event, zoomOptions, chartId) {
            event.preventDefault();

            zoomOptions.pan.enabled = !zoomOptions.pan.enabled;
            window.charts_chartjs[chartId].update();
        },

        _makeSnapshot: function(event, chartId) {
            event.preventDefault();

            var dataUrl = window.charts_chartjs[chartId].toBase64Image();

            var link = document.createElement('a')
            link.download = 'view-snapshot-' + Date.now() + '.png';
            link.href = dataUrl
            link.click()
        },
    }
});
