ckan.module("charts-render-chartjs", function ($, _) {
    "use strict";

    return {
        options: {
            config: null
        },

        initialize: function () {
            $.proxyAll(this, /_/);

            if (window.charts_chartjs) {
                window.charts_chartjs.destroy();
            }

            if (!this.options.config) {
                console.error("No configuration provided");
                return;
            }

            const unsupportedTypes = ['pie', 'doughnut', 'radar'];
            const isZoomSupported = !unsupportedTypes.includes(this.options.config.type);
            let zoomOptions = null;

            if (isZoomSupported) {
                zoomOptions =  this.options.config.options.plugins.zoom;

                this.options.config.options.plugins.title.text = () => {
                    return 'Zoom: ' + this.zoomStatus(zoomOptions) + ', Pan: ' + this.panStatus(zoomOptions);
                };

                $('#resetZoom').show();
                $('#toggleZoom').show();
                $('#togglePan').show();
            } else {
                $('#resetZoom').hide();
                $('#toggleZoom').hide();
                $('#togglePan').hide();
            }

            var chart = new Chart(this.el[0].getContext("2d"), this.options.config);
            window.charts_chartjs = chart;

            $('#resetZoom').on('click', this.resetZoom);
            $('#toggleZoom').on('click', (e) => this.toggleZoom(e, zoomOptions));
            $('#togglePan').on('click', (e) => this.togglePan(e, zoomOptions));
        },
        resetZoom: function(event) {
            event.preventDefault();
            window.charts_chartjs.resetZoom();
        },

        zoomStatus: function(zoomOptions) {
            return zoomOptions.zoom.drag.enabled ? 'enabled' : 'disabled';
        },

        panStatus: function(zoomOptions) {
            return zoomOptions.pan.enabled ? 'enabled' : 'disabled';
        },

        toggleZoom: function (event, zoomOptions) {
            event.preventDefault();

            const zoomEnabled = zoomOptions.zoom.wheel.enabled;

            zoomOptions.zoom.wheel.enabled = !zoomEnabled;
            zoomOptions.zoom.pinch.enabled = !zoomEnabled;
            zoomOptions.zoom.drag.enabled = !zoomEnabled;

            // Update the chart with the new zoom options
            window.charts_chartjs.update();
        },

        togglePan: function(event, zoomOptions) {
            event.preventDefault();

            const currentPanEnabled = zoomOptions.pan.enabled;
            zoomOptions.pan.enabled = !currentPanEnabled;

            // Update the chart with the new zoom options
            window.charts_chartjs.update();
        }
    };
});
