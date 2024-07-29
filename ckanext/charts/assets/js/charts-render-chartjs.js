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

            if (isZoomSupported) {
                const zoomOptions =  this.options.config.options.plugins.zoom;

                this.options.config.options.plugins.title.text = () => {
                    return 'Zoom: ' + this.zoomStatus(zoomOptions) + ', Pan: ' + this.panStatus(zoomOptions);
                };

                $('#resetZoom').on('click', this.resetZoom);
                $('#toggleZoom').on('click', (e) => this.toggleZoom(e, zoomOptions));
                $('#togglePan').on('click', (e) => this.togglePan(e, zoomOptions));
            }

            $(".zoom-control").toggle(isZoomSupported);

            window.charts_chartjs = new Chart(this.el[0].getContext("2d"), this.options.config);
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

            window.charts_chartjs.update();
        },

        togglePan: function(event, zoomOptions) {
            event.preventDefault();

            zoomOptions.pan.enabled = !zoomOptions.pan.enabled;
            window.charts_chartjs.update();
        }
    };
});
