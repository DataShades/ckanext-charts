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

            console.debug(this.options.config);

            if (!this.options.config) {
                console.error("No configuration provided");
                return;
            }

            var chart = new Chart(this.el[0].getContext("2d"), this.options.config);
            window.charts_chartjs = chart;
        }
    };
});
